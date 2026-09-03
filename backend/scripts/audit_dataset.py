import argparse
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError


def audit_dataset(root: Path) -> int:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    class_counts: Counter[str] = Counter()
    format_counts: Counter[str] = Counter()
    invalid_files: list[tuple[Path, str]] = []
    small_images: list[tuple[Path, tuple[int, int]]] = []
    hashes: defaultdict[str, list[Path]] = defaultdict(list)

    for path in files:
        class_counts[path.parent.name] += 1
        hashes[hashlib.sha256(path.read_bytes()).hexdigest()].append(path)
        try:
            with Image.open(path) as image:
                image.verify()
                image_format = image.format or "UNKNOWN"
            with Image.open(path) as image:
                width, height = image.size
            format_counts[image_format] += 1
            if min(width, height) < 224:
                small_images.append((path, (width, height)))
        except (UnidentifiedImageError, OSError, ValueError) as error:
            invalid_files.append((path, str(error)))

    duplicate_groups = [paths for paths in hashes.values() if len(paths) > 1]
    duplicate_files = sum(len(paths) - 1 for paths in duplicate_groups)

    print(f"Dataset: {root.resolve()}")
    print(f"Files: {len(files)}")
    print(f"Classes: {dict(sorted(class_counts.items()))}")
    print(f"Formats: {dict(sorted(format_counts.items()))}")
    print(f"Invalid files: {len(invalid_files)}")
    for path, error in invalid_files[:20]:
        print(f"  INVALID {path}: {error}")
    print(f"Images with a side below 224px: {len(small_images)}")
    for path, size in small_images[:20]:
        print(f"  SMALL {path}: {size[0]}x{size[1]}")
    print(f"Exact duplicate groups: {len(duplicate_groups)}")
    print(f"Redundant exact duplicate files: {duplicate_files}")
    for paths in duplicate_groups[:20]:
        print("  DUPLICATE " + " | ".join(str(path) for path in paths))

    return 1 if invalid_files else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an image classification dataset")
    parser.add_argument("root", type=Path, help="Directory containing one folder per class")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"Dataset directory does not exist: {args.root}")
    return audit_dataset(args.root)


if __name__ == "__main__":
    raise SystemExit(main())