#!/usr/bin/env bash
set -euo pipefail

api_port="${FOODLENS_API_PORT:-18431}"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: docker compose plugin is not installed."
  exit 1
fi

if ss -H -ltn "sport = :${api_port}" | grep -q .; then
  echo "ERROR: TCP port ${api_port} is already in use. Choose another FOODLENS_API_PORT."
  ss -H -ltnp "sport = :${api_port}" || true
  exit 1
fi

echo "OK: TCP port ${api_port} is free."
echo "Host resources:"
free -h
df -h /
echo "Existing containers (no changes made):"
docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'
echo "Preflight completed. No services were modified."