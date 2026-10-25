#!/usr/bin/env bash
# Fixed chess oracles only; no affinity, host-limit or termination changes.
set -euo pipefail
here="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
exec python3 -B "$here/forge_sol_S03_fixedrefs_20261025.py" "$@"
