from scripts.benchmark_recognition import summarize


def test_benchmark_summary_reports_accuracy_unknown_and_latency() -> None:
    results = [
        {
            "expected_food_id": "fesenjan",
            "predicted_food_id": "fesenjan",
            "needs_confirmation": False,
            "latency_ms": 100,
            "error": None,
        },
        {
            "expected_food_id": "ghormeh-sabzi",
            "predicted_food_id": None,
            "needs_confirmation": True,
            "latency_ms": 200,
            "error": None,
        },
        {
            "expected_food_id": "fesenjan",
            "predicted_food_id": None,
            "needs_confirmation": True,
            "latency_ms": 10,
            "error": "HTTPStatusError",
        },
    ]

    summary = summarize(results)

    assert summary["top1_accuracy"] == 0.5
    assert summary["unknown_rate"] == 0.5
    assert summary["request_errors"] == 1
    assert summary["latency_ms"] == {"p50": 100, "p95": 200}
    assert summary["per_class"]["fesenjan"] == {
        "total": 1,
        "correct": 1,
        "unknown": 0,
    }