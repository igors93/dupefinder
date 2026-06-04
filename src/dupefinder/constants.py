"""Central defaults used by dupefinder.

Keeping defaults here prevents magic numbers and repeated strings from being
spread across the codebase.
"""

SCHEMA_VERSION = "1.0"

DEFAULT_HASH_ALGORITHM = "sha256"
DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1 MiB
DEFAULT_MIN_SIZE = 1

DEFAULT_IGNORED_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".venv",
        "venv",
        "env",
        "node_modules",
    }
)

SIZE_UNITS = {
    "b": 1,
    "byte": 1,
    "bytes": 1,
    "kb": 1000,
    "mb": 1000**2,
    "gb": 1000**3,
    "tb": 1000**4,
    "kib": 1024,
    "mib": 1024**2,
    "gib": 1024**3,
    "tib": 1024**4,
}
