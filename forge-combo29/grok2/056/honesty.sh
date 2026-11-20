#!/usr/bin/env bash
# honesty.sh EXE TAG OUTDIR
# Fresh process per line. No setoption. Raw stdout+stderr saved beside a .meta file.
set -u
EXE="$1"
TAG="$2"
OUTDIR="$3"
mkdir -p "$OUTDIR"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{sub(/^id name /,""); print; exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  local out="$OUTDIR/honesty_${TAG}_${name}.txt"
  local meta="$OUTDIR/honesty_${TAG}_${name}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$out" 2>&1
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id name $ID"
    echo "command=$cmd"
    echo "options:"
  } > "$meta"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
echo "honesty $TAG done exe=$EXE sha256=$SHA id=$ID"
