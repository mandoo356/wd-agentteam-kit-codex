r"""슬랙 열쇠 3개를 점검한다. 값·응답 본문·소켓 URL은 출력하지 않는다.

PowerShell (slack-server 폴더):
    & "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" slack_check.py

환경점검.bat이 저장 직후 호출한다. 멤버 ID는 형식만 검사하므로
실제 소속·본인 여부나 봇과 앱의 동일 워크스페이스까지 보장하지 않는다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV = HERE / ".env"
REQUIRED = ("SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "OWNER_USER_ID")


def load_env(path: Path) -> dict[str, str]:
    """BOM은 허용하되 값의 공백·따옴표는 검사 단계에 그대로 넘긴다."""
    vals = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            vals[key.strip().upper()] = value
    return vals


def validate_values(vals: dict[str, str]) -> list[str]:
    errors = []
    for key in REQUIRED:
        value = vals.get(key, "")
        if not value.strip():
            errors.append(f"NG {key}가 비어 있습니다")
        elif value != value.strip() or value[:1] in "\"'" or value[-1:] in "\"'":
            errors.append(f"NG {key}의 앞뒤 공백·따옴표를 지우세요")
        elif key == "OWNER_USER_ID":
            if not re.fullmatch(r"[UW][A-Z0-9]{8,}", value):
                errors.append("NG OWNER_USER_ID는 U 또는 W로 시작하는 멤버 ID여야 합니다")
        else:
            prefix = "xoxb-" if key == "SLACK_BOT_TOKEN" else "xapp-"
            if not value.startswith(prefix) or len(value) <= len(prefix) or any(c.isspace() for c in value):
                errors.append(f"NG {key}는 {prefix}로 시작하는 토큰이어야 합니다")
    return errors


def api_failure(kind: str, code: object) -> str:
    """응답 error도 신뢰하지 않는다. 알려진 코드만 고정 안내로 변환한다."""
    if code in ("invalid_auth", "not_authed", "account_inactive", "token_revoked"):
        return f"NG {kind} 인증 실패 — 해당 토큰을 다시 복사하세요"
    if code in ("missing_scope", "not_allowed_token_type"):
        return ("NG 앱 토큰 권한 확인 — App-Level Tokens에서 connections:write를 확인하세요"
                if kind == "앱 토큰" else "NG 봇 토큰 종류·권한을 확인하세요")
    return f"NG {kind} 확인 실패 — Slack 앱 설정과 인터넷·방화벽을 확인하세요"


def check_values(vals: dict[str, str], client_factory=None, emit=print) -> int:
    """클라이언트를 주입할 수 있어 실제 연결 없이 실패 경로를 검증한다."""
    errors = validate_values(vals)
    if errors:
        for message in errors:
            emit(message)
        return 1
    if client_factory is None:
        try:
            from slack_sdk import WebClient
        except ImportError:
            emit('NG slack_sdk가 없습니다 — & "$env:LOCALAPPDATA\\Programs\\Python\\Python314\\python.exe" -m pip install -r requirements.txt')
            return 1
        client_factory = WebClient
    for kind, key, method in (
        ("봇 토큰", "SLACK_BOT_TOKEN", "auth_test"),
        ("앱 토큰", "SLACK_APP_TOKEN", "apps_connections_open"),
    ):
        try:
            response = getattr(client_factory(token=vals[key]), method)()
            if response.get("ok") is not True:
                emit(api_failure(kind, response.get("error")))
                return 1
        except Exception as error:
            # SlackApiError 외의 예외·응답 본문도 화면에 유출하지 않는다.
            try:
                response = getattr(error, "response", None)
                code = response.get("error") if response is not None else None
            except Exception:
                code = None
            emit(api_failure(kind, code))
            return 1
        emit(f"OK {kind} 확인 통과")
    emit("OK 멤버 ID 형식 통과 — 실제 소속·본인 여부는 조회하지 않았습니다")
    emit("OK 슬랙 열쇠 점검 통과 — 서버 실행 후 본인 메시지 응답을 확인하세요")
    return 0


def main(env_path: Path = ENV, client_factory=None, emit=print) -> int:
    try:
        values = load_env(env_path)
    except FileNotFoundError:
        emit("NG .env 파일이 없습니다 — 환경점검.bat에서 열쇠 3개를 입력하세요")
        return 1
    except Exception:
        emit("NG .env 파일을 읽지 못했습니다 — UTF-8 저장 형식·파일 권한을 확인하세요")
        return 1
    return check_values(values, client_factory, emit)


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
