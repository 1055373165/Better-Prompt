"""Code writer — write generated code to disk and sync state files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.tools.file_manager import write_file, read_file

logger = logging.getLogger(__name__)


def write_code_changes(project_dir: Path, file_changes: list[dict[str, str]]) -> list[str]:
    """Write a list of file changes to disk.

    Each change dict has: {"path": "<relative_path>", "content": "<file content>"}
    Returns list of written file paths.
    """
    written = []
    for change in file_changes:
        rel_path = change["path"]
        content = change["content"]
        write_file(project_dir, rel_path, content)
        written.append(rel_path)
    logger.info(f"[CodeWriter] Wrote {len(written)} files to {project_dir}")
    return written


def sync_progress_md(project_dir: Path, progress_data: dict[str, Any]) -> None:
    """Generate and write PROGRESS.md from structured progress data."""
    lines = ["# 项目进度", ""]
    lines += ["## 项目信息", ""]
    for key in ("项目名称", "一句话目标", "创建时间", "最后更新", "协议版本"):
        lines.append(f"- {key}：{progress_data.get(key, '')}")
    lines += ["", "## 全局指标", ""]
    for key in ("总阶段数", "总 MDU 数", "已完成 MDU", "整体完成度", "最大拆解深度"):
        lines.append(f"- {key}：{progress_data.get(key, '')}")

    lines += ["", "## 阶段总览", ""]
    lines.append("| 阶段 | 状态 | MDU 数 | 已完成 | 完成度 |")
    lines.append("|------|------|--------|--------|--------|")
    for phase in progress_data.get("phases", []):
        lines.append(
            f"| {phase['name']} | {phase['status']} | "
            f"{phase['mdu_count']} | {phase['completed']} | {phase['percent']}% |"
        )

    lines += ["", "## 当前位置", ""]
    pos = progress_data.get("current_position", {})
    lines.append(f"- 当前阶段：{pos.get('phase', '')}")
    lines.append(f"- 当前批次：{pos.get('batch', '')}")
    lines.append(f"- 当前 MDU：{pos.get('mdu', '')}")
    lines.append(f"- 整体完成度：{pos.get('percent', '0')}%")

    lines += ["", "## 变更记录", ""]
    lines.append("| 时间 | 类型 | 描述 | 影响范围 |")
    lines.append("|------|------|------|----------|")
    for log in progress_data.get("change_logs", []):
        lines.append(
            f"| {log['time']} | {log['type']} | {log['description']} | {log['scope']} |"
        )

    lines.append("")
    content = "\n".join(lines)
    write_file(project_dir, "PROGRESS.md", content)
    logger.info("[CodeWriter] Synced PROGRESS.md")


def sync_decisions_md(project_dir: Path, decisions: list[dict[str, Any]]) -> None:
    """Generate and write DECISIONS.md from structured decision data."""
    lines = ["# 架构决策记录", ""]

    for d in decisions:
        adr_num = d.get("adr_number", "?")
        title = d.get("title", "Untitled")
        status = d.get("status", "decided")
        content = d.get("content", {})

        lines.append(f"## ADR-{adr_num:03d}：{title}")
        lines.append("")
        lines.append(f"- 状态：{status}")
        lines.append(f"- 日期：{d.get('date', '')}")
        lines.append(f"- 背景：{content.get('background', '')}")

        candidates = content.get("candidates", [])
        if candidates:
            lines.append("- 候选方案：")
            for c in candidates:
                lines.append(f"  - {c}")

        lines.append(f"- 最终决定：{content.get('decision', '')}")
        lines.append(f"- 代价与妥协：{content.get('tradeoffs', '')}")
        lines.append(f"- 推翻条件：{content.get('overturn_conditions', '')}")
        lines.append(f"- 影响范围：{d.get('impact_scope', '')}")

        spike = d.get("spike_result", None)
        spike_str = "不适用" if spike is None else ("已通过" if spike == "passed" else "未通过")
        lines.append(f"- 探针验证：{spike_str}")
        lines.append("")

    content = "\n".join(lines)
    write_file(project_dir, "DECISIONS.md", content)
    logger.info("[CodeWriter] Synced DECISIONS.md")
