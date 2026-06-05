"""Simulate a FastAPI-like endpoint that scans an upload directory."""

from __future__ import annotations

from pathlib import Path

from dupefinder import DupeFinder, ScanOptions


def scan_uploads(upload_dir: str, min_size_kb: int = 0) -> dict:
    """Simulate a POST /scan endpoint."""
    finder = DupeFinder(
        options=ScanOptions(min_size=min_size_kb * 1024),
    )
    report = finder.scan(upload_dir)
    return {
        "status": "ok",
        "duplicates_found": report.has_duplicates,
        "total_groups": report.total_groups,
        "wasted_space_bytes": report.total_wasted_space,
        "groups": [{"files": [str(p) for p in g.files], "size": g.size} for g in report.groups],
    }


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("duplicate content")
        (root / "b.txt").write_text("duplicate content")
        (root / "c.txt").write_text("unique")

        result = scan_uploads(tmp)
        print(result)
