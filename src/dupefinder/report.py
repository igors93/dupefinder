"""Report formatting helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dupefinder.constants import SCHEMA_VERSION
from dupefinder.models import DuplicateGroup, ScanIssue, ScanReport


def bytes_to_human(size: int) -> str:
    """Convert a byte count into a readable string."""

    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units[:-1]:
        if value < 1000:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1000
    return f"{value:.2f} {units[-1]}"


def group_to_dict(group: DuplicateGroup) -> dict[str, Any]:
    return {
        "digest": group.digest,
        "size": group.size,
        "count": group.count,
        "wasted_space": group.wasted_space,
        "files": [str(path) for path in group.files],
    }


def issue_to_dict(issue: ScanIssue) -> dict[str, Any]:
    return {
        "path": str(issue.path),
        "message": issue.message,
        "phase": issue.phase,
    }


def report_to_dict(report: ScanReport) -> dict[str, Any]:
    """Convert a ScanReport into plain Python objects."""

    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(report.root),
        "scanned_files": report.scanned_files,
        "hashed_files": report.hashed_files,
        "total_groups": report.total_groups,
        "total_duplicate_files": report.total_duplicate_files,
        "total_wasted_space": report.total_wasted_space,
        "cancelled": report.cancelled,
        "elapsed_seconds": report.elapsed_seconds,
        "total_bytes_read": report.total_bytes_read,
        "groups": [group_to_dict(group) for group in report.groups],
        "issues": [issue_to_dict(issue) for issue in report.issues],
    }


def report_to_json(report: ScanReport, *, indent: int | None = 2) -> str:
    """Serialize a ScanReport as JSON."""

    return json.dumps(report_to_dict(report), indent=indent, ensure_ascii=False)


def format_report(report: ScanReport) -> str:
    """Return a human-readable text report."""

    lines = [
        f"dupefinder report for: {report.root}",
        f"Scanned files: {report.scanned_files}",
        f"Hashed files: {report.hashed_files}",
        f"Duplicate groups: {report.total_groups}",
        f"Duplicate files: {report.total_duplicate_files}",
        f"Potential wasted space: {bytes_to_human(report.total_wasted_space)}",
    ]
    if report.elapsed_seconds is not None:
        lines.append(f"Elapsed: {report.elapsed_seconds:.2f}s")
    if report.cancelled:
        lines.append("Status: CANCELLED (partial results)")

    if not report.groups:
        lines.append("")
        lines.append("No duplicates found.")
    else:
        for index, group in enumerate(report.groups, start=1):
            lines.append("")
            lines.append(f"Group {index}: {group.count} files, {bytes_to_human(group.size)} each")
            lines.append(f"Hash: {group.digest}")
            for path in group.files:
                lines.append(f"  - {path}")

    if report.issues:
        lines.append("")
        lines.append("Issues:")
        for issue in report.issues:
            lines.append(f"  - [{issue.phase}] {issue.path}: {issue.message}")

    return "\n".join(lines)
