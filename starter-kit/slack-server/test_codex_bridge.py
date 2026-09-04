"""네트워크·로그인 없이 Codex 슬랙 브리지의 명령과 JSONL 해석을 검사한다."""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import codex_bridge


class FakeProcess:
    returncode = 0

    async def communicate(self, prompt: bytes):
        assert "슬랙 테스트" in prompt.decode("utf-8")
        stdout = (
            b'{"type":"thread.started","thread_id":"thread-123"}\n'
            b'{"type":"item.completed","item":{"type":"agent_message",'
            b'"text":"staff1: \xec\x99\x84\xeb\xa3\x8c"}}\n'
        )
        return stdout, b""


class BridgeTest(unittest.IsolatedAsyncioTestCase):
    async def test_yolo_command_and_jsonl_response(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {"CODEX_YOLO": "1"}, clear=False
        ):
            codex_bridge.SESSION_FILE = Path(temp) / "session.json"
            pool = codex_bridge.AgentPool(Path(temp), "codex.cmd")
            captured = []

            async def fake_create(*command, **kwargs):
                captured.extend(command)
                return FakeProcess()

            with patch.object(asyncio, "create_subprocess_exec", fake_create):
                answer = await pool._run("슬랙 테스트", 10, False)

            self.assertEqual(answer, "staff1: 완료")
            self.assertIn("--dangerously-bypass-approvals-and-sandbox", captured)
            self.assertEqual(pool._session_id, "thread-123")

    def test_resume_command_contains_session(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {"CODEX_YOLO": "1"}, clear=False
        ):
            codex_bridge.SESSION_FILE = Path(temp) / "session.json"
            pool = codex_bridge.AgentPool(Path(temp), "codex.cmd")
            pool._session_id = "thread-456"
            command = pool._command(resume=True)

            self.assertEqual(command[:3], ["codex.cmd", "exec", "resume"])
            self.assertIn("thread-456", command)
            self.assertEqual(command[-1], "-")


if __name__ == "__main__":
    unittest.main()
