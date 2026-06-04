# Quickstart

## Install locally

```bash
python -m pip install -e .
```

## Use in Python

```python
from dupefinder import find_duplicates

groups = find_duplicates("./Downloads")

for group in groups:
    print(group.files)
```

## Use in terminal

```bash
dupefinder ./Downloads
```

## Important idea

`dupefinder` finds duplicate files. It does not delete them.
