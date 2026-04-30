#!/usr/bin/env bash
set -euo pipefail

staged_files="$(git diff --cached --name-only --diff-filter=ACMRTUXB)"

if [[ -z "${staged_files}" ]]; then
  exit 0
fi

echo "Running pre-commit safety checks..."

# 1) Block committing real .env files
env_files_found=0
while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  base_name="$(basename "$file")"

  if [[ "$base_name" == ".env" ]]; then
    env_files_found=1
    echo "ERROR: Refusing to commit environment file: $file"
  fi
done <<< "$staged_files"

if [[ "$env_files_found" -eq 1 ]]; then
  echo "Use .env.example for templates and keep .env local only."
  exit 1
fi

# 2) Only check real .env files for explicit allowlist emails.
#    .env.example and documentation files are intentionally allowed.
while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  base_name="$(basename "$file")"
  [[ "$base_name" != ".env" ]] && continue

  # This check is intentionally scoped to .env only.
  if git diff --cached --unified=0 -- "$file" | grep -E '^\+.*ALLOWED_GOOGLE_EMAILS\s*=\s*.*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' >/dev/null; then
    echo "ERROR: Refusing to commit real emails in ALLOWED_GOOGLE_EMAILS inside $file."
    exit 1
  fi
done <<< "$staged_files"

echo "Pre-commit safety checks passed."
