#!/usr/bin/env bash
set -euo pipefail

repo_dir="${FOODLENS_REPO_DIR:-$HOME/foodlens}"
env_file="$repo_dir/.env"
compose_file="$repo_dir/infra/compose.yaml"

if [[ ! -f "$env_file" || ! -f "$compose_file" ]]; then
  echo "ERROR: FoodLens deployment files were not found in $repo_dir."
  exit 1
fi

printf "Enter NEW Gemini API key (input is hidden): " > /dev/tty
IFS= read -r -s gemini_key < /dev/tty
printf "\n" > /dev/tty

if [[ -z "$gemini_key" ]]; then
  echo "ERROR: API key cannot be empty."
  exit 1
fi

umask 077
temp_file=$(mktemp "$repo_dir/.env.XXXXXX")
trap 'rm -f "$temp_file"; unset gemini_key' EXIT

while IFS= read -r line || [[ -n "$line" ]]; do
  case "$line" in
    VISION_PROVIDER=*) printf "%s\n" "VISION_PROVIDER=gemini" ;;
    GEMINI_API_KEY=*) printf "GEMINI_API_KEY=%s\n" "$gemini_key" ;;
    *) printf "%s\n" "$line" ;;
  esac
done < "$env_file" > "$temp_file"

mv "$temp_file" "$env_file"
chmod 600 "$env_file"
unset gemini_key
trap - EXIT

cd "$repo_dir"
docker compose -p foodlens --env-file .env -f infra/compose.yaml \
  up -d --no-deps --force-recreate --wait --wait-timeout 90 api

curl --fail --silent --show-error --max-time 5 \
  http://127.0.0.1:18431/health
printf "\nSUCCESS: Gemini is configured and FoodLens API is healthy.\n"
