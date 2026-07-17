#!/usr/bin/env python3
"""以失败关闭方式运行固定版本的 NVIDIA SkillSpector。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


SKILLSPECTOR_COMMIT = "36cb67d8cc1848c6fbf739861e21b5438deb0a97"
SKILLSPECTOR_REPOSITORY = "https://github.com/NVIDIA/SkillSpector.git"

PATTERNS = [
    ("unsafe-deserialization", "high", re.compile(r"\b(pickle\.loads?|marshal\.loads?|yaml\.load\s*\(|node-serialize|unserialize\s*\()", re.I)),
    ("shell-execution", "high", re.compile(r"\b(os\.system|subprocess\.(run|call|Popen)|child_process\.(exec|spawn)|shell\s*=\s*True)\b", re.I)),
    ("dynamic-code", "high", re.compile(r"\b(eval|exec|compile)\s*\(|__import__\s*\(|importlib\.import_module", re.I)),
    ("credential-access", "high", re.compile(r"(\.ssh|id_rsa|credentials|aws_access_key|api[_-]?key|secret[_-]?key|browser.*cookie|\.env\b)", re.I)),
    ("destructive-command", "critical", re.compile(r"\b(rm\s+-rf|mkfs\b|dd\s+if=|shred\b|git\s+reset\s+--hard)\b", re.I)),
    ("download-execute", "high", re.compile(r"(curl|wget|requests\.get|httpx\.get).{0,240}(bash|sh\b|eval|exec|pip\s+install|uv\s+tool|subprocess)", re.I | re.S)),
    ("encoded-payload", "medium", re.compile(r"(base64\.b64decode|fromhex\s*\(|atob\s*\(|\\x[0-9a-fA-F]{2}.{0,20}\\x[0-9a-fA-F]{2})", re.I)),
    ("approval-bypass", "critical", re.compile(r"(bypass|disable|ignore).{0,80}(approval|security|sandbox|policy|scanner|guardrail)", re.I | re.S)),
    ("prompt-injection", "high", re.compile(r"(ignore|override|disregard).{0,80}(previous|system|developer|instruction|policy)", re.I | re.S)),
]

TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".sh", ".bash", ".zsh", ".js", ".ts", ".tsx",
    ".jsx", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml",
    ".html", ".css", ".rb", ".php", ".ps1", ".bat", ".cmd", ".dockerfile",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(root: Path) -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []
    paths = [root] if root.is_file() or root.is_symlink() else sorted(root.rglob("*"))
    for path in paths:
        relative = path.name if root.is_file() else path.relative_to(root).as_posix()
        if path.is_symlink():
            manifest.append({"path": relative, "type": "symlink", "target": os.readlink(path)})
        elif path.is_file():
            manifest.append(
                {
                    "path": relative,
                    "type": "file",
                    "size": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    return manifest


def supplemental_scan(root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    paths = [root] if root.is_file() else sorted(root.rglob("*"))
    for path in paths:
        relative = path.name if root.is_file() else path.relative_to(root).as_posix()
        if path.is_symlink():
            target = os.readlink(path)
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                findings.append(
                    {"rule": "escaping-symlink", "severity": "critical", "path": relative, "detail": target}
                )
            continue
        if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"Dockerfile", "Makefile", "SKILL.md"}:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            findings.append(
                {"rule": "unreadable-file", "severity": "high", "path": relative, "detail": str(error)}
            )
            continue
        for rule, severity, pattern in PATTERNS:
            match = pattern.search(content)
            if match:
                findings.append(
                    {
                        "rule": rule,
                        "severity": severity,
                        "path": relative,
                        "line": content.count("\n", 0, match.start()) + 1,
                    }
                )
    return findings


def scanner_command() -> tuple[list[str] | None, str]:
    uvx = shutil.which("uvx")
    if uvx:
        source = f"git+{SKILLSPECTOR_REPOSITORY}@{SKILLSPECTOR_COMMIT}"
        return [uvx, "--from", source, "skillspector"], f"pinned-upstream:{SKILLSPECTOR_COMMIT}"
    return None, "scanner-unavailable"


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="运行固定版本的 NVIDIA SkillSpector 静态扫描")
    parser.add_argument("target", help="待扫描的完整 Skill 目录")
    parser.add_argument("--output-dir", required=True, help="扫描报告目录，不能位于 Skill 内部")
    parser.add_argument("--timeout", type=int, default=600, help="扫描超时秒数")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    output = Path(args.output_dir).expanduser().resolve()
    if not target.exists():
        parser.error(f"目标不存在：{target}")
    try:
        output.relative_to(target)
        parser.error("报告目录不能位于待扫描 Skill 内部")
    except ValueError:
        pass
    output.mkdir(parents=True, exist_ok=True)

    write_json(output / "artifact-manifest.json", build_manifest(target))
    supplemental = supplemental_scan(target)
    write_json(output / "supplemental-findings.json", supplemental)

    command, provenance = scanner_command()
    summary: dict[str, object] = {
        "decision": "BLOCK",
        "target": str(target),
        "scanner_executed": False,
        "scanner_provenance": provenance,
        "scanner_pin": SKILLSPECTOR_COMMIT,
        "scanner_mode": "static",
        "supplemental_findings": supplemental,
        "timestamp": int(time.time()),
    }
    if command is None:
        summary["reason"] = "未找到 SkillSpector 或 uvx，按失败关闭策略阻止合并。"
        write_json(output / "gate-summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 2

    report = output / "skillspector-report.json"
    full_command = command + ["scan", str(target), "--format", "json", "--output", str(report), "--no-llm"]
    environment = os.environ.copy()
    environment["PYTHONUNBUFFERED"] = "1"
    try:
        process = subprocess.run(
            full_command,
            env=environment,
            text=True,
            capture_output=True,
            timeout=args.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        summary["reason"] = "SkillSpector 扫描超时，按失败关闭策略阻止合并。"
        write_json(output / "gate-summary.json", summary)
        return 3

    summary["scanner_executed"] = True
    summary["scanner_exit_code"] = process.returncode
    summary["scanner_stderr_tail"] = process.stderr[-2000:]
    if process.returncode != 0 or not report.is_file():
        summary["reason"] = "SkillSpector 执行失败或未生成报告。"
        write_json(output / "gate-summary.json", summary)
        return 4

    try:
        payload = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        summary["reason"] = f"SkillSpector 报告无法解析：{error}"
        write_json(output / "gate-summary.json", summary)
        return 5

    if not isinstance(payload, dict):
        summary["reason"] = "SkillSpector 报告不是预期的 JSON 对象。"
        write_json(output / "gate-summary.json", summary)
        return 5

    risk = payload.get("risk_assessment")
    completeness = payload.get("analysis_completeness")
    issues = payload.get("issues")
    suppressed = payload.get("suppressed")
    metadata = payload.get("metadata")
    if (
        not isinstance(risk, dict)
        or not isinstance(completeness, dict)
        or not isinstance(issues, list)
        or not isinstance(metadata, dict)
    ):
        summary["reason"] = "SkillSpector 报告缺少风险、覆盖率或问题列表。"
        write_json(output / "gate-summary.json", summary)
        return 5

    severity = str(risk.get("severity") or "").lower()
    score = risk.get("score")
    total_components = completeness.get("total_components")
    scanned_components = completeness.get("scanned_components")
    coverage = completeness.get("coverage_percent")
    limitations = completeness.get("limitations")
    allowed_limitations = {"LLM meta-analysis was disabled (--no-llm)"}
    unexpected_limitations = (
        [item for item in limitations if item not in allowed_limitations]
        if isinstance(limitations, list)
        else ["limitations 字段缺失或格式错误"]
    )
    malformed_issues = [
        item
        for item in issues
        if not isinstance(item, dict) or not str(item.get("severity") or "").strip()
    ]
    summary["skillspector_version"] = metadata.get("skillspector_version") if isinstance(metadata, dict) else None
    summary["skillspector_risk_severity"] = severity.upper() or None
    summary["skillspector_risk_score"] = score
    summary["coverage_percent"] = coverage
    summary["issues"] = issues
    summary["suppressed"] = suppressed
    summary["unexpected_limitations"] = unexpected_limitations

    report_incomplete = (
        severity not in {"low", "medium", "high", "critical"}
        or not isinstance(score, (int, float))
        or coverage != 100
        or total_components != scanned_components
        or not isinstance(suppressed, list)
        or bool(suppressed)
        or payload.get("suppressed_count") != 0
        or not summary["skillspector_version"]
        or metadata.get("llm_requested") is not False
        or bool(malformed_issues)
        or bool(unexpected_limitations)
    )
    if report_incomplete:
        summary["reason"] = "扫描覆盖不完整、存在抑制项、异常限制或必需字段缺失。"
        write_json(output / "gate-summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 5

    blocking = [item for item in supplemental if item.get("severity") in {"critical", "high"}]
    blocking_issues = [
        item
        for item in issues
        if isinstance(item, dict) and str(item.get("severity") or "").lower() in {"critical", "high"}
    ]
    if severity in {"critical", "high"} or blocking or blocking_issues:
        summary["reason"] = "发现 critical/high 风险，修复前阻止合并。"
        write_json(output / "gate-summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 6

    summary["decision"] = "MANUAL_REVIEW_REQUIRED"
    summary["reason"] = "自动扫描完成；合并前仍须完成人工行为与来源审查。"
    write_json(output / "gate-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
