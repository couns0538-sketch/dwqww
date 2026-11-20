#!/usr/bin/env bash
# honesty.sh EXE TAG OUTDIR
# Fresh process per line. No setoption. Raw stdout saved beside a .meta file.
set -u
EXE=$(readlink -f "$1")
TAG=$2
OUT=$3
mkdir -p "$OUT"
sha=$(sha256sum "$EXE" | awk '{print $1}')
idline=$(printf 'uci\nquit\n' | "$EXE" | grep '^id name ' | head -n 1)
run_one() {
  local name="$1" cmd="$2"
  local raw="$OUT/honesty_${TAG}_${name}.txt"
  local meta="$OUT/honesty_${TAG}_${name}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  {
    echo "exe: $EXE"
    echo "sha256: $sha"
    echo "id name: ${idline#id name }"
    echo "options sent:"
    echo "measured stdin: ${cmd}"
    echo "then: quit"
    echo "id name source: separate uci handshake of this same exe; the measured process was not sent uci or any setoption"
  } > "$meta"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
echo "honesty $TAG done"
