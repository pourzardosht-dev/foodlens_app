import argparse
from pathlib import Path

from app.db.session import session_scope
from app.domain.nutrition_release import apply_release, load_release, release_summary
from app.nutrition import FOODS


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate or transactionally publish a sourced nutrition release"
    )
    parser.add_argument("release", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    release = load_release(args.release)
    fallback_ids = {food.id for food in FOODS}
    unknown = sorted({item.food_id for item in release.foods} - fallback_ids)
    if unknown:
        parser.error(f"unknown catalog food IDs: {', '.join(unknown)}")
    print(release_summary(release))
    if not args.apply:
        print("Validated only. Re-run with --apply to publish this release.")
        return 0

    with session_scope() as session:
        count = apply_release(session, release)
    print(f"Published {count} sourced food profiles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())