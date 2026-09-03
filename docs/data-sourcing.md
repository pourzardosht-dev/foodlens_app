# Data sourcing policy

## Cookpad

Cookpad is useful for discovering Iranian food names, aliases and recipe variation patterns. It must not be crawled or copied into the FoodLens image dataset without explicit written permission from Cookpad and, where required, the individual content owner.

Reasons:

- Cookpad states that users retain ownership of uploaded recipes and photographs.
- Its terms limit site materials to personal, non-commercial use and require explicit consent for commercial use.
- Its robots policy blocks multiple AI and dataset crawlers.
- A public URL and permissive default robots rule do not grant copyright or commercial reuse rights.

Allowed current workflow:

1. Manually record food names and ontology ideas without copying recipe text.
2. Store a source URL as a research reference.
3. Contact Cookpad for a commercial data partnership or explicit dataset licence.
4. Use only separately licensed images, commissioned images, owner submissions with consent, or original FoodLens photography for training and retrieval.

Do not download Cookpad images, mirror recipe text, remove attribution, or send Cookpad content to model training pipelines under the current policy.

References reviewed on 2026-09-03:

- https://cookpad.com/uk/terms
- https://cookpad.com/robots.txt
