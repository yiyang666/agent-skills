#!/usr/bin/env python3
"""Representative success and refusal tests for recover_session.py."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import recover_session


THREAD_ID = "11111111-2222-3333-4444-555555555555"


def record(payload: dict) -> dict:
    return {"timestamp": "2026-01-01T00:00:00Z", "type": "response_item", "payload": payload}


def write_fixture(path: Path) -> None:
    rows = [
        record({"type": "message", "role": "user", "content": [{"type": "input_text", "text": "hello"}]}),
        record({"type": "reasoning", "id": "rs_official", "summary": [], "encrypted_content": "gAAAA-safe"}),
        record(
            {
                "type": "reasoning",
                "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "summary": [],
                "content": [{"type": "reasoning_text", "text": "hidden"}],
                "encrypted_content": "ffffffff-1111-2222-3333-444444444444-0",
            }
        ),
        record({"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "hi"}]}),
        record(
            {
                "type": "reasoning",
                "id": "12345678-1234-1234-1234-123456789abc",
                "summary": [],
                "encrypted_content": "abcdefab-cdef-cdef-cdef-abcdefabcdef-0",
            }
        ),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class RecoveryTests(unittest.TestCase):
    def run_cli(self, *args: str, active: bool = False) -> SimpleNamespace:
        stdout = io.StringIO()
        stderr = io.StringIO()
        active_id = THREAD_ID if active else "99999999-8888-7777-6666-555555555555"
        with (
            patch.object(sys, "argv", ["recover_session.py", *args]),
            patch.dict(os.environ, {"CODEX_THREAD_ID": active_id}),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            returncode = recover_session.main()
        return SimpleNamespace(returncode=returncode, stdout=stdout.getvalue(), stderr=stderr.getvalue())

    def test_inspect_and_repair_preserve_visible_messages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"rollout-2026-01-01T00-00-00-{THREAD_ID}.jsonl"
            write_fixture(path)
            inspect = self.run_cli("inspect", "--session-file", os.fspath(path), "--json")
            self.assertEqual(inspect.returncode, 0, inspect.stderr)
            self.assertEqual(json.loads(inspect.stdout)["incompatible_reasoning"], 2)

            repaired = self.run_cli("repair", "--session-file", os.fspath(path), "--apply", "--json")
            self.assertEqual(repaired.returncode, 0, repaired.stderr)
            result = json.loads(repaired.stdout)
            self.assertEqual(result["removed_reasoning"], 2)
            self.assertEqual(result["before"]["visible_counts"], result["after"]["visible_counts"])
            self.assertEqual(result["after"]["incompatible_reasoning"], 0)
            self.assertTrue(Path(result["backup_file"]).is_file())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(Path(result["backup_file"]).stat().st_mode & 0o777, 0o600)
            clean = self.run_cli("inspect", "--session-file", os.fspath(path), "--json")
            self.assertEqual(clean.returncode, 0, clean.stderr)
            self.assertEqual(json.loads(clean.stdout)["incompatible_reasoning"], 0)

    def test_refuses_active_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"rollout-2026-01-01T00-00-00-{THREAD_ID}.jsonl"
            write_fixture(path)
            before = path.read_bytes()
            result = self.run_cli("repair", "--session-file", os.fspath(path), "--apply", active=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("当前活动会话", result.stderr)
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse(list(path.parent.glob("*.backup-*")))

    def test_repair_requires_apply(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"rollout-2026-01-01T00-00-00-{THREAD_ID}.jsonl"
            write_fixture(path)
            result = self.run_cli("repair", "--session-file", os.fspath(path))
            self.assertEqual(result.returncode, 2)
            self.assertIn("--apply", result.stderr)

    def test_invalid_json_never_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"rollout-2026-01-01T00-00-00-{THREAD_ID}.jsonl"
            path.write_text("{not-json}\n", encoding="utf-8")
            before = path.read_bytes()
            result = self.run_cli("repair", "--session-file", os.fspath(path), "--apply")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
