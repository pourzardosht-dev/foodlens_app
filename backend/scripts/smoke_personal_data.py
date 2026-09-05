import argparse
import math
import time
from datetime import UTC, datetime

import httpx


def require_status(response: httpx.Response, expected: int) -> None:
    if response.status_code != expected:
        raise RuntimeError(
            f"{response.request.method} {response.request.url.path} returned "
            f"{response.status_code}; expected {expected}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run disposable FoodLens personal-data production smoke tests"
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--expected-published-foods", type=int, default=20)
    parser.add_argument("--latency-samples", type=int, default=20)
    parser.add_argument("--diary-p95-ms", type=float, default=500)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    token: str | None = None
    headers: dict[str, str] = {}
    with httpx.Client(base_url=base_url, timeout=15) as client:
        require_status(client.get("/health"), 200)
        require_status(client.get("/health/database"), 200)
        foods_response = client.get("/v1/foods")
        require_status(foods_response, 200)
        foods = foods_response.json()
        if len(foods) < args.expected_published_foods:
            raise RuntimeError(
                f"published catalog has {len(foods)} foods; "
                f"expected at least {args.expected_published_foods}"
            )
        if any(
            food.get("nutrition_status")
            not in {"source_checked", "nutritionist_reviewed"}
            for food in foods
        ):
            raise RuntimeError("production catalog exposed an unpublished profile")

        cors = client.options(
            "/v1/profile",
            headers={
                "Origin": args.origin,
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        require_status(cors, 200)
        if "PATCH" not in cors.headers.get("access-control-allow-methods", ""):
            raise RuntimeError("CORS preflight did not allow PATCH")

        try:
            created_profile = client.post(
                "/v1/profiles/anonymous",
                json={"timezone": "UTC", "locale": "fa-IR"},
            )
            require_status(created_profile, 201)
            token = created_profile.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            custom_food = client.post(
                "/v1/custom-foods",
                headers=headers,
                json={
                    "name_fa": "Smoke test food",
                    "name_en": "Smoke test food",
                    "kcal_per_100g": 100,
                    "protein_g_per_100g": 10,
                    "carb_g_per_100g": 10,
                    "fat_g_per_100g": 2,
                    "fiber_g_per_100g": 1,
                    "uncertainty_percent": 0,
                },
            )
            require_status(custom_food, 201)
            food_id = custom_food.json()["id"]
            eaten_at = datetime.now(UTC)
            meal = client.post(
                "/v1/meals",
                headers=headers,
                json={
                    "meal_type": "snack",
                    "eaten_at": eaten_at.isoformat(),
                    "source": "manual",
                    "components": [{"food_id": food_id, "grams": 100}],
                },
            )
            require_status(meal, 201)

            durations: list[float] = []
            for _ in range(args.latency_samples):
                started_at = time.perf_counter()
                diary = client.get(
                    "/v1/diary/day",
                    headers=headers,
                    params={"date": eaten_at.date().isoformat()},
                )
                durations.append((time.perf_counter() - started_at) * 1000)
                require_status(diary, 200)
                if len(diary.json()["meals"]) != 1:
                    raise RuntimeError("saved meal was not returned by the diary")
            p95_index = max(0, math.ceil(len(durations) * 0.95) - 1)
            p95_ms = sorted(durations)[p95_index]
            if p95_ms >= args.diary_p95_ms:
                raise RuntimeError(
                    f"diary p95 was {p95_ms:.1f} ms; target is below "
                    f"{args.diary_p95_ms:.1f} ms"
                )

            exported = client.get("/v1/profile/export", headers=headers)
            require_status(exported, 200)
            if not exported.json()["meals"] or not exported.json()["custom_foods"]:
                raise RuntimeError("profile export omitted smoke-test records")
            print(
                f"Smoke test passed: {len(foods)} published foods, "
                f"diary p95 {p95_ms:.1f} ms over {len(durations)} samples."
            )
        finally:
            if token is not None:
                deleted = client.delete("/v1/profile", headers=headers)
                require_status(deleted, 204)
                require_status(client.get("/v1/profile", headers=headers), 401)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())