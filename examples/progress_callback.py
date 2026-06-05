"""Show scan progress via the event system."""

import sys
from dupefinder import DupeFinder, ScanOptions


def on_event(event) -> None:
    if event.type == "file_discovered":
        print(f"\rDiscovered {event.scanned_files} files...", end="", flush=True)
    elif event.type == "file_hashed":
        print(
            f"\rHashing {event.hashed_files}/{event.total_candidates}...",
            end="",
            flush=True,
        )
    elif event.type == "scan_completed":
        print(f"\nDone in {event.elapsed_seconds:.2f}s")
    elif event.type == "duplicate_group_found":
        print(f"\n  [group] {event.group.count} files × {event.group.size} bytes")


path = sys.argv[1] if len(sys.argv) > 1 else "."

finder = DupeFinder(
    options=ScanOptions(ignore_hidden=True),
    on_event=on_event,
)
report = finder.scan(path)
print(f"\nTotal wasted space: {report.total_wasted_space} bytes")
