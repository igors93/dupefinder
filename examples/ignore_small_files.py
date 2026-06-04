"""Ignore tiny files during duplicate search."""

from dupefinder import find_duplicates
from dupefinder.models import ScanOptions

# 1 MiB. Tiny files are often not worth reporting in cleanup tools.
ONE_MIB = 1024 * 1024

groups = find_duplicates(".", options=ScanOptions(min_size=ONE_MIB))

for group in groups:
    print(group)
