"""Cancel a scan after a timeout or from another thread."""

import sys
import threading
from dupefinder import DupeFinder, ScanOptions

path = sys.argv[1] if len(sys.argv) > 1 else "."
cancel_flag = threading.Event()

# Cancel after 2 seconds from another thread
timer = threading.Timer(2.0, cancel_flag.set)
timer.start()

finder = DupeFinder(
    options=ScanOptions(),
    should_cancel=cancel_flag.is_set,
)

report = finder.scan(path)
timer.cancel()

if report.cancelled:
    print(f"Scan was cancelled after {report.elapsed_seconds:.2f}s")
    print(
        f"Partial result: {report.scanned_files} files scanned, {report.total_groups} groups found"
    )
else:
    print(f"Scan completed in {report.elapsed_seconds:.2f}s")
    print(f"Found {report.total_groups} duplicate groups")
