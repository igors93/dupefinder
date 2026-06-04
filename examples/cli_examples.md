# CLI examples

Scan the current folder:

```bash
dupefinder .
```

Scan Downloads:

```bash
dupefinder ~/Downloads
```

Show JSON:

```bash
dupefinder ~/Downloads --json
```

Ignore files smaller than 1 MB:

```bash
dupefinder ~/Downloads --min-size 1MB
```

Only scan images:

```bash
dupefinder ~/Pictures --include-ext .jpg,.jpeg,.png
```

Ignore log and temporary files:

```bash
dupefinder . --ignore-ext .log,.tmp
```

Return exit code 2 if duplicates exist:

```bash
dupefinder . --fail-on-duplicates
```
