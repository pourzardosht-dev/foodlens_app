# Shared VPS deployment

FoodLens is designed to coexist with existing applications on the same Ubuntu VPS. Deployment must begin with inventory and preflight; never stop, rename or recreate unrelated containers and services.

## Isolation choices

- Compose project name: `foodlens`
- Default host port: `127.0.0.1:18431`
- The default deployment starts only the API. PostgreSQL is disabled behind the optional `database` profile, and MinIO is independently disabled behind `object-storage`; neither publishes host ports.
- Volumes are scoped to the FoodLens Compose project.
- The API is limited to 1 CPU, 1 GB RAM and 256 processes. Its local Docker logs rotate at 10 MB with three files retained.
- Optional database and object storage services have their own CPU and memory limits.
- Public HTTPS traffic must be routed by the VPS's existing reverse proxy to `127.0.0.1:18431`.

## Operations that are not allowed

- Do not stop, restart, rename or recreate any container outside the `foodlens` Compose project.
- Do not run `docker system prune`, change firewall rules or perform system package upgrades during this deployment.
- Do not edit the existing QuizLens or other Nginx site files. FoodLens must use a separate site file.
- Do not reload Nginx unless `nginx -t` succeeds first.
- Every Compose start, status or rollback command must explicitly use project name `foodlens` and `infra/compose.yaml`.

## Safe preflight

Run from the repository root on the VPS:

```bash
cp .env.example .env
chmod +x infra/preflight.sh
./infra/preflight.sh
docker compose -p foodlens --env-file .env -f infra/compose.yaml config
```

The script only reads host state. If port `18431` is occupied, set another high localhost port in `.env` and rerun preflight:

```dotenv
FOODLENS_API_PORT=18432
```

Only after reviewing `docker compose config` should the FoodLens services be started:

```bash
docker compose -p foodlens --env-file .env -f infra/compose.yaml up -d --build api
docker compose -p foodlens --env-file .env -f infra/compose.yaml ps
curl --fail http://127.0.0.1:${FOODLENS_API_PORT:-18431}/health
```

## PostgreSQL rollout

Enable the database and apply migrations as scoped FoodLens services:

```bash
docker compose -p foodlens --env-file .env -f infra/compose.yaml --profile database up -d postgres
docker compose -p foodlens --env-file .env -f infra/compose.yaml --profile database run --rm migrate
curl --fail http://127.0.0.1:${FOODLENS_API_PORT:-18431}/health/database
```

Set a unique `TOKEN_PEPPER` and an age recipient/identity in the server `.env`. Never copy the age private identity into the repository.

Create an encrypted backup and perform a restore test in an isolated temporary database:

```bash
./infra/backup-postgres.sh .env /var/backups/foodlens/postgres
./infra/test-postgres-restore.sh .env /var/backups/foodlens/postgres/daily/<backup>.dump.age
```

Schedule the backup script daily. It retains seven daily backups and five weeks of Sunday backups. The restore test verifies the encrypted checksum and reports profile, food, and meal row counts before deleting its temporary database.

After publishing the initial nutrition release, run the disposable production smoke test. It deletes its profile and records even when a later assertion fails:

```bash
cd backend
python scripts/smoke_personal_data.py \
	--base-url https://api.example.com \
	--origin https://app.example.com
```

The smoke test checks health, database connectivity, CORS, the production publication gate, profile and diary CRUD, JSON export, full deletion, and the diary p95 target.

Do not expose PostgreSQL or MinIO directly to the internet. Do not modify the existing reverse proxy until a FoodLens domain is chosen and its current configuration has been backed up.
