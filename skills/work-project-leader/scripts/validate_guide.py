#!/usr/bin/env python3
"""仅用 Python 标准库校验 work-project-leader 生成的项目指南。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


REQUIRED_FILES = (
    "README.md",
    "project-structure.md",
    "data-flow.md",
    "agent_note.md",
)
SNAPSHOT_KEYS = (
    "snapshot_commit",
    "snapshot_branch",
    "snapshot_worktree",
    "generated_at",
    "scope",
    "maintenance",
)
LINK_PATTERN = r"(?<!!)\[[^\]]*\]\(([^)]+)\)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="校验 project_guide 必需文件、快照元数据和本地链接。"
    )
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--guide-dir", default="project_guide")
    return parser.parse_args()


def read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"无法读取 {path}：{exc}")
        return ""


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return values
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def normalize_link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    target = unquote(target)
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith(("#", "mailto:")):
        return None
    return parsed.path or None


def check_links(guide_dir: Path, errors: list[str], warnings: list[str]) -> int:
    checked = 0
    source_links = 0
    for md_file in sorted(guide_dir.glob("*.md")):
        content = read_text(md_file, errors)
        for raw_target in re.findall(LINK_PATTERN, content):
            target = normalize_link_target(raw_target)
            if target is None:
                continue
            checked += 1
            resolved = (md_file.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"{md_file.name} 中的本地链接失效：{raw_target}")
                continue
            try:
                resolved.relative_to(guide_dir.resolve())
            except ValueError:
                source_links += 1
    if source_links == 0:
        warnings.append("没有发现从 project_guide 指向仓库源码或配置的链接")
    return checked


def main() -> int:
    args = parse_args()
    repository_root = args.repository_root.expanduser().resolve()
    guide_dir = (repository_root / args.guide_dir).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not repository_root.is_dir():
        print(f"错误：仓库根目录不是文件夹：{repository_root}")
        return 2
    if not guide_dir.is_dir():
        print(f"错误：指南目录不存在：{guide_dir}")
        return 1

    for name in REQUIRED_FILES:
        if not (guide_dir / name).is_file():
            errors.append(f"缺少必需文件：{args.guide_dir}/{name}")

    readme_path = guide_dir / "README.md"
    readme = read_text(readme_path, errors) if readme_path.is_file() else ""
    for name in ("project-structure.md", "data-flow.md", "agent_note.md"):
        if name not in readme:
            errors.append(f"README.md 未引用 {name}")

    note_path = guide_dir / "agent_note.md"
    note = read_text(note_path, errors) if note_path.is_file() else ""
    metadata = parse_frontmatter(note)
    for key in SNAPSHOT_KEYS:
        if not metadata.get(key):
            errors.append(f"agent_note.md 缺少快照元数据：{key}")
    if metadata.get("maintenance") != "one-shot":
        errors.append("agent_note.md 的 maintenance 必须为 one-shot")
    if metadata.get("snapshot_worktree") not in {
        "clean",
        "dirty",
        "not-a-git-repository",
    }:
        errors.append(
            "agent_note.md 的 snapshot_worktree 必须是 clean、dirty 或 not-a-git-repository"
        )
    if not re.search(r"stale|过期|失效|outdated", note, flags=re.IGNORECASE):
        errors.append("agent_note.md 缺少明确的过期警告")

    checked_links = check_links(guide_dir, errors, warnings)

    for warning in warnings:
        print(f"警告：{warning}")
    for error in errors:
        print(f"错误：{error}")

    if errors:
        print(
            f"失败：{len(errors)} 个错误，{len(warnings)} 个警告，"
            f"已检查 {checked_links} 个本地链接"
        )
        return 1
    print(
        f"通过：{len(REQUIRED_FILES)} 个必需文件，{checked_links} 个本地链接，"
        f"{len(warnings)} 个警告"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
