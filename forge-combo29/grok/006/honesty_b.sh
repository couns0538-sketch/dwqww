#!/usr/bin/env bash
# Fresh process per honesty line. No setoption.
set -u
EXE="$1"
OUT="$2"
sha=$(sha256sum "$EXE" | awk '{print $1}')
idname=$(printf 'uci\nquit\n' | "$EXE" | awk -F'\n' '/^id name /{sub(/^id name /,""); print; exit}')
run_one() {
  local name="$1" cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$OUT/${name}.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$sha"
    echo "id_name=$idname"
    echo "options_sent=none"
    echo "command=$cmd"
  } > "$OUT/${name}.meta"
}
run_one honesty_b_bench11 "bench 11"
run_one honesty_b_bench13 "bench 13"
run_one honesty_b_bench16 "bench 16"
run_one honesty_b_perft5 "go perft 5"
{
  echo "exe=$EXE"
  echo "sha256=$sha"
  echo "id_name=$idname"
  echo "bench11=$(grep -E 'bench depth 11 nodes ' "$OUT/honesty_b_bench11.txt")"
  echo "bench13=$(grep -E 'bench depth 13 nodes ' "$OUT/honesty_b_bench13.txt")"
  echo "bench16=$(grep -E 'bench depth 16 nodes ' "$OUT/honesty_b_bench16.txt")"
  echo "perft5=$(grep -E '^nodes ' "$OUT/honesty_b_perft5.txt")"
} > "$OUT/HONESTY_B.txt"
cat "$OUT/HONESTY_B.txt"
