#!/usr/bin/env python3
"""验证仓库中所有 Skill 的基础结构、命名和中文说明。"""

from __future__ import annotations

import re
import sys
from pathlib import Path


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CHINESE_PATTERN = re.compile(r"[\u3400-\u9fff]")


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("缺少起始 frontmatter 分隔符")
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("缺少结束 frontmatter 分隔符") from exc

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"无法解析 frontmatter：{line}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"\'')
    return fields, "\n".join(lines[end + 1 :])


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return ["缺少 SKILL.md"]

    if not NAME_PATTERN.fullmatch(skill_dir.name):
        errors.append("目录名必须使用小写字母、数字和连字符")

    try:
        fields, body = parse_frontmatter(skill_file)
    except (OSError, UnicodeError, ValueError) as exc:
        return [str(exc)]

    if set(fields) != {"name", "description"}:
        errors.append("frontmatter 只能包含 name 和 description")
    if fields.get("name") != skill_dir.name:
        errors.append("frontmatter name 必须与目录名一致")
    if not fields.get("description"):
        errors.append("description 不能为空")
    if not CHINESE_PATTERN.search(fields.get("description", "")):
        errors.append("description 必须包含中文说明")
    if not CHINESE_PATTERN.search(body):
        errors.append("SKILL.md 正文必须包含中文说明")
    if re.search(r"\bTODO\b|\[TODO", skill_file.read_text(encoding="utf-8"), re.IGNORECASE):
        errors.append("SKILL.md 仍包含 TODO 占位符")

    for script in skill_dir.glob("scripts/*.py"):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except (SyntaxError, UnicodeError) as exc:
            errors.append(f"{script.relative_to(skill_dir)} 语法错误：{exc}")
    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    skills_dir = repo_root / "skills"
    skill_dirs = sorted(path for path in skills_dir.iterdir() if path.is_dir())
    if not skill_dirs:
        print("未找到任何 Skill。", file=sys.stderr)
        return 1

    failed = False
    for skill_dir in skill_dirs:
        errors = validate_skill(skill_dir)
        if errors:
            failed = True
            print(f"[失败] {skill_dir.name}", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
        else:
            print(f"[通过] {skill_dir.name}")

    if failed:
        return 1
    print(f"仓库检查通过，共 {len(skill_dirs)} 个 Skill。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
