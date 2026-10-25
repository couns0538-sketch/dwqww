#!/usr/bin/env bash
# Linux GNU g++ pure-PGO build/correctness pipeline (no timing experiment).
# CPU/memory/priority limits must be established by the caller's reviewed
# supervisor. Its ACTIVE marker and ONE admission deadline attest that context;
# setting those variables alone does not establish any resource limit.
# Defaults consume the canonical packaged lock/recipe; options override defaults.
set -euo pipefail
script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
run_stamp=$(date -u +%Y%m%d_%H%M%S)
exec "${PYTHON:-python3}" "$script_dir/forge_sol_pgo_worker_20261025.py" --platform linux \
  --phase all --source "$script_dir/forge_sol_lock_source_20261025" \
  --out "$script_dir/forge_sol_pgo_linux_run_$run_stamp" \
  --recipe "$script_dir/forge_sol_lock_pc_recipe_20261025.ps1" --cxx "${CXX:-g++}" "$@"
