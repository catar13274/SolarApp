#!/usr/bin/env bash
set -euo pipefail

staged_files="$(git diff --cached --name-only --diff-filter=ACMRTUXB)"

if [[ -z "${staged_files}" ]]; then
  exit 0
fi

echo "Running pre-commit safety checks..."

# 1) Block committing real .env files
while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  base_name="$(basename "$file")"

  if [[ "$base_name" == ".env" ]]; then
    echo "ERROR: Refusing to commit environment file: $file"
    echo "Use .env.example for templates and keep .env local only."
    exit 1
  fi
done <<< "$staged_files"

# 2) Block explicit personal emails in allowlist-like keys
#    Allows empty placeholders but blocks real values such as:
#    ALLOWED_GOOGLE_EMAILS=alice@company.com,bob@company.com
staged_diff="$(git diff --cached --unified=0 -- .)"

if echo "$staged_diff" | rg -n "^\+.*ALLOWED_GOOGLE_EMAILS\s*=\s*.*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" >/dev/null; then
  echo "ERROR: Refusing to commit real emails in ALLOWED_GOOGLE_EMAILS."
  echo "Replace with placeholder values in tracked files."
  exit 1
fi

echo "Pre-commit safety checks passed."
