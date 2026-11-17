#!/usr/bin/env bash
# Reproduce every number in FINDINGS.md.
#
#   ./run_all.sh [path/to/forge]
#
# Writes JSON to ../evidence/ and the raw wire captures to ../evidence/wire/.
# Each stage prints its own counters; run_all does not summarise, so a stage that fails is visible
# rather than averaged away.  Order matters: the controls run BEFORE the thing they control.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EV="$(cd "$HERE/.." && pwd)/evidence"
mkdir -p "$EV/wire"
EXE="${1:-$(cd "$HERE/../../.." && pwd)/build/forge}"
PY=python3
rc=0

stage() {  # name, then the command
  local name="$1"; shift
  echo "=== $name"
  if ! "$@"; then echo "!!! $name FAILED"; rc=1; fi
}

[[ -x "$EXE" ]] || { echo "no such engine: $EXE  (run 00_build_and_pins.sh first)"; exit 2; }
echo "engine: $EXE"
# Build LABEL, not a security control: md5 so a reader can match this report to a binary that was
# described elsewhere, sha256 beside it for collision resistance. Nothing authenticates against it.
sha256sum "$EXE" | tee "$EV/wire/engine.sha256"
md5sum    "$EXE" | tee "$EV/wire/engine.md5"

# --- pins, the gate every other number depends on --------------------------------------------
stage "pins" bash -c '
  exe="'"$EXE"'"; out="'"$EV"'/wire/pins.txt"
  { printf "uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name UseNNUE value true\n"
    for d in 11 13 16; do printf "bench %s\n" "$d"; done
    printf "position startpos\ngo perft 5\n"; sleep 2; printf "quit\n"; } | "$exe" > "$out"
  python3 - "$out" "'"$EV"'/pins.json" <<PYEOF
import json, re, sys
txt = open(sys.argv[1]).read()
nodes = re.findall(r"info string bench depth \d+ nodes (\d+)", txt)
perft = re.findall(r"^nodes (\d+)", txt, re.M)
want = ["312866", "862329", "3024920"]
out = {"bench11": int(nodes[0]), "bench13": int(nodes[1]), "bench16": int(nodes[2]),
       "perft5": int(perft[-1]),
       "want": {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}}
out["all_match"] = all(out[k] == out["want"][k] for k in out["want"])
json.dump(out, open(sys.argv[2], "w"), indent=1)
print("pins:", {k: out[k] for k in out["want"]}, "match:", out["all_match"])
sys.exit(0 if out["all_match"] else 1)
PYEOF
'

# --- self-tests first: a checker whose failure has not been shown is not a checker ------------
stage "selftest" bash -c "$PY '$HERE/check_multipv.py' --selftest | tee '$EV/wire/selftest.txt'"
stage "wire control" bash -c "$PY '$HERE/wire_control.py' '$EXE' | tee '$EV/wire/wire_control.txt'"

# --- the six properties ----------------------------------------------------------------------
stage "structural + controls + agreement" "$PY" "$HERE/audit.py" "$EXE" \
      --positions 40 --depth 12 --json "$EV/audit.json"
stage "lint selftest" bash -c "$PY '$HERE/lint_scripts.py' --selftest"
stage "lint scripts" "$PY" "$HERE/lint_scripts.py"
stage "render selftest" bash -c "$PY '$HERE/render.py' --selftest"
stage "budget stability" "$PY" "$HERE/budget_stability.py" "$EXE" \
      --positions 40 --mpv 6 --repeats 3 --json "$EV/budget_stability.json"
stage "instability control" "$PY" "$HERE/instability.py" "$EXE" \
      --positions 40 --depth 12 --delta 4 --mpv 6 --json "$EV/instability.json"
stage "property 5 judge" "$PY" "$HERE/judge.py" "$EXE" \
      --positions 40 --depth 12 --judge-depth 16 --mpv 6 --json "$EV/judge.json"
stage "judge noise floor" "$PY" "$HERE/agreement.py" "$EXE" \
      --positions 12 --depth 12 --judge-depth 16 --mpv 6 --json "$EV/agreement.json"
stage "fast paths" "$PY" "$HERE/fastpaths.py" "$EXE" --json "$EV/fastpaths.json"

# --- the report's figures, checked against the JSON ------------------------------------------
cp "$EV/wire/selftest.txt" /dev/null 2>/dev/null || true
python3 - "$EV" <<'PYEOF'
import json, re, sys, os
ev = sys.argv[1]
selftxt = open(os.path.join(ev, "wire", "selftest.txt")).read()
m = re.search(r"selftest: (\d+) checks over (\d+) planted faults, (\d+) failures", selftxt)
json.dump({"checks": int(m.group(1)), "planted_faults": int(m.group(2)),
           "failures": int(m.group(3))}, open(os.path.join(ev, "selftest.json"), "w"), indent=1)
wtxt = open(os.path.join(ev, "wire", "wire_control.txt")).read()
m = re.search(r"wire control: (\d+) assertions, (\d+) blind, (\d+) captures already dirty", wtxt)
json.dump({"assertions": int(m.group(1)), "blind": int(m.group(2)),
           "captures_already_dirty": int(m.group(3))},
          open(os.path.join(ev, "wire_control.json"), "w"), indent=1)
print("selftest/wire counters lifted from their own output")
PYEOF
stage "render report" "$PY" "$HERE/render.py"
stage "report is committed and current" "$PY" "$HERE/render.py" --check

echo
if [[ "$rc" == 0 ]]; then echo "run_all: all stages passed"; else echo "run_all: AT LEAST ONE STAGE FAILED"; fi
exit $rc
