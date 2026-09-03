"""1회 실행 — 전용 크롬 프로필에 Google Flow 로그인 세션을 저장한다.

창이 뜨면 사용자가 직접 Google 계정으로 로그인한다.
(에이전트는 자격증명을 대신 입력하지 않는다.)

로그인 판정은 DOM 텍스트가 아니라 NextAuth 세션 API(`/fx/api/auth/session`)로 한다.
랜딩 페이지와 앱 빈 화면은 미로그인 상태에서도 렌더되므로 DOM 판정은 반드시 오탐한다.
"""
from __future__ import annotations

import sys
import time

from flow_common import FLOW_URL, PROFILE_DIR, accept_cookie_banner, close, get_session, launch

TIMEOUT_SEC = 900  # 15분


def main() -> int:
    print(f"[*] 전용 프로필: {PROFILE_DIR}")
    print("[*] 크롬 창을 엽니다. Google 계정으로 로그인해 주세요.")
    print("[*] 로그인 완료(세션 토큰 발급)가 확인될 때까지 창을 닫지 않습니다.")
    pw, ctx, page = launch(headless=False)
    try:
        page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(3_000)
        accept_cookie_banner(page)

        # OAuth 시작
        try:
            page.get_by_role("button", name="Create with Google Flow").first.click(timeout=15_000)
        except Exception:
            print("[!] 진입 버튼 자동 클릭 실패 — 창에서 직접 'Create with Google Flow'를 눌러 주세요.")

        deadline = time.time() + TIMEOUT_SEC
        while time.time() < deadline:
            sess = get_session(ctx)
            if sess:
                user = sess.get("user", {})
                page.wait_for_timeout(3_000)  # 디스크 flush
                print(f"[OK] 로그인 완료: {user.get('email') or user.get('name') or '(unknown)'}")
                print(f"[OK] 세션 만료: {sess.get('expires', 'n/a')}")
                return 0
            print(f"    ... 로그인 대기 중 ({int(deadline - time.time())}s 남음)", flush=True)
            page.wait_for_timeout(5_000)

        print("[FAIL] 시간 초과 — 세션 토큰이 발급되지 않았습니다.", file=sys.stderr)
        return 1
    finally:
        close(pw, ctx)


if __name__ == "__main__":
    raise SystemExit(main())
