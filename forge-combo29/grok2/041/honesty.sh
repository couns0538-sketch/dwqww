#!/usr/bin/env bash
# honesty.sh EXE TAG OUTDIR
# Fresh process per line. No setoption. Raw stdout saved. Meta beside each output.
set -u
EXE="$1"
TAG="$2"
OUTDIR="$3"
sha=$(sha256sum "$EXE" | awk '{print $1}')
idline=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{print; exit}')
run_one() {
  local name="$1" cmd="$2"
  local out="$OUTDIR/${TAG}_${name}.txt"
  local meta="$OUTDIR/${TAG}_${name}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$out"
  {
    echo "exe $EXE"
    echo "sha256 $sha"
    echo "$idline"
    echo "options none"
    echo "command $cmd"
  } > "$meta"
  echo "WROTE $out"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
