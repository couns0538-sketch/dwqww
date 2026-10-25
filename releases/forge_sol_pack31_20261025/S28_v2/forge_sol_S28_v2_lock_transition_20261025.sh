#!/usr/bin/env bash
# Linux qualification only; every output must be a new directory.
set -euo pipefail
script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
exec python3 -B "$script_dir/forge_sol_S28_v2_lock_transition_20261025.py" "$@"
