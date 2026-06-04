"""Custom exceptions raised by dupefinder."""


class DupeFinderError(Exception):
    """Base class for all dupefinder-specific errors."""


class InvalidPathError(DupeFinderError):
    """Raised when the scan path does not exist or is invalid."""


class UnsupportedHashAlgorithmError(DupeFinderError):
    """Raised when the selected hash algorithm is not available."""


class InvalidOptionError(DupeFinderError):
    """Raised when a ScanOptions value is unsafe or inconsistent."""


class FileAccessError(DupeFinderError):
    """Raised when a file or directory cannot be accessed in strict mode."""


class FileHashError(DupeFinderError):
    """Raised when a file cannot be hashed in strict mode."""


class _ScanCancelled(Exception):
    """Internal signal raised when hashing is cancelled mid-file. Not part of the public API."""
