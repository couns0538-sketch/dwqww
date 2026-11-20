#!/usr/bin/env bash
# honesty.sh EXE OUTDIR TAG
# One fresh engine process per line. No setoption. Raw stdout saved.
set -u
EXE=$1
OUT=$2
TAG=$3
mkdir -p "$OUT"
run() {
  local name=$1
  local cmd=$2
  local f="$OUT/${TAG}_${name}.txt"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$f"
  echo "wrote $f"
}
run bench11 "bench 11"
run bench13 "bench 13"
run bench16 "bench 16"
run perft5 "go perft 5"
# id name from a separate process of the same exe. Not sent before bench or perft.
printf 'uci\nquit\n' | "$EXE" > "$OUT/${TAG}_idname.txt"
sha=$(sha256sum "$EXE" | awk '{print $1}')
id=$(grep -m1 '^id name ' "$OUT/${TAG}_idname.txt" || true)
{
  echo "exe: $EXE"
  echo "sha256: $sha"
  echo "id_name_line: $id"
  echo "options_sent:"
  echo "(none)"
  echo "commands: bench 11; bench 13; bench 16; go perft 5"
  echo "note: each command was a fresh process; uci was a fifth process for id name only"
} > "$OUT/${TAG}_honesty.meta"
echo "wrote $OUT/${TAG}_honesty.meta"
