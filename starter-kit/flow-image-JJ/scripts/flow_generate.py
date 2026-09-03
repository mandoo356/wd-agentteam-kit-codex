"""Google Flow 이미지 배치 생성 + 다운로드 (헤드리스 Playwright).

사용 예:
  python flow_generate.py --prompts prompts.txt --model nano-banana-2 --ratio 1:1 --count 4 --out ./out
  python flow_generate.py --prompts "a red apple||a blue car" --ratio 16:9 --out ./out

사전 조건: flow_login.py 로 1회 로그인되어 있어야 한다.

## 결과 보고 — `<out>/report.json`
프롬프트 하나가 끝날 때마다 **덮어써서 갱신**한다. 계정 한도에 걸려 중간에 끊겨도
어디까지 나왔는지가 파일에 남아, 호출자가 «빠진 번호만» 골라 다시 돌릴 수 있다.
`results[]` 의 각 항목은 `{index, prompt, generated, saved[], error?}` 이고
`error` 는 `submit_failed`(제출 자체 실패) · `flow_error`(Flow 오류 배너 — 한도 소진 의심) ·
`timeout`(생성이 끝났는데 결과 0장) 중 하나다.

## 종료 코드
  0 = 요청한 프롬프트 전부 최소 1장씩 저장
  3 = **일부만** 나왔다 → `report.json` 을 읽고 `--only <빠진번호>` 로 재시도
  1 = 한 장도 못 받았다   ·   2 = 인자 오류

빠진 것만 다시 뽑기:
  python flow_generate.py --prompts p.txt --only 2,5-6 --out ./out    # 번호·파일명은 원본 유지
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from flow_common import FLOW_URL, accept_cookie_banner, close, dismiss_overlays, launch, require_login
from flow_download import download_url, read_prompts, slug

# Material Symbols ligature 텍스트 = UI 언어와 무관하게 동일 → 셀렉터로 안전하다.
RATIO_ICON = {
    "16:9": "crop_16_9",
    "4:3": "crop_landscape",
    "1:1": "crop_square",
    "3:4": "crop_portrait",
    "9:16": "crop_9_16",
}
# 장수 탭 라벨. 2026-08-07 UI 개편으로 1장 탭이 '1x' → 'x1' 로 바뀌었다.
# 다시 바뀔 수 있으므로 후보를 모두 시도한다.
COUNT_TAB = {n: (f"x{n}", f"{n}x") for n in (1, 2, 3, 4)}
MODEL_MENU = {
    "nano-banana-2-lite": "🍌 Nano Banana 2 Lite",
    "nano-banana-2": "🍌 Nano Banana 2",
    "nano-banana-pro": "🍌 Nano Banana Pro",
}

MEDIA_SRC = "media.getMediaUrlRedirect"

# 참고 이미지를 프롬프트에 붙일 때 쓰는 라벨 (UI 언어에 따라 둘 중 하나)
ADD_TO_PROMPT = ("프롬프트에 추가", "Add to prompt")
REF_EXT = {".jpg", ".jpeg", ".png", ".webp"}


# 프롬프트에 방향/비율 표현이 들어가면 에이전트가 그것을 우선해 설정 패널의 비율을 덮어쓴다.
# 실측: --ratio 3:4 + 프롬프트 'vertical composition' → 768x1376(9:16) 로 나옴.
#       같은 설정에서 문구만 빼면 896x1200(3:4) 로 정상.
ORIENTATION_PATTERNS = [
    r"\b(vertical|horizontal|portrait|landscape|square)\s+(composition|format|orientation|layout|framing)\b",
    r"\b(composition|format|orientation|layout|framing)\s*:\s*(vertical|horizontal|portrait|landscape|square)\b",
    r"\b(16\s*:\s*9|9\s*:\s*16|4\s*:\s*3|3\s*:\s*4|1\s*:\s*1)\b",
    r"\b(widescreen|ultrawide|panoramic)\b",
    r"\b(tall|wide)\s+(vertical|horizontal)\b",
]


def strip_orientation(prompt: str) -> str:
    """프롬프트에서 방향/비율 표현을 제거한다.

    비율은 반드시 Flow 설정 패널(--ratio)로만 지정해야 한다.
    프롬프트에 남아 있으면 에이전트가 설정을 무시한다.
    """
    import re

    cleaned = prompt
    hits: list[str] = []
    for pat in ORIENTATION_PATTERNS:
        found = re.findall(pat, cleaned, flags=re.IGNORECASE)
        if found:
            hits.extend(" ".join(f) if isinstance(f, tuple) else f for f in found)
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

    if hits:
        cleaned = re.sub(r"\s*,\s*,+", ",", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        cleaned = re.sub(r"\s+([,.])", r"\1", cleaned).strip(" ,")
        print(f"    [정리] 프롬프트에서 방향/비율 표현 제거: {sorted(set(h.strip() for h in hits))}")
        print("           비율은 --ratio (Flow 설정 패널)로만 지정됩니다.")
    return cleaned


IMAGE_PREFIX = "Generate an image: "
# 이미 이미지 의도를 명시한 프롬프트인지 판정하는 접두 표현
_INTENT = ("generate an image", "create an image", "make an image", "draw ", "generate images")


def force_image_intent(prompt: str) -> str:
    """이미지 생성을 확실히 유도하는 접두어를 붙인다.

    Flow는 에이전트 주도형이라 프롬프트만 보고 이미지/동영상/기타를 판단한다.
    실측: 동일 프롬프트를 접두어 없이 넣으면 생성은 돌지만 이미지가 0장 나오고,
    'Generate an image:' 를 붙이면 정상적으로 4장이 나온다.
    """
    if prompt.strip().lower().startswith(_INTENT):
        return prompt
    return IMAGE_PREFIX + prompt


def select_count(page, count: int) -> str:
    """출력 장수 탭 선택.

    탭 라벨이 UI 개편으로 바뀐다(2026-08-07: '1x' → 'x1'). 후보를 순서대로 시도하고,
    role=tab 요소의 innerText 를 '정확히' 비교한다. 이미지 섹션이 DOM 상 먼저이므로
    첫 번째 일치를 클릭하면 된다.
    """
    tabs = page.locator("button[role=tab]")
    total = tabs.count()
    for label in COUNT_TAB[count]:
        for i in range(total):
            tab = tabs.nth(i)
            try:
                if (tab.inner_text() or "").strip() == label:
                    tab.click()
                    return label
            except Exception:
                continue
    raise RuntimeError(
        f"장수 탭을 찾지 못했습니다 (시도: {COUNT_TAB[count]}). "
        "UI가 바뀌었을 수 있습니다 — flow_probe.py 로 재정찰하세요."
    )


def icon(page, ligature: str):
    """Material Symbols ligature가 '정확히' 일치하는 버튼.

    `:has-text()` 는 부분 일치라 쓰면 안 된다 — 생성 후 채팅 응답에 나타나는
    `arrow_forward_ios`(생각하는 과정 표시) 버튼이 `arrow_forward` 에 걸려버려
    두 번째 프롬프트부터 제출 버튼 대신 그쪽을 클릭하게 된다. (실측된 버그)
    """
    return page.locator(f"button:has(:text-is('{ligature}'))")


# ---------------------------------------------------------------- 진입/탐색
def enter_app(page):
    """랜딩 → 앱 홈. 프로젝트 딥링크 직접 진입은 client-side exception 이 나므로 금지."""
    page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(7_000)
    accept_cookie_banner(page)
    try:
        page.get_by_role("button", name="Create with Google Flow").first.click(timeout=5_000)
        page.wait_for_timeout(9_000)
    except Exception:
        pass
    accept_cookie_banner(page)
    page.wait_for_timeout(3_000)


def _create_project(page, name: str | None):
    dismiss_overlays(page)
    icon(page, "add_2").first.click()
    page.wait_for_timeout(13_000)
    if name:
        rename_project(page, name)
    return page.url


def rename_project(page, name: str) -> None:
    """편집기 상단의 프로젝트 제목 input 을 name 으로 바꾼다."""
    try:
        title = page.locator("input").first
        title.click()
        page.keyboard.press("Control+A")
        page.keyboard.insert_text(name)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2_500)
        print(f"[프로젝트] 이름 설정: {name}")
    except Exception as exc:
        print(f"[!] 프로젝트 이름 설정 실패: {exc}")


def auto_project_name() -> str:
    """새 프로젝트 기본 이름 — 나중에 계정에서 식별 가능하도록 시각을 붙인다."""
    return "image-flow " + datetime.now().strftime("%Y-%m-%d %H:%M")


def downloads_dir() -> Path:
    """사용자 PC의 다운로드 폴더. 레지스트리(한국어 Windows에서 위치 변경 가능)를 먼저 본다."""
    try:
        import winreg

        key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
            path, _ = winreg.QueryValueEx(k, "{374DE290-123F-4565-9164-39C4925E467B}")
        p = Path(path).expanduser()
        if p.is_dir():
            return p
    except Exception:
        pass
    return Path.home() / "Downloads"


def safe_folder(name: str, maxlen: int = 60) -> str:
    """폴더명으로 쓸 수 있게 정리한다. 한글은 그대로 살린다(slug 는 ASCII만 남겨서 부적합)."""
    import re

    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name).strip(" .")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:maxlen] or "image-flow"


def default_out_dir(project_name: str) -> Path:
    """기본 저장 위치 — 다운로드 폴더 아래 image-flow/<프로젝트명>.

    사용자가 탐색기에서 바로 찾을 수 있도록 다운로드 폴더를 기본값으로 쓴다.
    """
    return downloads_dir() / "image-flow" / safe_folder(project_name)


def open_project(page, reuse: bool, name: str | None = None):
    """프로젝트 진입.

    **기본 동작은 매 실행마다 새 프로젝트 생성이다.** 결과물이 실행 단위로 깔끔히 분리되고,
    기존 프로젝트에 쌓인 이미지와 섞이지 않는다.

    - 기본(reuse=False): 항상 새 프로젝트를 만들고 이름을 부여
      (name 미지정 시 `image-flow YYYY-MM-DD HH:MM`)
    - reuse=True + name 지정: 같은 이름 프로젝트가 있으면 재사용, 없으면 생성
    - reuse=True + name 미지정: 가장 최근 프로젝트 재사용
    """
    dismiss_overlays(page)
    if not reuse:
        return _create_project(page, name or auto_project_name())

    links = page.locator("a[href*='/tools/flow/project/']")
    total = links.count()

    if name:
        # 카드 제목은 <a> 바깥에 있고, a.innerText 는 비어 있다.
        # '프로젝트 링크를 정확히 1개만 포함하는 최근접 조상' 을 카드로 보고 그 텍스트에서 제목을 읽는다.
        titles = page.evaluate(
            """() => Array.from(document.querySelectorAll("a[href*='/tools/flow/project/']")).map(a => {
                 let el = a;
                 while (el.parentElement &&
                        el.parentElement.querySelectorAll("a[href*='/tools/flow/project/']").length === 1) {
                   el = el.parentElement;
                 }
                 return {href: a.getAttribute('href'), text: (el.innerText || '').trim()};
               })"""
        )
        for i, t in enumerate(titles):
            if name.lower() in (t.get("text") or "").lower():
                links.nth(i).click()
                page.wait_for_timeout(13_000)
                print(f"[프로젝트] 기존 재사용: {name}")
                return page.url
        print(f"[프로젝트] '{name}' 이 최근 {total}개 목록에 없음 → 새로 생성")
        print("           (Flow 홈은 최근 6개만 노출한다. 밀려난 프로젝트는 재사용할 수 없다)")
        return _create_project(page, name)

    if total:
        links.first.click()
        page.wait_for_timeout(13_000)
        print("[프로젝트] 최근 프로젝트 재사용")
        return page.url
    return _create_project(page, None)


# ---------------------------------------------------------------- 설정
def configure(page, model: str, ratio: str, count: int) -> None:
    """설정 패널에서 이미지 모델 / 비율 / 장수를 지정하고 저장.

    설정 패널에는 이미지 섹션과 동영상 섹션이 같은 구조로 두 번 나온다.
    이미지 섹션이 DOM 상 먼저 오므로 항상 .first 를 쓴다.
    (동영상 섹션에는 crop_square 자체가 없어 비율 선택은 자연히 이미지 섹션에 걸린다.)
    """
    icon(page, "tune").first.click()
    page.wait_for_timeout(3_500)

    # 모델
    page.locator("button:has-text('Nano Banana')").first.click()
    page.wait_for_timeout(2_500)
    page.get_by_role("menuitem", name=MODEL_MENU[model], exact=True).click()
    page.wait_for_timeout(1_800)

    # 비율 (동영상 섹션에는 crop_square/crop_landscape/crop_portrait 자체가 없다)
    page.locator(f"button[role=tab]:has(:text-is('{RATIO_ICON[ratio]}'))").first.click()
    page.wait_for_timeout(1_200)

    # 장수 — 이미지 섹션이 DOM 상 먼저이므로 첫 번째 일치를 쓴다
    select_count(page, count)
    page.wait_for_timeout(1_200)

    for name in ("저장", "Save"):
        try:
            page.get_by_role("button", name=name, exact=True).click(timeout=3_000)
            break
        except Exception:
            continue
    page.wait_for_timeout(4_000)
    print(f"[설정] model={model} ratio={ratio} count={count}")


# ---------------------------------------------------------------- 생성
def media_srcs(page) -> set[str]:
    """현재 DOM에 실린 생성 이미지 URL 집합."""
    return set(
        page.evaluate(
            f"""() => Array.from(document.querySelectorAll('img'))
                  .map(i => i.src).filter(s => s && s.includes('{MEDIA_SRC}'))"""
        )
    )


def is_generating(page) -> bool:
    """제출 버튼이 stop(중지)으로 바뀌어 있으면 생성 중. 아이콘 ligature라 언어 무관."""
    try:
        return icon(page, "stop").count() > 0
    except Exception:
        return False


FLOW_ERROR_MARKERS = ("문제가 발생", "Something went wrong", "오류가 발생")
RETRY_LABELS = ("다시 시도", "Try again", "재시도", "Retry")


def flow_error_shown(page) -> bool:
    """Flow가 생성 실패 배너를 띄웠는지."""
    try:
        body = page.inner_text("body")[-4000:]
    except Exception:
        return False
    return any(m in body for m in FLOW_ERROR_MARKERS)


def click_retry(page) -> bool:
    """Flow의 '다시 시도' 버튼을 누른다. 눌렀으면 True."""
    for label in RETRY_LABELS:
        try:
            btn = page.get_by_role("button", name=label, exact=True).first
            if btn.is_visible(timeout=1_000):
                btn.click()
                page.wait_for_timeout(4_000)
                print(f"    [재시도] Flow 오류 → '{label}' 클릭")
                return True
        except Exception:
            continue
    return False


def wait_idle(page, timeout_s: int = 180) -> bool:
    """에이전트가 유휴 상태(제출 가능)가 될 때까지 대기.

    wait_for_images 는 목표 장수가 채워지면 즉시 반환하지만, 그 시점에도 에이전트는
    응답을 마무리 중이라 제출 버튼이 아직 stop 이다. 이 상태에서 다음 프롬프트를
    제출하면 arrow_forward 가 없어 '제출 버튼 없음' 으로 실패한다. (실측된 버그)
    """
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if not is_generating(page) and icon(page, "arrow_forward").count() > 0:
            return True
        page.wait_for_timeout(3_000)
    return False


def submit_prompt(page, prompt: str) -> bool:
    """프롬프트 입력 후 제출. 생성이 실제로 시작되면 True.

    제출 버튼(arrow_forward)이 사라지고 stop 으로 바뀌는 것이 시작 신호다.
    """
    if not wait_idle(page):
        print("    [!] 이전 생성이 끝나지 않음 (유휴 대기 시간 초과)")

    # 전면 오버레이(공지 팝업 등)가 뜨면 <html>이 pointer events 를 가로채
    # 클릭이 전부 막힌다 (2026-08-23 실측 — 배치 도중에도 뜬다). Escape 로 닫는다.
    for _ in range(2):
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception:
            break

    tb = page.locator("[contenteditable=true]").first
    tb.click()
    page.wait_for_timeout(600)
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.keyboard.insert_text(prompt)
    page.wait_for_timeout(1_200)

    for attempt in (1, 2, 3):
        btn = icon(page, "arrow_forward")
        if not btn.count():
            print(f"    [!] 제출 버튼 없음 (시도 {attempt})")
            page.wait_for_timeout(3_000)
            continue
        try:
            btn.last.scroll_into_view_if_needed(timeout=5_000)
            btn.last.click(timeout=10_000)
        except Exception as exc:
            print(f"    [!] 제출 클릭 실패 (시도 {attempt}): {exc}")
            page.wait_for_timeout(3_000)
            continue
        # 생성 시작 확인 (최대 30초). 도중에 Flow 오류 배너가 뜨면 '다시 시도'를 누른다.
        for _ in range(15):
            page.wait_for_timeout(2_000)
            if is_generating(page):
                return True
            if flow_error_shown(page) and click_retry(page):
                for _ in range(10):
                    page.wait_for_timeout(2_000)
                    if is_generating(page):
                        return True
        print(f"    [!] 제출 반응 없음 (시도 {attempt})")
        if flow_error_shown(page):
            print("    [!] Flow가 생성 오류를 반환했습니다 — 일일 캡 소진 가능성이 높습니다.")
            return False
        page.wait_for_timeout(5_000)
    return False


# ---------------------------------------------------------------- 참고 이미지
def parse_refs(specs: list[str] | None) -> list[Path]:
    """--ref 인자를 실제 이미지 파일 목록으로 편다.

    파일 경로, 콤마 구분 목록, 폴더 경로를 모두 받는다.
    """
    if not specs:
        return []
    out: list[Path] = []
    for spec in specs:
        for token in str(spec).split(","):
            token = token.strip().strip('"').strip("'")
            if not token:
                continue
            p = Path(token).expanduser()
            if p.is_dir():
                out += sorted(f for f in p.iterdir() if f.suffix.lower() in REF_EXT)
            elif p.is_file():
                out.append(p)
            else:
                print(f"[!] 참고 이미지를 찾을 수 없음: {p}")
    return out


def upload_refs(page, paths: list[Path]) -> bool:
    """숨은 input[type=file] 로 참고 이미지를 애셋 라이브러리에 올린다."""
    inputs = page.locator("input[type=file]")
    if not inputs.count():
        print("[!] 파일 입력(input[type=file])이 DOM에 없습니다 — UI 변경 가능성")
        return False
    try:
        inputs.first.set_input_files([str(p) for p in paths], timeout=90_000)
    except Exception as exc:
        print(f"[!] 업로드 실패: {exc}")
        return False
    print(f"[참고] 업로드 {len(paths)}장 — 라이브러리 반영 대기")
    page.wait_for_timeout(6_000 + 2_500 * len(paths))
    return True


def ref_chip_count(page) -> int:
    """프롬프트 바에 붙은 참고 이미지 개수.

    썸네일은 3개까지만 보이고 나머지는 '+N' 칩으로 접힌다. 둘을 합쳐 센다.
    '프롬프트에 추가' 버튼 클릭 성공 여부보다 이 값이 정확한 판정 기준이다.
    """
    try:
        return page.evaluate(
            """() => {
                 const box = document.querySelector('[contenteditable=true]');
                 if (!box) return 0;
                 let el = box;
                 for (let i = 0; i < 6 && el.parentElement; i++) el = el.parentElement;
                 const thumbs = el.querySelectorAll('img').length;
                 const more = Array.from(el.querySelectorAll('*'))
                   .map(n => (n.childElementCount === 0 ? (n.textContent || '').trim() : ''))
                   .map(t => /^\\+(\\d+)$/.exec(t))
                   .filter(Boolean)
                   .map(m => parseInt(m[1], 10));
                 return thumbs + (more.length ? Math.max(...more) : 0);
               }"""
        )
    except Exception:
        return 0


def open_asset_panel(page) -> bool:
    """프롬프트 바의 '+' 버튼으로 애셋 패널을 연다."""
    for lig in ("add", "add_2", "attach_file", "add_circle"):
        btn = icon(page, lig)
        if not btn.count():
            continue
        try:
            btn.last.click(timeout=5_000)
            page.wait_for_timeout(2_500)
            if any(page.get_by_text(lbl, exact=True).count() for lbl in ADD_TO_PROMPT):
                return True
        except Exception:
            continue
    return False


def attach_refs(page, paths: list[Path]) -> int:
    """업로드한 이미지를 하나씩 '프롬프트에 추가' 한다. 최종 첨부 개수를 돌려준다.

    실측 주의: 3번째 애셋부터는 항목 클릭만으로 바로 추가되고 '프롬프트에 추가' 버튼이
    나타나지 않는다. 버튼 클릭 실패를 실패로 보면 안 되고, ref_chip_count 로 판정한다.
    """
    for p in paths:
        if not open_asset_panel(page):
            print(f"    [!] 애셋 패널 열기 실패 ({p.name})")
            continue
        try:
            page.get_by_text(p.name, exact=True).first.click(timeout=8_000)
            page.wait_for_timeout(2_000)
        except Exception as exc:
            print(f"    [!] 애셋 '{p.name}' 선택 실패: {exc}")
            continue
        for lbl in ADD_TO_PROMPT:
            try:
                page.get_by_role("button", name=lbl, exact=True).first.click(timeout=4_000)
                page.wait_for_timeout(2_500)
                break
            except Exception:
                continue
        page.wait_for_timeout(1_000)
    # 프롬프트 바 주변의 img 를 세는 방식이라 과다 집계될 수 있다(실측 5장 첨부에 8).
    # 정확한 장수보다 '붙었는가'가 중요하므로 요청 장수로 클램프해서 보고한다.
    n = min(ref_chip_count(page), len(paths))
    print(f"[참고] 프롬프트에 첨부됨: 약 {n}/{len(paths)}장")
    return n


def dump_failure(page, out_dir: Path, tag: str) -> None:
    """제출 실패 시 화면 상태 저장 — 일일 캡 소진/정책 거부 등 원인 파악용."""
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out_dir / f"FAIL_{tag}.png"))
        (out_dir / f"FAIL_{tag}.txt").write_text(page.inner_text("body")[:20_000], encoding="utf-8")
        print(f"    [진단] {out_dir / f'FAIL_{tag}.png'}")
    except Exception:
        pass


def wait_for_images(page, before: set[str], want: int, timeout_s: int) -> list[str]:
    """새 이미지가 want 장 나오거나 생성이 끝날 때까지 대기."""
    t0 = time.time()
    idle = 0
    while time.time() - t0 < timeout_s:
        page.wait_for_timeout(6_000)
        new = media_srcs(page) - before
        gen = is_generating(page)
        el = int(time.time() - t0)
        print(f"    t={el:>3}s  new={len(new)}  generating={gen}")
        if len(new) >= want:
            return sorted(new)
        if gen:
            idle = 0
            continue
        # 생성 중 Flow 오류가 뜨면 '다시 시도'로 복구를 시도한다
        if not new and flow_error_shown(page) and click_retry(page):
            idle = 0
            continue
        # 생성이 끝났는데 목표 미달 — 지연 렌더를 감안해 몇 사이클만 더 본다
        idle += 1
        if idle >= 3:
            return sorted(new)
    return sorted(media_srcs(page) - before)


def parse_only(spec: str | None, n: int) -> list[int]:
    """`--only 2,5-7` → [2,5,6,7]. 범위 밖 번호는 버린다. 없으면 전체."""
    if not spec:
        return list(range(1, n + 1))
    picked: set[int] = set()
    for part in spec.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part[1:]:
            a, _, b = part.partition("-")
            try:
                picked.update(range(int(a), int(b) + 1))
            except ValueError:
                continue
        else:
            try:
                picked.add(int(part))
            except ValueError:
                continue
    return [i for i in sorted(picked) if 1 <= i <= n]


# ---------------------------------------------------------------- 메인
def main() -> int:
    ap = argparse.ArgumentParser(description="Google Flow 이미지 배치 생성/다운로드")
    ap.add_argument("--prompts", required=True, help="프롬프트 파일 경로 또는 '||' 구분 문자열")
    ap.add_argument("--model", default="nano-banana-2", choices=sorted(MODEL_MENU))
    ap.add_argument("--ratio", default="1:1", choices=sorted(RATIO_ICON))
    # 4장이 동시에 생성되므로 소요 시간이 1장과 사실상 같다 → 낮출 이유가 없다. 항상 x4가 기본.
    ap.add_argument("--count", type=int, default=4, choices=[1, 2, 3, 4],
                    help="프롬프트당 장수 (기본 4 — 동시 생성이라 줄여도 빨라지지 않는다)")
    ap.add_argument("--out", default=None,
                    help="저장 폴더 (미지정 시 다운로드 폴더 아래 image-flow/<프로젝트명>)")
    ap.add_argument("--ref", action="append", default=None,
                    help="참고 이미지 경로. 여러 번 쓰거나 콤마로 나열, 폴더도 가능. "
                         "지정하면 Flow 프롬프트에 첨부해 얼굴/스타일을 참조시킨다")
    ap.add_argument("--timeout", type=int, default=420, help="프롬프트당 대기 초")
    ap.add_argument("--project", default=None,
                    help="프로젝트 이름. 미지정 시 'image-flow YYYY-MM-DD HH:MM' 자동 부여")
    ap.add_argument("--reuse", action="store_true",
                    help="새로 만들지 않고 기존 프로젝트를 재사용한다 (--project 이름 우선, 없으면 최근 것)")
    ap.add_argument("--new-project", action="store_true",
                    help="(하위호환) 기본 동작이 이미 새 프로젝트 생성이라 무시된다")
    # 헤드리스는 Google이 생성 요청을 403으로 차단한다(2026-08-07 실측). 창 띄우기가 기본.
    ap.add_argument("--only", default=None,
                    help="이 번호의 프롬프트만 생성한다 (1부터, 쉼표·범위 — 예: 2,5-7). "
                         "번호와 파일명 접두사는 원본 순서를 그대로 유지하므로, "
                         "한도로 빠진 장만 골라 다시 뽑을 때 쓴다.")
    ap.add_argument("--headless", action="store_true",
                    help="창 없이 실행 (생성이 403으로 차단되므로 정찰 용도에만 쓸 것)")
    ap.add_argument("--headed", action="store_true",
                    help="(하위호환) 기본이 이미 창 띄우기라 무시된다")
    args = ap.parse_args()

    prompts = read_prompts(args.prompts)
    if not prompts:
        print("[ERROR] 프롬프트가 비었습니다.", file=sys.stderr)
        return 2

    todo = parse_only(args.only, len(prompts))
    if not todo:
        print(f"[ERROR] --only {args.only} 가 프롬프트 1~{len(prompts)} 범위와 겹치지 않습니다.",
              file=sys.stderr)
        return 2

    project_name = args.project or auto_project_name()
    out_dir = Path(args.out) if args.out else default_out_dir(project_name)
    refs = parse_refs(args.ref)
    if args.only:
        print(f"[*] --only {args.only} → 프롬프트 {todo} 번만 생성 "
              f"(번호·파일명은 원본 순서 유지)")
    print(f"[*] 프롬프트 {len(todo)}개 × {args.count}장 = 최대 {len(todo) * args.count}장")
    print(f"[*] 저장 폴더: {out_dir}")
    if refs:
        print(f"[*] 참고 이미지 {len(refs)}장: {', '.join(p.name for p in refs)}")

    pw, ctx, page = launch(headless=args.headless)
    report: list[dict] = []
    try:
        sess = require_login(ctx)
        print(f"[*] 계정: {sess.get('user', {}).get('email')}")

        enter_app(page)
        proj = open_project(page, args.reuse, project_name)
        print(f"[*] 프로젝트: {proj}")

        configure(page, args.model, args.ratio, args.count)

        attached = 0
        if refs:
            wait_idle(page)
            if upload_refs(page, refs):
                attached = attach_refs(page, refs)
            if not attached:
                print("[!] 참고 이미지가 프롬프트에 붙지 않았습니다 — 참조 없이 진행합니다")
                dump_failure(page, out_dir, "ref")

        # 리포트는 «프롬프트 하나 끝날 때마다» 덮어쓴다. 한도에 걸려 중간에 죽어도
        # 어디까지 나왔는지가 파일에 남아야 호출자가 «빠진 것만» 다시 돌릴 수 있다.
        def flush() -> None:
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "report.json").write_text(
                json.dumps(
                    {
                        "account": sess.get("user", {}).get("email"),
                        "project": proj,
                        "model": args.model,
                        "ratio": args.ratio,
                        "count": args.count,
                        "refs": [str(p) for p in refs],
                        "refs_attached": attached,
                        "out_dir": str(out_dir.resolve()),
                        "requested": todo,
                        "total_prompts": len(prompts),
                        "results": report,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        for pos, i in enumerate(todo, 1):
            raw = prompts[i - 1]
            prompt = force_image_intent(strip_orientation(raw))
            print(f"\n[{pos}/{len(todo)}] (#{i}) {prompt[:70]}...")
            if not submit_prompt(page, prompt):
                print("    → 제출 실패 (생성 시작 안 됨) — 건너뜀")
                dump_failure(page, out_dir, f"{i:02d}")
                report.append({"index": i, "prompt": prompt, "generated": 0, "saved": [],
                               "error": "submit_failed"})
                flush()
                continue
            # 기준선은 '생성이 시작된 뒤'에 잡는다. 업로드한 참고 이미지도 생성물과 같은
            # media URL 로 렌더되므로, 제출 전에 잡으면 참고 사진이 결과로 오인된다. (실측)
            page.wait_for_timeout(8_000)
            before = media_srcs(page)
            urls = wait_for_images(page, before, args.count, args.timeout)
            print(f"    → 생성 {len(urls)}장")
            err = None
            if not urls:
                dump_failure(page, out_dir, f"{i:02d}_zero")
                # 0장인 이유를 구분해 둔다. «한도 소진»이면 이 계정으로 재시도해 봐야
                # 소용없고, 호출자가 다른 계정으로 넘겨야 한다.
                err = "flow_error" if flow_error_shown(page) else "timeout"

            saved = []
            for n, url in enumerate(urls, 1):
                name = f"{i:02d}_{slug(raw)}_{n}"
                p = download_url(ctx, url, out_dir, name)
                if p:
                    saved.append(str(p))
                    print(f"      saved {p.name} ({p.stat().st_size:,}B)")
            rec = {"index": i, "prompt": prompt, "generated": len(urls), "saved": saved}
            if err:
                rec["error"] = err
            report.append(rec)
            flush()

        flush()
        done = [r["index"] for r in report if r["saved"]]
        missing = [i for i in todo if i not in done]
        total = sum(len(r["saved"]) for r in report)
        print(f"\n[완료] 총 {total}장 저장 → {out_dir.resolve()}")
        if missing:
            print(f"[!] 빠진 프롬프트: {','.join(map(str, missing))} "
                  f"— 다시 돌리려면 --only {','.join(map(str, missing))}")
            # 3 = «일부만 나왔다». 호출자가 빠진 번호만 골라 재시도하라는 신호.
            return 3 if total else 1
        return 0
    finally:
        close(pw, ctx)


if __name__ == "__main__":
    raise SystemExit(main())
