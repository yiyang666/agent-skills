#!/usr/bin/env python3
"""Diagnose and repair incompatible hidden reasoning items in Codex rollouts."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


THREAD_ID_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
PLACEHOLDER_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-[0-9]+"
UUID_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
VISIBLE_TYPES = {
    "message",
    "function_call",
    "function_call_output",
    "custom_tool_call",
    "custom_tool_call_output",
}


class RecoveryError(RuntimeError):
    pass


def codex_home(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser().resolve() if configured else Path.home() / ".codex"


def rollout_thread_id(path: Path) -> str | None:
    matches = re.findall(THREAD_ID_PATTERN, path.name)
    return matches[-1] if matches else None


def candidate_files(home: Path) -> list[Path]:
    roots = [home / "sessions", home / "archived_sessions"]
    result: list[Path] = []
    for root in roots:
        if root.is_dir():
            result.extend(p for p in root.rglob("*.jsonl") if ".backup-" not in p.name)
    return sorted(set(result))


def resolve_session(args: argparse.Namespace) -> Path:
    if args.session_file:
        path = Path(args.session_file).expanduser().resolve()
        if not path.is_file():
            raise RecoveryError(f"会话文件不存在：{path}")
        return path

    home = codex_home(args.codex_home)
    matches = [p for p in candidate_files(home) if rollout_thread_id(p) == args.thread_id]
    if not matches:
        raise RecoveryError(f"未找到 thread ID：{args.thread_id}")
    if len(matches) != 1:
        joined = "\n".join(f"  - {p}" for p in matches)
        raise RecoveryError(f"thread ID 对应多个文件，请改用 --session-file：\n{joined}")
    return matches[0]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    raise RecoveryError(f"第 {line_number} 行为空，拒绝修复")
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise RecoveryError(f"JSONL 第 {line_number} 行解析失败：{exc.msg}") from exc
                if not isinstance(value, dict):
                    raise RecoveryError(f"第 {line_number} 行不是 JSON 对象")
                rows.append(value)
    except OSError as exc:
        raise RecoveryError(f"无法读取会话：{exc}") from exc
    return rows


def incompatible_reasoning(value: Any) -> bool:
    if not isinstance(value, dict) or value.get("type") != "reasoning":
        return False
    content = value.get("content")
    if isinstance(content, list) and len(content) > 0:
        return True
    item_id = value.get("id")
    encrypted = value.get("encrypted_content")
    return bool(
        isinstance(item_id, str)
        and re.fullmatch(UUID_PATTERN, item_id)
        and isinstance(encrypted, str)
        and re.fullmatch(PLACEHOLDER_PATTERN, encrypted)
    )


def removable_node(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("type") == "response_item":
        return incompatible_reasoning(value.get("payload"))
    return incompatible_reasoning(value)


def count_incompatible(value: Any) -> int:
    if removable_node(value):
        return 1
    if isinstance(value, dict):
        return sum(count_incompatible(child) for child in value.values())
    if isinstance(value, list):
        return sum(count_incompatible(child) for child in value)
    return 0


def clean_nested(value: Any) -> tuple[Any, int]:
    if isinstance(value, list):
        cleaned: list[Any] = []
        removed = 0
        for child in value:
            if removable_node(child):
                removed += 1
                continue
            new_child, child_removed = clean_nested(child)
            cleaned.append(new_child)
            removed += child_removed
        return cleaned, removed
    if isinstance(value, dict):
        cleaned_dict: dict[str, Any] = {}
        removed = 0
        for key, child in value.items():
            if removable_node(child):
                raise RecoveryError(f"发现位于对象字段 {key!r} 的未知推理结构，拒绝自动修复")
            new_child, child_removed = clean_nested(child)
            cleaned_dict[key] = new_child
            removed += child_removed
        return cleaned_dict, removed
    return value, 0


def clean_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    cleaned: list[dict[str, Any]] = []
    removed = 0
    for row in rows:
        if removable_node(row):
            removed += 1
            continue
        new_row, nested_removed = clean_nested(row)
        cleaned.append(new_row)
        removed += nested_removed
    return cleaned, removed


def visible_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    result: Counter[str] = Counter()
    for row in rows:
        if row.get("type") != "response_item":
            continue
        item_type = row.get("payload", {}).get("type")
        if item_type in VISIBLE_TYPES:
            result[item_type] += 1
    return result


def report(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    mode = stat.S_IMODE(path.stat().st_mode)
    return {
        "thread_id": rollout_thread_id(path),
        "session_file": str(path),
        "records": len(rows),
        "incompatible_reasoning": sum(count_incompatible(row) for row in rows),
        "visible_counts": dict(sorted(visible_counts(rows).items())),
        "permissions": f"{mode:04o}",
    }


def unique_backup_path(path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = path.with_name(f"{path.name}.backup-codex-session-recovery-{stamp}")
    candidate = base
    index = 1
    while candidate.exists():
        candidate = path.with_name(f"{base.name}-{index}")
        index += 1
    return candidate


def atomic_repair(path: Path, rows: list[dict[str, Any]]) -> tuple[Path, int]:
    before_counts = visible_counts(rows)
    cleaned, removed = clean_rows(rows)
    if removed == 0:
        raise RecoveryError("没有可修复的非兼容推理项，未写入")
    if visible_counts(cleaned) != before_counts:
        raise RecoveryError("可见历史计数发生变化，拒绝写入")
    if any(count_incompatible(row) for row in cleaned):
        raise RecoveryError("清理后仍存在非兼容推理项，拒绝写入")

    backup = unique_backup_path(path)
    original_mode = stat.S_IMODE(path.stat().st_mode)
    shutil.copy2(path, backup)
    os.chmod(backup, 0o600)

    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.recovery-",
            delete=False,
        ) as stream:
            temp_name = stream.name
            for row in cleaned:
                stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temp_path = Path(temp_name)
        os.chmod(temp_path, original_mode)
        verification = load_jsonl(temp_path)
        if len(verification) != len(cleaned) or any(count_incompatible(row) for row in verification):
            raise RecoveryError("临时文件验证失败，原文件未替换")
        os.replace(temp_path, path)
        temp_name = None
        os.chmod(path, 0o600)
    except Exception:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)
        raise
    return backup, removed


def print_report(value: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
        return
    for key, item in value.items():
        if isinstance(item, dict):
            print(f"{key}:")
            for nested_key, nested_value in item.items():
                print(f"  {nested_key}: {nested_value}")
        else:
            print(f"{key}: {item}")


def command_find(args: argparse.Namespace) -> int:
    home = codex_home(args.codex_home)
    results = []
    needle = args.error_text.encode("utf-8")
    for path in candidate_files(home):
        try:
            occurrences = path.read_bytes().count(needle)
        except OSError:
            continue
        if occurrences:
            results.append(
                {
                    "thread_id": rollout_thread_id(path),
                    "session_file": str(path),
                    "occurrences": occurrences,
                    "modified_ns": path.stat().st_mtime_ns,
                }
            )
    results.sort(key=lambda item: item["modified_ns"], reverse=True)
    for item in results:
        item.pop("modified_ns", None)
    print_report({"matches": len(results), "sessions": {str(i + 1): v for i, v in enumerate(results)}}, args.json)
    return 0 if results else 1


def command_inspect(args: argparse.Namespace) -> int:
    path = resolve_session(args)
    rows = load_jsonl(path)
    value = report(path, rows)
    print_report(value, args.json)
    return 0


def command_repair(args: argparse.Namespace) -> int:
    if not args.apply:
        raise RecoveryError("repair 必须显式增加 --apply")
    path = resolve_session(args)
    target_id = rollout_thread_id(path)
    active_id = os.environ.get("CODEX_THREAD_ID")
    if target_id and active_id == target_id and not args.allow_active:
        raise RecoveryError("目标是当前活动会话；请从独立恢复会话操作，或先完全退出 Codex")
    rows = load_jsonl(path)
    before = report(path, rows)
    backup, removed = atomic_repair(path, rows)
    after_rows = load_jsonl(path)
    after = report(path, after_rows)
    value = {
        "status": "repaired",
        "removed_reasoning": removed,
        "backup_file": str(backup),
        "before": before,
        "after": after,
        "restart_required": True,
    }
    print_report(value, args.json)
    return 0


def add_target_arguments(parser: argparse.ArgumentParser) -> None:
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--thread-id")
    target.add_argument("--session-file")
    parser.add_argument("--codex-home")
    parser.add_argument("--json", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    find_parser = subparsers.add_parser("find", help="按错误文本定位会话")
    find_parser.add_argument("--error-text", default="array_above_max_length")
    find_parser.add_argument("--codex-home")
    find_parser.add_argument("--json", action="store_true")
    find_parser.set_defaults(handler=command_find)

    inspect_parser = subparsers.add_parser("inspect", help="只读检查会话")
    add_target_arguments(inspect_parser)
    inspect_parser.set_defaults(handler=command_inspect)

    repair_parser = subparsers.add_parser("repair", help="备份并修复会话")
    add_target_arguments(repair_parser)
    repair_parser.add_argument("--apply", action="store_true")
    repair_parser.add_argument("--allow-active", action="store_true", help=argparse.SUPPRESS)
    repair_parser.set_defaults(handler=command_repair)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except RecoveryError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
