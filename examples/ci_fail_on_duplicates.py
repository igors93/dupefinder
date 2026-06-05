"""CI script: exit with code 2 if duplicates are found."""

import sys
from dupefinder import find_duplicates

path = sys.argv[1] if len(sys.argv) > 1 else "."
groups = find_duplicates(path)

if groups:
    print(f"ERROR: {len(groups)} duplicate group(s) found.", file=sys.stderr)
    for group in groups:
        print(f"  {group.count} files — {group.size} bytes each:", file=sys.stderr)
        for p in group.files:
            print(f"    {p}", file=sys.stderr)
    sys.exit(2)

print("No duplicates found.")
