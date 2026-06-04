"""Basic dupefinder usage."""

from dupefinder import find_duplicates


def main() -> None:
    groups = find_duplicates(".")

    for group in groups:
        print(f"Found {group.count} duplicate files of {group.size} bytes:")
        for file_path in group.files:
            print(" -", file_path)


if __name__ == "__main__":
    main()
