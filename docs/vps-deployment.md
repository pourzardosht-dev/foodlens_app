# Shared VPS deployment

FoodLens is designed to coexist with existing applications on the same Ubuntu VPS. Deployment must begin with inventory and preflight; never stop, rename or recreate unrelated containers and services.

## Isolation choices

- Compose project name: `foodlens`
- Default host port: `127.0.0.1:18431`
- PostgreSQL and MinIO have no published host ports.
- Volumes are scoped to the FoodLens Compose project.
- API, database and object storage have CPU and memory limits.
- Public HTTPS traffic must be routed by the VPS's existing reverse proxy to `127.0.0.1:18431`.

## Safe preflight

Run from the repository root on the VPS:

```bash
cp .env.example .env
chmod +x infra/preflight.sh
./infra/preflight.sh
docker compose --env-file .env -f infra/compose.yaml config
```

The script only reads host state. If port `18431` is occupied, set another high localhost port in `.env` and rerun preflight:

```dotenv
FOODLENS_API_PORT=18432
```

Only after reviewing `docker compose config` should the FoodLens services be started:

```bash
docker compose --env-file .env -f infra/compose.yaml up -d --build
docker compose --env-file .env -f infra/compose.yaml ps
curl --fail http://127.0.0.1:${FOODLENS_API_PORT:-18431}/health
```

Do not expose PostgreSQL or MinIO directly to the internet. Do not modify the existing reverse proxy until a FoodLens domain is chosen and its current configuration has been backed up.
