# Design

## Goal

The goal is to make duplicate detection easy for users and maintainable for developers.

## Main flow

```text
scan path
  -> discover files
  -> group by file size
  -> hash only files with matching sizes
  -> group by hash
  -> return report
```

## Why group by size first?

Two files with different sizes cannot be identical. Grouping by size before hashing avoids unnecessary work.

## Why hash in chunks?

Reading huge files all at once can use too much memory. Chunked reads keep memory usage stable.

## Why no deletion feature?

Deleting files is dangerous. This project focuses on detection. A future deletion feature should be explicit, optional, and heavily tested.

## Module responsibilities

- `api.py`: public functions.
- `scanner.py`: file discovery.
- `hashing.py`: hashing.
- `grouping.py`: duplicate grouping.
- `filters.py`: include/ignore rules.
- `models.py`: data classes.
- `report.py`: output formatting.
- `safety.py`: validation.
- `cli.py`: terminal interface.
