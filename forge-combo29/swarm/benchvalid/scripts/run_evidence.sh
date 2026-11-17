#!/usr/bin/env bash
# Reproduce every file in evidence/. Each step writes the JSON/text it names.
#   export BENCHVALID_WORK=/tmp/bv && scripts/build_all.sh && scripts/run_evidence.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EV="$HERE/../evidence"
mkdir -p "$EV"
export BENCHVALID_WORK="${BENCHVALID_WORK:-$PWD/benchvalid-work}"
PY=python3

echo "[1/9] four pins, argv trap"
$PY "$HERE/pins.py" > "$EV/pins_base.json"
$PY - "$EV/argv_trap.json" <<'EOF'
import json, subprocess, sys
exe = __import__("os").path.join(__import__("os").environ["BENCHVALID_WORK"], "build", "forge")
rows = []
for arg in ("bench 11", "bench 13", "bench 16", "bench 99"):
    p = subprocess.run([exe] + arg.split(), capture_output=True, text=True, timeout=600)
    rows.append({"argv": arg, "exit": p.returncode,
                 "stdout_bytes": len(p.stdout), "stderr_bytes": len(p.stderr), "stdout": p.stdout})
json.dump({"trap": "bench N on argv prints nothing and exits 0",
           "exe": exe, "rows": rows,
           "all_silent": all(r["stdout_bytes"] == 0 for r in rows),
           "all_exit_zero": all(r["exit"] == 0 for r in rows)}, open(sys.argv[1], "w"), indent=2)
EOF

echo "[2/9] per-position bench detail"
"$BENCHVALID_WORK/bin/benchprobe" 13 > "$EV/bench_positions_d13.txt"
"$BENCHVALID_WORK/bin/benchprobe" 11 > "$EV/bench_positions_d11.txt"

echo "[3/9] independence: forward / reverse / noclear / fresh"
for m in forward reverse noclear fresh; do
  echo "=== $m"
  "$BENCHVALID_WORK/bin/orderprobe" 13 "$m"
done > "$EV/order_independence.txt"

echo "[4/9] coverage of the pin workload"
$PY "$HERE/coverage.py" "$BENCHVALID_WORK/cov" bench13 "$HERE/cmd_bench13.txt" > "$EV/coverage_bench13.json"
$PY "$HERE/bench_coverage.py" > "$EV/coverage_workloads.json"

echo "[5/9] the Hash trap"
$PY "$HERE/hash_trap.py" > "$EV/hash_trap.json"

echo "[6/9] fixed-depth repeatability under go"
$PY "$HERE/go_repeatability.py" > "$EV/go_repeatability.json"

echo "[7/9] sensitivity: should-move and should-not-move mutants"
$PY "$HERE/sensitivity.py" > "$EV/sensitivity.json"

echo "[8/9] blind-spot mutants"
$PY "$HERE/blindspots.py" > "$EV/blindspots.json"

echo "[9/9] gate, its self-check, and G2's responsiveness"
$PY "$HERE/gate.py" > "$EV/gate_base.txt" || true
$PY "$HERE/gate_selfcheck.py" > "$EV/gate_selfcheck.json"
$PY "$HERE/g2_can_move.py" > "$EV/g2_can_move.json"

echo "[10/10] the document's own figures, and the plants that prove the checks fire"
$PY "$HERE/verify_figures.py" | tee "$EV/verify_figures.txt"
bash "$HERE/plant_check.sh" | tee "$EV/plant_check.txt"

echo "evidence written to $EV"
