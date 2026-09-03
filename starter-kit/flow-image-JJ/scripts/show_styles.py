"""카드뉴스 스타일 20종 대시보드를 새 창으로 띄운다.

스타일 번호를 사용자에게 묻기 **전에 반드시 실행**한다.
샘플 이미지를 눈으로 보고 고를 수 있어야 하며, 번호만 물어보면 안 된다.

사용: python show_styles.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import urllib.request

LIVE_URL = "https://jj-aiedu.vercel.app/style/card-styles.html"


def _open(target: str) -> bool:
    """기본 브라우저로 새 창을 연다."""
    try:
        if sys.platform == "win32":
            os.startfile(target)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", target], check=True)
        else:
            subprocess.run(["xdg-open", target], check=True)
        return True
    except Exception as exc:
        print(f"[!] 열기 실패 ({target}): {exc}", file=sys.stderr)
        return False


def _reachable(url: str, timeout: int = 6) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310
            return r.status == 200
    except Exception:
        return False


def main() -> int:
    if _reachable(LIVE_URL) and _open(LIVE_URL):
        print(f"[OK] 스타일 대시보드를 새 창으로 열었습니다: {LIVE_URL}")
        return 0

    print("[FAIL] 대시보드를 열지 못했습니다. 사용자에게 URL을 직접 안내하세요:",
          LIVE_URL, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
