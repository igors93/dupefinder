"""Public package interface for dupefinder.

Most users should import from here instead of internal modules.
"""

from dupefinder.api import find_duplicates, scan
from dupefinder.models import DuplicateGroup, FileInfo, ScanIssue, ScanOptions, ScanReport

__version__ = "0.1.0"

__all__ = [
    "find_duplicates",
    "scan",
    "DuplicateGroup",
    "FileInfo",
    "ScanIssue",
    "ScanOptions",
    "ScanReport",
]
