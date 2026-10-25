#!/usr/bin/env bash
set -euo pipefail
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec python3 -B "$script_dir/forge_sol_S28_lock_transition_20261025.py" "$@"
