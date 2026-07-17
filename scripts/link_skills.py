#!/usr/bin/env python3
"""将仓库中的 Skills 安全链接到指定 Agent 的用户目录。"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def target_dir(target: str) -> Path:
    home = Path.home()
    if target == "cursor":
        return home / ".cursor" / "skills"
    if target == "agents":
        return home / ".agents" / "skills"
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex"))
    return codex_home / "skills"


def available_skills(skills_dir: Path) -> dict[str, Path]:
    return {
        path.name: path.resolve()
        for path in sorted(skills_dir.iterdir())
        if path.is_dir() and (path / "SKILL.md").is_file()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="把仓库 Skills 链接到 Cursor、通用 Agent 或 Codex")
    parser.add_argument("skills", nargs="*", help="要链接的 Skill 名称；省略时处理全部")
    parser.add_argument("--target", required=True, choices=("cursor", "agents", "codex"), help="目标 Agent")
    parser.add_argument("--dry-run", action="store_true", help="只显示计划，不创建目录或链接")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    skills_dir = repo_root / "skills"
    available = available_skills(skills_dir)
    selected = args.skills or list(available)

    unknown = [name for name in selected if name not in available]
    if unknown:
        print(f"不存在的 Skill：{', '.join(unknown)}", file=sys.stderr)
        print(f"可用 Skill：{', '.join(available)}", file=sys.stderr)
        return 2

    destination_root = target_dir(args.target).expanduser()
    if not args.dry_run:
        destination_root.mkdir(parents=True, exist_ok=True)

    failed = False
    for name in selected:
        source = available[name]
        destination = destination_root / name
        if destination.is_symlink():
            try:
                if destination.resolve(strict=True) == source:
                    print(f"已存在：{destination} -> {source}")
                    continue
            except FileNotFoundError:
                pass
            print(f"冲突：{destination} 是指向其他位置或已失效的软链接，未修改。", file=sys.stderr)
            failed = True
            continue
        if destination.exists():
            print(f"冲突：{destination} 已存在且不是本仓库链接，未修改。", file=sys.stderr)
            failed = True
            continue

        print(f"{'计划链接' if args.dry_run else '创建链接'}：{destination} -> {source}")
        if not args.dry_run:
            destination.symlink_to(source, target_is_directory=True)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
