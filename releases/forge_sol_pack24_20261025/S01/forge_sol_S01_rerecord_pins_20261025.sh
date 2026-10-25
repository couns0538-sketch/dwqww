#!/usr/bin/env bash
# Read-only engine pin observations; never changes expected values or host limits.
set -euo pipefail
script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
exec python3 -B "$script_dir/forge_sol_S01_rerecord_pins_20261025.py" "$@"
