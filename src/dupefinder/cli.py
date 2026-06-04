"""Command line interface for dupefinder."""

from __future__ import annotations

import argparse
import re
import sys
from typing import Iterable

from dupefinder import __version__
from dupefinder.api import scan
from dupefinder.constants import DEFAULT_CHUNK_SIZE, DEFAULT_HASH_ALGORITHM, SIZE_UNITS
from dupefinder.models import ScanOptions
from dupefinder.report import format_report, report_to_json
from dupefinder.safety import normalize_extensions

_SIZE_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([a-zA-Z]*)\s*$")


def parse_size(value: str) -> int:
    """Parse values like '1024', '10MB', '5MiB', or '1GB'."""

    match = _SIZE_PATTERN.match(value)
    if not match:
        raise argparse.ArgumentTypeError(f"Invalid size: {value!r}")

    number_text, unit_text = match.groups()
    unit = (unit_text or "bytes").lower()
    if unit not in SIZE_UNITS:
        valid = ", ".join(sorted(SIZE_UNITS))
        raise argparse.ArgumentTypeError(f"Invalid size unit {unit!r}. Valid units: {valid}")

    return int(float(number_text) * SIZE_UNITS[unit])


def split_extensions(value: str | None) -> frozenset[str] | None:
    if value is None:
        return None
    items = [part.strip() for part in value.split(",") if part.strip()]
    return normalize_extensions(items)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dupefinder",
        description="Find duplicate files safely using file hashes.",
    )
    parser.add_argument("path", help="File or directory to scan.")
    parser.add_argument("--algorithm", default=DEFAULT_HASH_ALGORITHM, help="Hash algorithm. Default: sha256.")
    parser.add_argument("--chunk-size", type=parse_size, default=DEFAULT_CHUNK_SIZE, help="Read chunk size. Example: 1MB.")
    parser.add_argument("--min-size", type=parse_size, default=1, help="Ignore files smaller than this. Example: 10KB.")
    parser.add_argument("--max-size", type=parse_size, default=None, help="Ignore files larger than this. Example: 5GB.")
    parser.add_argument("--include-ext", default=None, help="Only scan these extensions. Example: .jpg,.png")
    parser.add_argument("--ignore-ext", default=None, help="Ignore these extensions. Example: .tmp,.log")
    parser.add_argument("--no-ignore-hidden", action="store_true", help="Do not ignore hidden dotfiles and dotfolders.")
    parser.add_argument("--follow-symlinks", action="store_true", help="Follow symbolic links. Disabled by default.")
    parser.add_argument("--strict", action="store_true", help="Raise errors instead of recording and skipping them.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--fail-on-duplicates", action="store_true", help="Exit with code 2 when duplicates are found.")
    parser.add_argument("--version", action="version", version=f"dupefinder {__version__}")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    options = ScanOptions(
        algorithm=args.algorithm,
        chunk_size=args.chunk_size,
        min_size=args.min_size,
        max_size=args.max_size,
        ignore_hidden=not args.no_ignore_hidden,
        follow_symlinks=args.follow_symlinks,
        ignored_extensions=split_extensions(args.ignore_ext) or frozenset(),
        include_extensions=split_extensions(args.include_ext),
        on_error="raise" if args.strict else "skip",
    )

    try:
        report = scan(args.path, options=options)
    except Exception as exc:  # CLI should turn exceptions into clear messages.
        print(f"dupefinder error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(report_to_json(report))
    else:
        print(format_report(report))

    if args.fail_on_duplicates and report.has_duplicates:
        return 2
    return 0
