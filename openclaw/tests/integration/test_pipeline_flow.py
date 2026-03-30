from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from openclaw.scripts import memcli


class MemcliCommandFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.memory_path = self.base / "Memory"
        self.run_dir = self.memory_path / "run"
        self.run_dir.mkdir(parents=True)
        # Seed buffer + manual edit files that upstream pipeline steps would produce
        self.buffer_file = self.run_dir / "buffer-content.txt"
        self.manual_file = self.run_dir / "manual-edits.txt"
        self.buffer_file.write_text("Daily reflection", encoding="utf-8")
        self.manual_file.write_text("Manual edit", encoding="utf-8")

        for filename in ["insights.md", "goals.md", "tasks.md", "hot-memory.md"]:
            (self.memory_path / filename).write_text(f"Existing {filename}", encoding="utf-8")

        self.task_inbox_file = self.run_dir / "task-inbox.json"
        task_inbox = {"tasks": [{"title": "Task"}], "completed": [], "open_count": 1}
        self.task_inbox_file.write_text(json.dumps(task_inbox), encoding="utf-8")

        self.env_patch = mock.patch.dict(
            os.environ,
            {"OPENCLAW_URL": "http://gateway.local", "OPENCLAW_TOKEN": "test-token"},
            clear=False,
        )
        self.env_patch.start()

    def tearDown(self) -> None:
        self.env_patch.stop()
        self._tmp.cleanup()

    def run_command(self, args: list[str]) -> str:
        argv = ["memcli.py"] + args
        buf = io.StringIO()
        with mock.patch.object(sys, "argv", argv):
            with contextlib.redirect_stdout(buf):
                memcli.main()
        return buf.getvalue().strip()

    @staticmethod
    def _detect_job(input_payload: dict) -> str:
        if "raw_patterns" in input_payload:
            return "insights"
        if "task_inbox" in input_payload and "raw_goals" in input_payload:
            return "goals"
        if "task_inbox" in input_payload:
            return "tasks"
        return "hot_memory"

    @mock.patch("openclaw.scripts.gateway_client.post_json")
    def test_run_extraction_then_parallel_memory(self, mock_post_json):
        extraction_output = {
            "raw_insights": [{"summary": "insight"}],
            "raw_goals": [{"title": "goal"}],
            "raw_tasks": [{"title": "task"}],
            "raw_patterns": [{"pattern": "pattern"}],
            "classifiers": ["project:personal"],
        }

        captured_payloads: list[dict] = []

        def fake_gateway(url: str, payload: dict, token: str, timeout: int):
            captured_payloads.append(payload)
            if len(captured_payloads) == 1:
                return {
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(extraction_output)}
                        ]
                    }
                }

            job_name = self._detect_job(payload["args"]["input"])
            return {
                "result": {
                    "details": {
                        "json": {"content": f"{job_name}-content"}
                    }
                }
            }

        mock_post_json.side_effect = fake_gateway

        extraction_stdout = self.run_command(
            [
                "run-extraction",
                "--buffer-content-file",
                str(self.buffer_file),
                "--manual-edits-file",
                str(self.manual_file),
                "--agent",
                "memspren-heavy",
                "--memory-path",
                str(self.memory_path),
            ]
        )
        self.assertEqual(json.loads(extraction_stdout), extraction_output)

        extraction_file = self.run_dir / "extraction-output.json"
        self.assertTrue(extraction_file.exists())

        parallel_stdout = self.run_command(
            [
                "parallel-memory",
                "--extraction-file",
                str(extraction_file),
                "--task-inbox-file",
                str(self.task_inbox_file),
                "--memory-path",
                str(self.memory_path),
            ]
        )
        parallel_result = json.loads(parallel_stdout)

        for job in ["insights", "goals", "tasks", "hot_memory"]:
            self.assertTrue(parallel_result[job]["ok"], f"{job} should be ok")
            self.assertEqual(parallel_result[job]["content"], f"{job}-content")

        # 1 extraction call + 4 parallel jobs
        self.assertEqual(len(captured_payloads), 5)
        insights_payload = next(
            payload
            for payload in captured_payloads[1:]
            if "raw_insights" in payload["args"]["input"]
        )
        self.assertEqual(
            insights_payload["args"]["input"]["raw_insights"],
            extraction_output["raw_insights"],
        )
