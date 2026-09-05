import argparse
import hashlib
import json
import math
import mimetypes
import time
from collections import Counter
from pathlib import Path

import httpx


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0
    index = max(0, math.ceil(len(values) * percentile_value) - 1)
    return sorted(values)[index]


def summarize(results: list[dict[str, object]]) -> dict[str, object]:
    successful = [item for item in results if item["error"] is None]
    latencies = [float(item["latency_ms"]) for item in successful]
    correct = sum(item["expected_food_id"] == item["predicted_food_id"] for item in successful)
    unknown = sum(item["predicted_food_id"] is None for item in successful)
    confirmations = sum(bool(item["needs_confirmation"]) for item in successful)
    per_class: dict[str, dict[str, int]] = {}
    for food_id in sorted({str(item["expected_food_id"]) for item in results}):
        class_results = [item for item in successful if item["expected_food_id"] == food_id]
        per_class[food_id] = {
            "total": len(class_results),
            "correct": sum(item["predicted_food_id"] == food_id for item in class_results),
            "unknown": sum(item["predicted_food_id"] is None for item in class_results),
        }
    return {
        "total": len(results),
        "successful_requests": len(successful),
        "request_errors": len(results) - len(successful),
        "top1_accuracy": correct / len(successful) if successful else 0,
        "unknown_rate": unknown / len(successful) if successful else 0,
        "needs_confirmation_rate": confirmations / len(successful) if successful else 0,
        "latency_ms": {
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
        },
        "predictions": dict(
            sorted(Counter(str(item["predicted_food_id"]) for item in successful).items())
        ),
        "per_class": per_class,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark the FoodLens recognition API from a dataset manifest"
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("label_map", type=Path)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    label_map = json.loads(args.label_map.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in args.manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if args.limit is not None:
        rows = rows[: args.limit]
    missing_labels = sorted({row["label"] for row in rows} - set(label_map))
    if missing_labels:
        parser.error(f"label map is missing: {', '.join(missing_labels)}")

    results: list[dict[str, object]] = []
    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=45) as client:
        for index, row in enumerate(rows, start=1):
            image_path = args.dataset_root / row["path"]
            content = image_path.read_bytes()
            if hashlib.sha256(content).hexdigest() != row["sha256"]:
                raise RuntimeError(f"manifest hash mismatch: {row['path']}")
            started_at = time.perf_counter()
            predicted_food_id = None
            needs_confirmation = True
            error = None
            try:
                response = client.post(
                    "/v1/recognition",
                    files={
                        "image": (
                            image_path.name,
                            content,
                            mimetypes.guess_type(image_path.name)[0]
                            or "application/octet-stream",
                        )
                    },
                )
                response.raise_for_status()
                body = response.json()
                predicted_food_id = body["food_id"]
                needs_confirmation = body["needs_confirmation"]
            except (httpx.HTTPError, KeyError, ValueError) as exception:
                error = type(exception).__name__
            results.append(
                {
                    "index": index,
                    "sha256": row["sha256"],
                    "expected_food_id": label_map[row["label"]],
                    "predicted_food_id": predicted_food_id,
                    "needs_confirmation": needs_confirmation,
                    "latency_ms": (time.perf_counter() - started_at) * 1000,
                    "error": error,
                }
            )
            print(f"[{index}/{len(rows)}] {row['label']} -> {predicted_food_id or 'unknown'}")

    report = {"summary": summarize(results), "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".partial")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(args.output)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0 if report["summary"]["request_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())