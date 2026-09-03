import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError


@dataclass(frozen=True)
class ImageRecord:
    path: str
    label: str
    width: int
    height: int
    sha256: str
    perceptual_hash: int


class DisjointSet:
    def __init__(self, size: int) -> None:
        self.parents = list(range(size))

    def find(self, item: int) -> int:
        while self.parents[item] != item:
            self.parents[item] = self.parents[self.parents[item]]
            item = self.parents[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parents[right_root] = left_root


def difference_hash(image: Image.Image) -> int:
    pixels = list(image.convert("L").resize((9, 8)).get_flattened_data())
    value = 0
    for row in range(8):
        offset = row * 9
        for column in range(8):
            value = (value << 1) | (
                pixels[offset + column] > pixels[offset + column + 1]
            )
    return value


def inspect_images(
    root: Path, minimum_side: int
) -> tuple[list[ImageRecord], list[dict[str, object]]]:
    records: list[ImageRecord] = []
    excluded: list[dict[str, object]] = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative_path = path.relative_to(root).as_posix()
        try:
            content = path.read_bytes()
            with Image.open(path) as image:
                image.load()
                width, height = image.size
                perceptual_hash = difference_hash(image)
        except (UnidentifiedImageError, OSError, ValueError) as error:
            excluded.append(
                {"path": relative_path, "reason": "invalid", "detail": str(error)}
            )
            continue

        if min(width, height) < minimum_side:
            excluded.append(
                {
                    "path": relative_path,
                    "reason": "small",
                    "width": width,
                    "height": height,
                }
            )
            continue

        records.append(
            ImageRecord(
                path=relative_path,
                label=path.parent.name,
                width=width,
                height=height,
                sha256=hashlib.sha256(content).hexdigest(),
                perceptual_hash=perceptual_hash,
            )
        )
    return records, excluded


def build_groups(
    records: list[ImageRecord], perceptual_distance: int
) -> list[list[ImageRecord]]:
    sets = DisjointSet(len(records))
    exact_hashes: dict[str, int] = {}
    for index, record in enumerate(records):
        duplicate_index = exact_hashes.setdefault(record.sha256, index)
        sets.union(index, duplicate_index)

    for left in range(len(records)):
        for right in range(left + 1, len(records)):
            if (
                records[left].perceptual_hash ^ records[right].perceptual_hash
            ).bit_count() <= perceptual_distance:
                sets.union(left, right)

    groups: defaultdict[int, list[ImageRecord]] = defaultdict(list)
    for index, record in enumerate(records):
        groups[sets.find(index)].append(record)
    return [sorted(group, key=lambda record: record.path) for group in groups.values()]


def split_groups(
    groups: list[list[ImageRecord]], seed: int
) -> tuple[dict[str, list[ImageRecord]], list[dict[str, object]]]:
    split_records: dict[str, list[ImageRecord]] = {
        "train": [],
        "validation": [],
        "test": [],
    }
    conflicts: list[dict[str, object]] = []
    groups_by_label: defaultdict[str, list[list[ImageRecord]]] = defaultdict(list)
    for group in groups:
        labels = sorted({record.label for record in group})
        if len(labels) != 1:
            conflicts.extend(
                {
                    "path": record.path,
                    "reason": "label_conflict",
                    "labels": labels,
                }
                for record in group
            )
            continue
        groups_by_label[labels[0]].append(group)

    for label, label_groups in sorted(groups_by_label.items()):
        random.Random(f"{seed}:{label}").shuffle(label_groups)
        targets = {"train": 0.8, "validation": 0.1, "test": 0.1}
        total = sum(len(group) for group in label_groups)
        class_counts = {name: 0 for name in targets}
        for group in sorted(label_groups, key=len, reverse=True):
            split = min(
                targets,
                key=lambda name: class_counts[name] / targets[name],
            )
            split_records[split].extend(group)
            class_counts[split] += len(group)

        if sum(class_counts.values()) != total:
            raise RuntimeError(f"Failed to assign every image for class {label}")

    for records in split_records.values():
        records.sort(key=lambda record: record.path)
    return split_records, conflicts


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    content = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    )
    path.write_text(content, encoding="utf-8")


def prepare_dataset(
    root: Path,
    output: Path,
    seed: int,
    minimum_side: int,
    perceptual_distance: int,
) -> dict[str, object]:
    records, excluded = inspect_images(root, minimum_side)
    groups = build_groups(records, perceptual_distance)
    splits, conflicts = split_groups(groups, seed)
    excluded.extend(conflicts)
    output.mkdir(parents=True, exist_ok=True)

    for split, split_records in splits.items():
        write_jsonl(
            output / f"{split}.jsonl",
            [
                {
                    "path": record.path,
                    "label": record.label,
                    "width": record.width,
                    "height": record.height,
                    "sha256": record.sha256,
                }
                for record in split_records
            ],
        )
    write_jsonl(output / "excluded.jsonl", excluded)

    summary: dict[str, object] = {
        "dataset_root": root.resolve().as_posix(),
        "seed": seed,
        "minimum_side": minimum_side,
        "perceptual_distance": perceptual_distance,
        "eligible_images": len(records),
        "included_images": sum(len(records) for records in splits.values()),
        "duplicate_groups": sum(len(group) > 1 for group in groups),
        "excluded": dict(sorted(Counter(row["reason"] for row in excluded).items())),
        "splits": {
            split: {
                "total": len(split_records),
                "classes": dict(
                    sorted(Counter(record.label for record in split_records).items())
                ),
            }
            for split, split_records in splits.items()
        },
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create deterministic dataset manifests without moving source images"
    )
    parser.add_argument("root", type=Path, help="Directory containing one folder per class")
    parser.add_argument("output", type=Path, help="Directory for generated manifests")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--minimum-side", type=int, default=224)
    parser.add_argument("--perceptual-distance", type=int, default=4)
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"Dataset directory does not exist: {args.root}")
    summary = prepare_dataset(
        args.root,
        args.output,
        args.seed,
        args.minimum_side,
        args.perceptual_distance,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())