#!/usr/bin/env bash
# honesty.sh EXE TAG OUTDIR
# Fresh process per line. No setoption. Raw stdout+stderr saved.
set -u
EXE="$1"
TAG="$2"
OUTDIR="$3"
sha=$(sha256sum "$EXE" | awk '{print $1}')
idname=$(printf 'uci\nquit\n' | "$EXE" | awk -F 'id name ' '/^id name /{print substr($0,9); exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  local out="$OUTDIR/honesty_${TAG}_${name}.txt"
  local meta="$OUTDIR/honesty_${TAG}_${name}.meta"
  printf '%s\n' "$cmd" | "$EXE" > "$out" 2>&1
  {
    echo "exe: $EXE"
    echo "sha256: $sha"
    echo "id name: $idname"
    echo "command: $cmd"
    echo "option lines sent: none"
  } > "$meta"
  echo "wrote $out"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
echo "id name probe: $idname"
echo "exe sha256: $sha"
