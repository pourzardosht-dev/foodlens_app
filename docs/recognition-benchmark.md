# Recognition benchmark

The local licensed-image gate uses immutable JSONL manifests. The current dataset contains only Fesenjan and Ghormeh Sabzi, so it can measure those classes but cannot establish unsupported-food or non-food recall.

The 2026-09-05 local audit found 413 readable images, 22 below the 224 px minimum, one redundant exact duplicate, and two cross-label perceptual conflicts. The deterministic manifest contains 389 images: 311 train, 39 validation, and 39 test.

Create a local label map that is not committed with credentials or private metadata:

```json
{
  "فسنجان": "fesenjan",
  "قورمه سبزی": "ghormeh-sabzi"
}
```

Start an API configured with the provider under evaluation, then run:

```powershell
Set-Location backend
python scripts/benchmark_recognition.py `
  ../dataset/manifests/test.jsonl `
  "../food pic" `
  ../dataset/label-map.json `
  --base-url http://127.0.0.1:8000 `
  --output ../dataset/results/provider-test.json
```

The evaluator verifies each image SHA-256 before upload and records no image bytes in its report. It reports top-1 accuracy, unknown rate, confirmation rate, request errors, per-class counts, and p50/p95 latency.

Before using results as a production gate, expand the held-out test set to at least 100 licensed images spanning supported foods, unsupported Iranian foods, non-food images, poor lighting, rotation, and partial occlusion. Record provider/model configuration and actual API billing metadata alongside each report.