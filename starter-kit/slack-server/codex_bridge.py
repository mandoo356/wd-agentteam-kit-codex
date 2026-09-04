"""슬랙에서 온 말을 Codex CLI에 전달하고 답을 받아오는 다리.

강의용 기본값은 YOLO 모드다. Codex가 확인창 없이 파일·명령 작업을 끝까지
수행하도록 ``--dangerously-bypass-approvals-and-sandbox`` 를 사용한다.
따라서 server.py의 OWNER_USER_ID 검사를 끄지 않는다.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger("agent.bridge")
KIT_ROOT = Path(__file__).resolve().parent.parent
QUERY_TIMEOUT_SEC = int(os.environ.get("QUERY_TIMEOUT_SEC", "300"))
RETRY_TIMEOUT_SEC = int(os.environ.get("RETRY_TIMEOUT_SEC", "180"))
SESSION_MAX_AGE_SEC = int(os.environ.get("SESSION_MAX_AGE_SEC", "10800"))
SESSION_FILE = Path(__file__).resolve().parent / ".codex_session.json"


def yolo_enabled() -> bool:
    """dotenv가 로드된 뒤의 값을 읽는다. 기본값은 강의 요청대로 켬."""
    return os.environ.get("CODEX_YOLO", "1").strip().lower() not in {
        "0", "false", "no", "off"
    }


class CodexError(RuntimeError):
    pass


def find_codex_cli(explicit: Optional[str] = None) -> str:
    """PowerShell 실행 정책에 막히는 codex.ps1보다 codex.cmd를 우선한다."""
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
    raise CodexError(
        "codex 명령어를 찾을 수 없습니다.\n"
        "  → 검은 창에서 npm install -g @openai/codex\n"
        "  → 그래도 안 되면 .env에 CODEX_CLI=전체경로를 적어주세요"
    )


class AgentPool:
    """Codex 요청을 한 번에 하나씩 실행하고 직전 세션을 이어 쓴다."""

    def __init__(self, workspace: Path, cli_path: str):
        self.workspace = workspace
        self.cli_path = cli_path
        self._lock = asyncio.Lock()
        self._session_id: Optional[str] = self._load_session()

    @staticmethod
    def _load_session() -> Optional[str]:
        try:
            data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        except Exception:
            return None
        session_id = data.get("session_id")
        updated_at = data.get("updated_at", 0)
        if not session_id or time.time() - updated_at > SESSION_MAX_AGE_SEC:
            return None
        log.info("직전 Codex 대화를 이어받습니다")
        return str(session_id)

    def _save_session(self, session_id: str) -> None:
        self._session_id = session_id
        SESSION_FILE.write_text(
            json.dumps({"session_id": session_id, "updated_at": time.time()}, ensure_ascii=False),
            encoding="utf-8",
        )

    def forget_session(self) -> None:
        self._session_id = None
        SESSION_FILE.unlink(missing_ok=True)

    def _command(self, resume: bool) -> list[str]:
        command = [self.cli_path, "exec"]
        command += ["resume", "--json"] if resume else ["--json"]
        if yolo_enabled():
            command.append("--dangerously-bypass-approvals-and-sandbox")
        elif not resume:
            command += ["--sandbox", "workspace-write"]
        command.append("--skip-git-repo-check")
        command += [self._session_id or "", "-"] if resume else ["-"]
        return command

    async def query_agent(self, agent: str, user_message: str,
                          timeout_sec: Optional[int] = None) -> str:
        timeout_sec = timeout_sec or QUERY_TIMEOUT_SEC
        prompt = (
            f"[슬랙으로 온 요청. 담당 직원: @{agent}]\n"
            f"먼저 .codex/agents/{agent}.toml을 읽고 그 직원의 정체성과 규칙대로 직접 처리할 것.\n"
            "파일이 없으면 .codex/agents/에서 담당이 가장 가까운 직원을 찾아 처리할 것.\n"
            "workspace/memory/facts.md를 먼저 읽고 자기 inbox 쪽지를 확인한다.\n"
            "산출물은 workspace/결과물/에 저장한다.\n"
            "다른 직원이 이어받아야 하면 workspace/inbox/<상대>/에 쪽지를 남긴다.\n"
            "모르는 금액·날짜·고객사 이름은 지어내지 않는다.\n\n"
            "[답하는 방식 — 지킬 것]\n"
            "- 카톡처럼 한 줄에 한 마디. 각 줄은 '이름: 내용' 형태로 쓴다.\n"
            "- 한 줄 40자 내외, 전체 5줄 이내.\n"
            "- 과정 설명·요약·서론 없이 결론과 사람이 할 일만 쓴다.\n"
            "- 마크다운 강조, 불릿, 제목, 코드블록을 쓰지 않는다.\n\n"
            f"---\n{user_message}"
        )
        async with self._lock:
            try:
                return await self._run(prompt, timeout_sec, bool(self._session_id))
            except Exception as first_error:
                if not self._session_id:
                    raise
                log.warning("Codex 대화 이어받기 실패(%s) — 새 대화로 한 번 더 시도합니다",
                            type(first_error).__name__)
                self.forget_session()
                return await self._run(prompt, RETRY_TIMEOUT_SEC, False)

    async def _run(self, prompt: str, timeout_sec: int, resume: bool) -> str:
        process = await asyncio.create_subprocess_exec(
            *self._command(resume), cwd=str(KIT_ROOT),
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(prompt.encode("utf-8")), timeout=timeout_sec)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

        out = stdout.decode("utf-8", errors="replace")
        err = stderr.decode("utf-8", errors="replace").strip()
        final_messages: list[str] = []
        errors: list[str] = []
        for line in out.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_type = event.get("type")
            if event_type == "thread.started" and event.get("thread_id"):
                self._save_session(str(event["thread_id"]))
            elif event_type == "item.completed":
                item = event.get("item") or {}
                if item.get("type") == "agent_message" and item.get("text"):
                    final_messages.append(str(item["text"]))
            elif event_type in {"error", "turn.failed"}:
                errors.append(str(event.get("message") or event.get("error") or event))

        if process.returncode != 0:
            detail = " / ".join(errors) or err or f"종료코드 {process.returncode}"
            raise CodexError(detail[-2000:])
        result = final_messages[-1].strip() if final_messages else ""
        if not result:
            raise CodexError(err or "Codex가 빈 응답을 반환했습니다")
        return result

    async def close(self) -> None:
        """Codex는 요청마다 프로세스가 끝나므로 종료할 연결이 없다."""


_pool: Optional[AgentPool] = None


def get_pool(workspace: Path, cli_path: str) -> AgentPool:
    global _pool
    if _pool is None:
        _pool = AgentPool(workspace=workspace, cli_path=cli_path)
    return _pool


async def invoke_agent(agent: str, user_message: str, workspace: Path,
                       cli_path: str, timeout_sec: Optional[int] = None) -> str:
    return await get_pool(workspace, cli_path).query_agent(
        agent, user_message, timeout_sec=timeout_sec)
