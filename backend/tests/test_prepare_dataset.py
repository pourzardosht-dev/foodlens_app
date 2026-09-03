from scripts.prepare_dataset import ImageRecord, build_groups, split_groups


def make_record(path: str, label: str, index: int) -> ImageRecord:
    return ImageRecord(
        path=path,
        label=label,
        width=320,
        height=320,
        sha256=f"hash-{index}",
        perceptual_hash=(index * 0x9E3779B97F4A7C15) & ((1 << 64) - 1),
    )


def test_duplicate_groups_never_cross_splits_and_are_deterministic() -> None:
    records = [
        make_record(f"class-a/image-{index}.jpg", "class-a", index)
        for index in range(1, 21)
    ]
    duplicate = ImageRecord(
        path="class-a/image-1-copy.jpg",
        label="class-a",
        width=320,
        height=320,
        sha256=records[0].sha256,
        perceptual_hash=records[0].perceptual_hash,
    )
    records.append(duplicate)

    groups = build_groups(records, perceptual_distance=0)
    first_splits, first_conflicts = split_groups(groups, seed=42)
    second_splits, second_conflicts = split_groups(groups, seed=42)

    assert first_conflicts == []
    assert second_conflicts == []
    assert first_splits == second_splits
    duplicate_splits = {
        split
        for split, split_records in first_splits.items()
        if records[0] in split_records or duplicate in split_records
    }
    assert len(duplicate_splits) == 1