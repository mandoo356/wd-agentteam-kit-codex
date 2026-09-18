"""저녁 8시 자동 블로그.

오늘 끝난 강의가 있으면 일정매니저가 일정을 확인하고 블로그대리가 원고를
작성해 네이버 임시저장함에 넣는다. 공개 발행은 하지 않는다.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
LOG = HERE / "evening_blog.log"


def load_env() -> dict[str, str]:
    """슬랙 서버와 이 폴더의 .env에서 값이 있는 항목만 읽는다."""
    env: dict[str, str] = {}
    for path in (KIT / "slack-server" / ".env", HERE / ".env"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            if value:
                env[key.strip()] = value
    return env


def log(message: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")
    print(message)


def notify(webhook: str, message: str) -> None:
    """P20-b에서 만든 Incoming Webhook으로 결과를 알린다."""
    if not webhook:
        log("SLACK_WEBHOOK_URL이 없어 슬랙 알림은 건너뜁니다.")
        return
    request = urllib.request.Request(
        webhook,
        data=json.dumps({"text": message}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response.read()
        log("슬랙 알림을 보냈습니다.")
    except Exception as exc:  # 알림 실패가 원고 작업 결과를 바꾸지는 않는다.
        log(f"슬랙 알림 실패: {exc}")


def find_codex() -> str:
    """PowerShell 실행 정책의 영향을 덜 받도록 codex.cmd를 우선한다."""
    explicit = os.environ.get("CODEX_CLI", "").strip()
    if explicit and Path(explicit).is_file():
        return explicit
    for name in ("codex.cmd", "codex.exe", "codex"):
        found = shutil.which(name)
        if found and not found.lower().endswith(".ps1"):
            return found
    for candidate in (
        os.path.expandvars(r"%APPDATA%\npm\codex.cmd"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\codex\codex.exe"),
    ):
        if Path(candidate).is_file():
            return candidate
    raise RuntimeError(
        "codex 명령어를 찾을 수 없습니다. "
        "검은 창에서 npm.cmd install -g @openai/codex를 실행한 뒤 다시 시도하세요."
    )


def ask(cli: str, agent: str, request: str, timeout: int) -> str:
    """Codex 비대화 모드로 지정 직원에게 한 번 요청하고 마지막 답을 돌려준다."""
    prompt = (
        f"[예약 작업 요청. 담당 직원: @{agent}]\n"
        f"먼저 .codex/agents/{agent}.toml을 읽고 그 직원의 정체성과 규칙대로 처리할 것.\n"
        "AGENTS.md와 workspace/memory/facts.md를 먼저 읽을 것.\n"
        "모르는 고객사·일정·사실은 지어내지 말 것.\n\n"
        f"{request}"
    )
    command = [
        cli,
        "exec",
        "--json",
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
        "-",
    ]
    process = subprocess.run(
        command,
        input=prompt.encode("utf-8"),
        capture_output=True,
        cwd=str(KIT),
        timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    stdout = process.stdout.decode("utf-8", errors="replace")
    stderr = process.stderr.decode("utf-8", errors="replace").strip()
    messages: list[str] = []
    errors: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and item.get("text"):
                messages.append(str(item["text"]))
        elif event.get("type") in {"error", "turn.failed"}:
            errors.append(str(event.get("message") or event.get("error") or event))
    if process.returncode != 0:
        detail = " / ".join(errors) or stderr or f"종료코드 {process.returncode}"
        raise RuntimeError(f"{agent} 실행 실패: {detail[-1000:]}")
    if not messages:
        raise RuntimeError(f"{agent}가 빈 응답을 반환했습니다: {stderr[-500:]}")
    return messages[-1].strip()


def main() -> int:
    env = load_env()
    webhook = env.get("SLACK_WEBHOOK_URL", "")
    cli = find_codex()
    today = date.today().isoformat()
    log(f"시작 — 오늘 {today}")

    calendar_request = f"""오늘({today}) 구글 캘린더를 조회해줘.

오늘 끝난 강의·교육 일정이 있으면 아래 형식으로만 답해. 다른 말은 붙이지 마.

LECTURE_TODAY: yes
CLIENT: <고객사>
LECTURE_NAME: <강의명>
LOCATION: <장소>
DURATION: <시간>

없으면 `LECTURE_TODAY: no` 한 줄만 답해.
조회만 하고 등록·수정하지 마. 캘린더를 읽지 못했으면 추측하지 말고
`LECTURE_TODAY: error` 다음 줄에 `REASON: <이유>`를 적어."""

    calendar_result = ask(cli, "staff4", calendar_request, timeout=300)
    if "LECTURE_TODAY: error" in calendar_result:
        log(f"캘린더 조회 실패 — {calendar_result[:300]}")
        notify(webhook, "📅 저녁 블로그가 캘린더를 읽지 못했어요. 저녁블로그/evening_blog.log를 확인해 주세요.")
        return 1
    if "LECTURE_TODAY: yes" not in calendar_result:
        log("오늘 강의 없음 — 조용히 끝냅니다.")
        return 0

    info: dict[str, str] = {}
    for line in calendar_result.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            info[key.strip()] = value.strip()
    client = info.get("CLIENT") or "(고객사 확인 필요)"
    lecture = info.get("LECTURE_NAME") or "(강의명 확인 필요)"
    log(f"오늘 강의 있음 — {client} / {lecture}")

    blog_request = f"""오늘({today}) 다녀온 강의로 블로그 글을 써줘.

- 고객사: {client}
- 강의명: {lecture}
- 장소: {info.get('LOCATION', '(정보 없음)')}
- 시간: {info.get('DURATION', '(정보 없음)')}

순서대로 끝까지 처리해. 중간에 묻지 마.
1. 카드 P4-0에서 만든 블로그 스킬로 원고를 쓴다.
   `workspace/결과물/blog/{today}_{client}/` 안에 post.md·titles.md·hashtags.md를 저장한다.
2. `naver-blog/naver_draft.py`로 네이버 블로그 임시저장까지 한다.
   임시저장 목록에서 제목을 확인하기 전에는 저장했다고 보고하지 않는다.
   사진과 AI 삽화는 넣지 않는다.
3. 공개 발행 버튼은 절대 누르지 않는다.

끝나면 슬랙 알림용 답만 5줄 이내로 작성해.
- 어떤 강의 글을 썼는지
- 제목 후보 3개
- 임시저장 확인 여부
- 비워둔 정보가 있으면 그 항목
캐릭터 인사말과 서명은 빼."""

    blog_result = ask(cli, "staff3", blog_request, timeout=1800)
    notify(webhook, blog_result or "✍️ 블로그 초안이 준비됐어요.")
    log("작업을 마쳤습니다.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired:
        log("Codex 작업 시간이 초과됐습니다.")
        sys.exit(2)
    except Exception as exc:
        log(f"실패 — {exc}")
        sys.exit(1)
