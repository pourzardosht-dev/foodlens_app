#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${1:-${repo_root}/.env}"
backup_root="${2:-${repo_root}/backups/postgres}"

if [[ ! -f "${env_file}" ]]; then
  echo "ERROR: env file not found: ${env_file}" >&2
  exit 1
fi
if ! command -v age >/dev/null 2>&1; then
  echo "ERROR: age is required for encrypted backups." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${BACKUP_AGE_RECIPIENT:?BACKUP_AGE_RECIPIENT is required}"

compose=(docker compose -p foodlens --env-file "${env_file}" -f "${repo_root}/infra/compose.yaml")
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
daily_dir="${backup_root}/daily"
weekly_dir="${backup_root}/weekly"
mkdir -p "${daily_dir}" "${weekly_dir}"
output="${daily_dir}/foodlens-${timestamp}.dump.age"
temporary="${output}.partial"
trap 'rm -f "${temporary}"' EXIT

"${compose[@]}" exec -T postgres \
  pg_dump --format=custom --no-owner --no-privileges \
  --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" \
  | age --recipient "${BACKUP_AGE_RECIPIENT}" --output "${temporary}"
mv "${temporary}" "${output}"
sha256sum "${output}" > "${output}.sha256"

find "${daily_dir}" -type f -mtime +7 -delete
if [[ "$(date -u +%u)" == "7" ]]; then
  cp "${output}" "${weekly_dir}/"
  cp "${output}.sha256" "${weekly_dir}/"
fi
find "${weekly_dir}" -type f -mtime +35 -delete

echo "Encrypted FoodLens backup created: ${output}"