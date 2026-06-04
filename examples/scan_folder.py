"""Get a complete scan report."""

from dupefinder import scan
from dupefinder.models import ScanOptions
from dupefinder.report import format_report


report = scan(
    ".",
    options=ScanOptions(
        algorithm="sha256",
        ignore_hidden=True,
        follow_symlinks=False,
    ),
)

print(format_report(report))
