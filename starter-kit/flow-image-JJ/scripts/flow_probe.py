"""Flow 앱 정찰 — 프로젝트 화면 DOM + 이미지 생성 네트워크 요청 캡처.

셀렉터/엔드포인트가 바뀌었을 때 이 스크립트로 재파악한다.

사용:
  python flow_probe.py                 # 앱 화면만 덤프 (헤드리스)
  python flow_probe.py --headed        # 창 띄우고 관찰
  python flow_probe.py --capture       # 네트워크 요청 캡처 모드(수동 생성 1회 관찰)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from flow_common import close, get_session, launch, open_app

INTERESTING = ("aisandbox", "/api/trpc", "generate", "image", "media")


def dump_page(page, out: Path, tag: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / f"{tag}.png"), full_page=False)
    (out / f"{tag}_body.txt").write_text(page.inner_text("body")[:30000], encoding="utf-8")
    (out / f"{tag}.html").write_text(page.content(), encoding="utf-8")
    elems = page.evaluate(
        """() => Array.from(document.querySelectorAll(
             'button,a[href],[role=button],[role=combobox],[role=menuitem],[role=option],input,textarea,[contenteditable=true],select'))
           .filter(e => e.offsetParent || e.getClientRects().length)
           .slice(0,400).map(e => ({
             tag: e.tagName.toLowerCase(),
             role: e.getAttribute('role') || '',
             text: (e.innerText || e.value || e.placeholder || '').trim().slice(0,80),
             aria: e.getAttribute('aria-label') || '',
             testid: e.getAttribute('data-testid') || '',
             cls: (typeof e.className === 'string' ? e.className : '').slice(0,80)
           }))"""
    )
    (out / f"{tag}_elements.json").write_text(json.dumps(elems, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[{tag}] interactive elements: {len(elems)}")
    for e in elems[:80]:
        lab = e["text"] or e["aria"] or e["testid"] or e["cls"]
        print(f"  {e['tag']:<12} {e['role']:<10} | {lab[:64]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--capture", action="store_true", help="네트워크 캡처 모드")
    ap.add_argument("--seconds", type=int, default=180, help="캡처 관찰 시간")
    ap.add_argument("--out", default="probe")
    args = ap.parse_args()

    out = Path(args.out)
    captured: list[dict] = []

    pw, ctx, page = launch(headless=not args.headed)
    try:
        if args.capture:
            def on_request(req):
                if req.method != "POST":
                    return
                if not any(k in req.url for k in INTERESTING):
                    return
                try:
                    body = req.post_data
                except Exception:
                    body = None
                captured.append({"url": req.url, "headers": dict(req.headers), "body": body})
                print(f"[REQ] {req.url[:130]}")

            ctx.on("request", on_request)

        sess = get_session(ctx)
        print("SESSION:", sess.get("user", {}).get("email") or "(none)")
        if not sess:
            print("!! 로그인 필요 — flow_login.py 실행")
            return 2
        open_app(page)
        print("URL:", page.url)

        dump_page(page, out, "app")

        if args.capture:
            print(f"\n[*] {args.seconds}초 동안 관찰합니다. 창에서 이미지를 1회 생성하세요.")
            page.wait_for_timeout(args.seconds * 1000)
            out.mkdir(parents=True, exist_ok=True)
            (out / "requests.json").write_text(
                json.dumps(captured, ensure_ascii=False, indent=1), encoding="utf-8"
            )
            print(f"[saved] {len(captured)} requests -> {out/'requests.json'}")

        print(f"\n[saved] {out.resolve()}")
        return 0
    finally:
        close(pw, ctx)


if __name__ == "__main__":
    raise SystemExit(main())
