#!/usr/bin/env bash
# honesty.sh EXE LABEL OUTDIR
# Fresh process per line. No setoption. Raw stdout saved. Meta beside it.
set -u
EXE="$1"
LABEL="$2"
OUT="$3"
mkdir -p "$OUT"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{sub(/^id name /,""); print; exit}')
run_one() {
  local cmd="$1" tag="$2"
  local raw="$OUT/honesty_${LABEL}_${tag}.txt"
  local meta="$OUT/honesty_${LABEL}_${tag}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  {
    echo "exe: $EXE"
    echo "sha256: $SHA"
    echo "id name: $ID"
    echo "command: $cmd"
    echo "options: none"
    echo "id-name-probe: separate process, uci then quit, same exe"
  } > "$meta"
  echo "WROTE $raw"
}
run_one "bench 11" "bench11"
run_one "bench 13" "bench13"
run_one "bench 16" "bench16"
run_one "go perft 5" "perft5"
echo "---- $LABEL nodes ----"
grep -H -E 'nodes ' "$OUT"/honesty_${LABEL}_*.txt
