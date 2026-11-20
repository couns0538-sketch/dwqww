#!/usr/bin/env bash
# Honesty check of exe P. Fresh process per line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE="${1:-/tmp/forge-p/forge}"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{sub(/^id name /,""); print; exit}')
run_one() {
  local tag="$1"
  local cmd="$2"
  local raw="$OUT/honesty_p_${tag}.txt"
  local meta="$OUT/honesty_p_${tag}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  {
    echo "exe $EXE"
    echo "sha256 $SHA"
    echo "id name $IDNAME"
    echo "options none"
    echo "command $cmd"
  } > "$meta"
  echo "WROTE $raw"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
{
  echo "exe $EXE"
  echo "sha256 $SHA"
  echo "id name $IDNAME"
  echo "---- bench 11 ----"
  cat "$OUT/honesty_p_bench11.txt"
  echo "---- bench 13 ----"
  cat "$OUT/honesty_p_bench13.txt"
  echo "---- bench 16 ----"
  cat "$OUT/honesty_p_bench16.txt"
  echo "---- go perft 5 ----"
  cat "$OUT/honesty_p_perft5.txt"
} > "$OUT/HONESTY_P.txt"
echo "HONESTY_P written"
