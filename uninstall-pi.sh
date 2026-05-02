#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$SCRIPT_DIR/dietpi-uninstall.sh"

if [[ ! -f "$TARGET" ]]; then
  echo "Missing script: $TARGET"
  exit 1
fi

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo: sudo ./uninstall-pi.sh"
  exit 1
fi

exec "$TARGET" "$@"
