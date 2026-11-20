#!/usr/bin/env bash
# honesty.sh EXE TAG OUTDIR
# Fresh process per line. No setoption. Raw engine stdout only.
set -u
EXE="$1"
TAG="$2"
OUT="$3"
mkdir -p "$OUT"
sha=$(sha256sum "$EXE" | awk '{print $1}')
idname=$(printf 'uci\nquit\n' | "$EXE" | awk -F'id name ' '/^id name /{print substr($0, 9); exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  local raw="$OUT/${TAG}_${name}.txt"
  local meta="$OUT/${TAG}_${name}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  {
    echo "exe $EXE"
    echo "sha256 $sha"
    echo "id name $idname"
    echo "options none"
    echo "command $cmd"
  } > "$meta"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
echo "honesty $TAG done id=$idname"
