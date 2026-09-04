"""flow-image-JJ 공통 모듈 — 브라우저 기동 / 프로필 관리 / 로그인 상태 확인."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import BrowserContext, sync_playwright

# 전용 크롬 프로필 (사용자의 일반 크롬과 완전 분리 — 잠금 충돌 없음)
# 계정을 여러 개 쓰려면 IMAGE_FLOW_PROFILE 환경변수로 프로필 경로를 갈아끼운다.
PROFILE_DIR = Path(os.environ.get("IMAGE_FLOW_PROFILE", Path.home() / ".codex" / ".image-flow-profile"))

FLOW_URL = "https://labs.google/fx/tools/flow"
# 실제 앱(프로젝트 목록). 미로그인 시 accounts.google.com 으로 리다이렉트된다.
FLOW_APP_URL = "https://labs.google/fx/tools/flow/project"

# 자동화 탐지 회피 + 안정화 플래그
LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-features=Translate,OptimizationHints",
]

# 창 위치. 다른 위치를 원하면 IMAGE_FLOW_WINDOW_POS="x,y" 환경변수로 덮어쓴다.
_WIN_POS = os.environ.get("IMAGE_FLOW_WINDOW_POS", "60,40")
if _WIN_POS:
    LAUNCH_ARGS.append(f"--window-position={_WIN_POS}")

VIEWPORT = {"width": 1600, "height": 1000}


def launch(headless: bool = True, slow_mo: int = 0):
    """persistent context를 띄우고 (playwright, context, page) 반환.

    반드시 close(pw, ctx)로 정리할 것.
    """
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    pw = sync_playwright().start()
    try:
        ctx: BrowserContext = pw.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="chrome",
            headless=headless,
            slow_mo=slow_mo,
            args=LAUNCH_ARGS,
            viewport=VIEWPORT,
            locale="en-US",
            accept_downloads=True,
        )
    except Exception as exc:  # 크롬 채널 없거나 프로필 손상
        pw.stop()
        raise RuntimeError(
            f"크롬 기동 실패: {exc}\n"
            f"프로필 경로: {PROFILE_DIR}\n"
            "→ 시스템에 Chrome이 설치돼 있는지 확인하고, "
            "프로필이 깨졌으면 지운 뒤 flow_login.py를 다시 실행하세요."
        ) from exc

    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    # navigator.webdriver 흔적 제거
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    return pw, ctx, page


def close(pw, ctx) -> None:
    try:
        ctx.close()
    except Exception:
        pass
    try:
        pw.stop()
    except Exception:
        pass


def dismiss_overlays(page) -> None:
    """'새 소식(changelog)' 모달 등 클릭을 가로채는 오버레이를 치운다.

    실측: Flow 홈에 changelog iframe 모달이 떠 프로젝트 카드·add_2
    버튼 클릭이 전부 «subtree intercepts pointer events» 로 타임아웃했다.
    닫기 버튼 → Escape → (그래도 남으면) 장식용 오버레이 DOM 제거 순으로 처리한다.
    """
    try:
        if not page.evaluate(
            """() => !!(document.querySelector("iframe[src*='/changelogs/']") ||
                        document.querySelector("[data-state='open'][aria-hidden='true']"))"""
        ):
            return
    except Exception:
        return

    for label in ("close", "cancel"):
        try:
            btn = page.locator(f"button:has(:text-is('{label}'))").first
            if btn.is_visible(timeout=1000):
                btn.click(timeout=2000)
                page.wait_for_timeout(800)
        except Exception:
            pass
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)
    except Exception:
        pass

    try:
        removed = page.evaluate(
            """() => {
                 let n = 0;
                 const hide = (el) => {
                   if (!el) return;
                   el.style.setProperty('display', 'none', 'important');
                   el.style.setProperty('pointer-events', 'none', 'important');
                   n++;
                 };
                 // changelog iframe -> 가장 가까운 dialog 조상만 숨긴다 (제거 금지: 앱 셸까지 날아간다)
                 document.querySelectorAll("iframe[src*='/changelogs/']").forEach(f => {
                   let el = f, dlg = null;
                   for (let i = 0; i < 8 && el && el !== document.body; i++) {
                     if (el.getAttribute &&
                         (el.getAttribute('role') === 'dialog' || el.hasAttribute('data-state'))) {
                       dlg = el; break;
                     }
                     el = el.parentElement;
                   }
                   hide(dlg || f);
                 });
                 // 클릭을 가로채는 «빈» Radix 오버레이만
                 document.querySelectorAll("[data-state='open'][aria-hidden='true']").forEach(d => {
                   if (d.children.length === 0) hide(d);
                 });
                 return n;
               }"""
        )
        if removed:
            print(f"[오버레이] changelog/모달 {removed}개 차단")
            page.wait_for_timeout(600)
    except Exception:
        pass


def accept_cookie_banner(page) -> None:
    """쿠키/약관 배너가 있으면 닫는다 (없으면 조용히 통과)."""
    dismiss_overlays(page)
    for label in ("Agree", "Accept all", "I agree", "No thanks", "Got it"):
        try:
            btn = page.get_by_role("button", name=label, exact=True).first
            if btn.is_visible(timeout=1200):
                btn.click()
                page.wait_for_timeout(1200)
                return
        except Exception:
            continue


# NextAuth 세션 엔드포인트 — 로그인 여부의 유일하게 신뢰할 수 있는 근거.
# 랜딩 페이지·앱 빈 화면은 미로그인 상태에서도 렌더되므로 DOM 텍스트로 판정하면 반드시 오탐한다.
SESSION_URL = "https://labs.google/fx/api/auth/session"


def get_session(ctx) -> dict:
    """로그인 세션 정보를 반환. 미로그인이면 빈 dict."""
    try:
        resp = ctx.request.get(SESSION_URL, timeout=30_000)
        if not resp.ok:
            return {}
        data = resp.json()
        return data if isinstance(data, dict) and data.get("user") else {}
    except Exception:
        return {}


def is_logged_in(ctx) -> bool:
    """Flow 로그인 여부. page가 아니라 BrowserContext를 받는다."""
    return bool(get_session(ctx))


def open_app(page, timeout: int = 90_000):
    """앱 진입.

    labs.google/fx/tools/flow 는 로그인 상태와 무관하게 마케팅 랜딩을 렌더한다.
    랜딩이 뜨면 'Create with Google Flow'를 눌러 실제 앱으로 넘어간다.
    """
    page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=timeout)
    page.wait_for_timeout(4_000)
    accept_cookie_banner(page)

    try:
        btn = page.get_by_role("button", name="Create with Google Flow").first
        if btn.is_visible(timeout=4_000):
            btn.click()
            page.wait_for_timeout(9_000)
    except Exception:
        pass

    accept_cookie_banner(page)
    page.wait_for_timeout(3_000)
    return page


def require_login(ctx) -> dict:
    sess = get_session(ctx)
    if not sess:
        print(
            "[ERROR] Flow 로그인 세션이 없습니다.\n"
            "  python scripts/flow_login.py 를 먼저 실행해 1회 로그인하세요.",
            file=sys.stderr,
        )
        sys.exit(2)
    return sess
