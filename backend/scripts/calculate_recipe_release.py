import argparse
from datetime import datetime
from pathlib import Path

from app.domain.recipe_calculation import calculate_recipe_release


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Calculate a sourced nutrition release from a recipe worksheet"
    )
    parser.add_argument("worksheet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--reviewer-note", required=True)
    parser.add_argument("--effective-at", required=True)
    args = parser.parse_args()

    release = calculate_recipe_release(
        args.worksheet,
        release_id=args.release_id,
        reviewer_note=args.reviewer_note,
        effective_at=datetime.fromisoformat(args.effective_at.replace("Z", "+00:00")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(release.model_dump_json(indent=2), encoding="utf-8")
    print(f"Calculated {len(release.foods)} food profiles: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())