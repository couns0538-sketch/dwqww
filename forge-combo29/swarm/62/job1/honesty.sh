#!/usr/bin/env bash
# Honesty check: four pinned numbers, one fresh process per line.
# Usage: bash honesty.sh <path-to-forge> <outdir>
set -u
EXE="${1:?exe}"
OUT="${2:?outdir}"
mkdir -p "$OUT"
sha256sum "$EXE" > "$OUT/exe.sha256"
echo "EXE=$EXE" > "$OUT/exe.meta"
"$EXE" name 2>/dev/null | head -2 >> "$OUT/exe.meta"

run_bench() {
  local n="$1"
  { echo uci; echo isready; echo "bench $n"; echo quit; } > "$OUT/in_bench$n.txt"
  timeout 300 "$EXE" < "$OUT/in_bench$n.txt" > "$OUT/raw_bench$n.txt" 2>&1
  echo "rc=$?" >> "$OUT/raw_bench$n.txt"
}

run_perft() {
  { echo uci; echo isready; echo "go perft 5"; echo quit; } > "$OUT/in_perft5.txt"
  timeout 300 "$EXE" < "$OUT/in_perft5.txt" > "$OUT/raw_perft5.txt" 2>&1
  echo "rc=$?" >> "$OUT/raw_perft5.txt"
}

run_bench 11
run_bench 13
run_bench 16
run_perft

{
  echo "bench 11 nodes: $(grep -oE 'bench depth 11 nodes [0-9]+' "$OUT/raw_bench11.txt" | tail -1)"
  echo "bench 13 nodes: $(grep -oE 'bench depth 13 nodes [0-9]+' "$OUT/raw_bench13.txt" | tail -1)"
  echo "bench 16 nodes: $(grep -oE 'bench depth 16 nodes [0-9]+' "$OUT/raw_bench16.txt" | tail -1)"
  echo "perft 5 nodes: $(grep -oE '^nodes [0-9]+' "$OUT/raw_perft5.txt" | tail -1)"
} | tee "$OUT/HONESTY.txt"
