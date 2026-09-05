#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${1:-${repo_root}/.env}"
backup_file="${2:-}"

if [[ -z "${backup_file}" || ! -f "${backup_file}" ]]; then
  echo "ERROR: pass an existing .dump.age backup as the second argument." >&2
  exit 1
fi
if ! command -v age >/dev/null 2>&1; then
  echo "ERROR: age is required for restore tests." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${BACKUP_AGE_IDENTITY:?BACKUP_AGE_IDENTITY is required}"

compose=(docker compose -p foodlens --env-file "${env_file}" -f "${repo_root}/infra/compose.yaml")
restore_db="foodlens_restore_test_$(date -u +%Y%m%d%H%M%S)"
started_at="$(date +%s)"

cleanup() {
  "${compose[@]}" exec -T postgres \
    dropdb --if-exists --username "${POSTGRES_USER}" "${restore_db}" >/dev/null
}
trap cleanup EXIT

if [[ -f "${backup_file}.sha256" ]]; then
  (cd "$(dirname "${backup_file}")" && sha256sum --check "$(basename "${backup_file}.sha256")")
fi
"${compose[@]}" exec -T postgres \
  createdb --username "${POSTGRES_USER}" "${restore_db}"
age --decrypt --identity "${BACKUP_AGE_IDENTITY}" "${backup_file}" \
  | "${compose[@]}" exec -T postgres \
    pg_restore --exit-on-error --no-owner --no-privileges \
    --username "${POSTGRES_USER}" --dbname "${restore_db}"

"${compose[@]}" exec -T postgres psql \
  --username "${POSTGRES_USER}" --dbname "${restore_db}" \
  --tuples-only --command \
  "SELECT 'profiles=' || count(*) FROM profiles UNION ALL SELECT 'foods=' || count(*) FROM foods UNION ALL SELECT 'meals=' || count(*) FROM meals;"

echo "Restore test completed in $(( $(date +%s) - started_at )) seconds."