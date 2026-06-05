"""Public package interface for dupefinder."""

from dupefinder.api import find_duplicates, scan
from dupefinder.engine import DupeFinder
from dupefinder.events import ScanEvent, ScanProgress
from dupefinder.models import DuplicateGroup, FileInfo, ScanIssue, ScanOptions, ScanReport

__version__ = "0.4.0"

__all__ = [
    "find_duplicates",
    "scan",
    "DupeFinder",
    "ScanEvent",
    "ScanProgress",
    "DuplicateGroup",
    "FileInfo",
    "ScanIssue",
    "ScanOptions",
    "ScanReport",
]
