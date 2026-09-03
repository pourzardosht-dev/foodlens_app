# Vision provider decision

Last reviewed: 2026-09-03

## Initial choice

FoodLens starts with `gemini-2.5-flash` behind the `VisionProvider` interface. It supports image input and structured JSON output, has stable production availability, and currently costs $0.30 per million input tokens and $2.50 per million output tokens on the paid tier.

This is a starting hypothesis, not a permanent winner. No general-purpose vision model can guarantee completely correct food recognition. The final provider will be selected using the FoodLens gold benchmark.

## Candidate snapshot

| Provider | Candidate | Input / 1M tokens | Output / 1M tokens | Status |
| --- | --- | ---: | ---: | --- |
| Google | Gemini 2.5 Flash | $0.30 | $2.50 | Initial production candidate |
| OpenAI | GPT-5.6 Luna | $0.20 | $1.20 | Benchmark candidate |
| DeepSeek | V4 Flash Vision | $0.22-$0.44 | $0.66-$1.32 | Experimental; benchmark only |

DeepSeek prices vary between off-peak and peak hours. Prices can change and must not be hard-coded into product logic.

Official references:

- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/image-understanding
- https://developers.openai.com/api/docs/pricing
- https://developers.openai.com/api/docs/guides/images-vision
- https://api-docs.deepseek.com/quick_start/pricing

## Benchmark gate

Before public release, evaluate at least 100 held-out Iranian food images containing:

- Supported foods from homes and restaurants
- Visually similar foods
- Unsupported Iranian foods
- Non-food images
- Poor lighting, rotation and partial occlusion

Measure top-1 accuracy, unknown recall, false acceptance rate, calibrated confidence, p50/p95 latency and cost per 1,000 analyses. A provider change is configuration-only; application code must not depend on provider-specific response formats.

The first benchmark target is not 100% accuracy. It is high supported-food accuracy while safely returning `unknown` for ambiguous and unsupported images.
