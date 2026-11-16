#!/usr/bin/env bash
# S02 honesty check: bench 11, bench 13, bench 16, go perft 5 — a FRESH engine process per line,
# commands sent on stdin, raw stdout+stderr kept as text.
# usage: run_honesty.sh <exe> <outdir>
set -u
EXE="${1:-/agent/repos/base/forge-combo29/build/forge}"
OUT="${2:-.}"
mkdir -p "$OUT"
rm -f "$OUT"/bench11.txt "$OUT"/bench13.txt "$OUT"/bench16.txt "$OUT"/perft5.txt
{
  echo "exe $EXE"
  echo "sha256 $(sha256sum "$EXE" | cut -d' ' -f1)"
  echo "nm __asan_ count $(nm -C "$EXE" 2>/dev/null | grep -c __asan_)"
  echo "nm __ubsan_ count $(nm -C "$EXE" 2>/dev/null | grep -c __ubsan_)"
  echo "date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/env.txt"

run_one() { # name, stdin text
  local name="$1" text="$2"
  printf '%s' "$text" | "$EXE" > "$OUT/$name.txt" 2>&1
  echo "$name exit=$? $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT/exits.txt"
}

: > "$OUT/exits.txt"
run_one bench11 'bench 11
quit
'
run_one bench13 'bench 13
quit
'
run_one bench16 'bench 16
quit
'
run_one perft5 'position startpos
isready
go perft 5
quit
'
# the four numbers, straight out of the raw files
{
  echo "bench11 nodes: $(grep -o 'bench depth 11 nodes [0-9]*' "$OUT/bench11.txt" | awk '{print $5}')"
  echo "bench13 nodes: $(grep -o 'bench depth 13 nodes [0-9]*' "$OUT/bench13.txt" | awk '{print $5}')"
  echo "bench16 nodes: $(grep -o 'bench depth 16 nodes [0-9]*' "$OUT/bench16.txt" | awk '{print $5}')"
  echo "perft5 nodes:  $(grep -o '^nodes [0-9]*' "$OUT/perft5.txt" | awk '{print $2}')"
} | tee "$OUT/numbers.txt"

python3 - "$OUT/numbers.txt" <<'PY'
import sys, re
exp = {"bench11 nodes": 312866, "bench13 nodes": 862329, "bench16 nodes": 3024920, "perft5 nodes": 4865609}
bad = 0
for line in open(sys.argv[1]):
    k, v = line.split(":")
    k = k.strip(); v = v.strip()
    if k in exp:
        ok = (v == str(exp[k]))
        print(f"{'PASS' if ok else 'FAIL'} {k} got={v} want={exp[k]}")
        bad += (not ok)
print("HONESTY", "PASS" if bad == 0 else f"FAIL({bad})")
PY
