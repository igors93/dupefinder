"""Use the SQLite hash cache to speed up repeated scans."""

import sys
import time
from dupefinder import DupeFinder, ScanOptions
from dupefinder.cache import SQLiteHashCache

path = sys.argv[1] if len(sys.argv) > 1 else "."

with SQLiteHashCache(".dupefinder-cache.sqlite") as cache:
    finder = DupeFinder(options=ScanOptions(), cache=cache)

    start = time.monotonic()
    report = finder.scan(path)
    elapsed_first = time.monotonic() - start
    print(f"First scan: {report.scanned_files} files, {elapsed_first:.2f}s")

    start = time.monotonic()
    report2 = finder.scan(path)
    elapsed_second = time.monotonic() - start
    print(f"Second scan (cached): {report2.scanned_files} files, {elapsed_second:.2f}s")
    print(f"Speedup: {elapsed_first / max(elapsed_second, 0.001):.1f}x")
