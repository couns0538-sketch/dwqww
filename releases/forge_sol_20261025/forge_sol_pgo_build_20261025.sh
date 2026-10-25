#!/usr/bin/env bash
# Linux GNU g++ pure-PGO build/lock-bench/internal-QA pipeline, no NPS experiment.
# This launcher establishes Linux controls; the Windows job uses its own shared
# aggregate limit. Original Linux QA tests may kill their owned child on timeout.
set -euo pipefail
script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
pgo_python=${PYTHON:-python3}
function pgo_fail { printf '%s\n' "PGO LINUX GUARD STOP: $*" >&2; exit 2; }
command -v uname >/dev/null || pgo_fail 'uname is required'
[[ $(uname -s) == Linux ]] || pgo_fail 'Linux is required; use the PowerShell entry on Windows'
for pgo_argument in "$@"; do
  if [[ $pgo_argument == --help || $pgo_argument == -h ]]; then
    cat <<'PGO_HELP'
Usage: bash forge_sol_pgo_build_20261025.sh [worker options]
Default: complete Linux build, lock-bench and unchanged CTest QA pipeline.
Options: --source DIR --recipe FILE --out NEW_DIR --cxx G++ --cmake CMAKE
         --phase all|baseline|check-baseline|generate|train|check-instrumented|use|check-use|validate
Linux controls: taskset CPUs0-3, nice19, inherited per-process RLIMIT_AS3GiB.
The address-space cap is per process, not an aggregate Windows job-memory cap.
One existing admission deadline is reused; otherwise this launch sets now+2580s.
No timing experiment. Original Linux CTest may kill its owned child on timeout.
--guard-self-test reads back actual controls and exits without invoking GCC.
PGO_HELP
    exit 0
  fi
done
for pgo_tool in taskset nice date "$pgo_python"; do
  command -v -- "$pgo_tool" >/dev/null || pgo_fail "required tool missing: $pgo_tool"
done
if [[ ${1:-} != --__forge_pgo_guarded_20261025 ]]; then
  # Every descendant inherits affinity/priority. Failure admits no worker.
  exec taskset --cpu-list 0-3 nice -n 19 "$BASH" "$script_dir/forge_sol_pgo_build_20261025.sh" --__forge_pgo_guarded_20261025 "$@"
fi
shift
# Set soft first so lowering hard cannot leave a higher inherited soft limit.
ulimit -S -v 3145728 || pgo_fail 'cannot establish 3GiB soft RLIMIT_AS'
ulimit -H -v 3145728 || pgo_fail 'cannot establish 3GiB hard RLIMIT_AS'
if [[ ! ${FORGE_PGO_ADMISSION_DEADLINE_UNIX+x} ]]; then
  FORGE_PGO_ADMISSION_DEADLINE_UNIX=$(( $(date -u +%s) + 2580 ))
fi
export FORGE_PGO_ADMISSION_DEADLINE_UNIX
export PYTHONDONTWRITEBYTECODE=1
"$pgo_python" - <<'PGO_READBACK'
# BEGIN_FORGE_PGO_READBACK_PY
import json
import math
import os
import resource
import time

cap = 3 * 1024 * 1024 * 1024
affinity = set(os.sched_getaffinity(0))
priority = os.getpriority(os.PRIO_PROCESS, 0)
address_space = resource.getrlimit(resource.RLIMIT_AS)
deadline = float(os.environ['FORGE_PGO_ADMISSION_DEADLINE_UNIX'])
now = time.time()
if affinity != {0, 1, 2, 3}:
    raise SystemExit('PGO LINUX GUARD STOP: affinity readback is not exactly CPUs0-3')
if priority != 19:
    raise SystemExit('PGO LINUX GUARD STOP: priority readback is not nice19')
if address_space != (cap, cap):
    raise SystemExit('PGO LINUX GUARD STOP: soft/hard RLIMIT_AS readback is not 3GiB')
if not math.isfinite(deadline) or not now < deadline <= now + 2580:
    raise SystemExit('PGO LINUX GUARD STOP: deadline expired, invalid, or exceeds43minutes')
print(json.dumps({'linux_guard': 'READBACK_PASS', 'cpus': sorted(affinity),
                  'nice': priority, 'rlimit_as_soft_hard': address_space,
                  'memory_scope': 'per-process address space; not aggregate job memory',
                  'admission_deadline_unix': deadline,
                  'linux_ctest_may_kill_owned_child_on_timeout': True}))
# END_FORGE_PGO_READBACK_PY
PGO_READBACK
export FORGE_PGO_REVIEWED_ENVELOPE=ACTIVE
if [[ ${1:-} == --guard-self-test ]]; then
  printf '%s\n' 'PGO Linux guard self-test PASS; no worker, GCC or chess engine invoked.'
  exit 0
fi
run_stamp=$(date -u +%Y%m%d_%H%M%S)
exec "$pgo_python" "$script_dir/forge_sol_pgo_worker_20261025.py" --platform linux \
  --phase all --source "$script_dir/forge_sol_lock_source_20261025" \
  --out "$script_dir/forge_sol_pgo_linux_run_$run_stamp" \
  --recipe "$script_dir/forge_sol_lock_pc_recipe_20261025.ps1" --cxx "${CXX:-g++}" "$@"
