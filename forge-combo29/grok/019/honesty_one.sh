#!/usr/bin/env bash
# Honesty check. Usage: honesty_one.sh EXE PREFIX
# One fresh process per line. No setoption.
set -u
EXE="$1"
PREFIX="$2"
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
cd "$REPO"
DIR="forge-combo29/grok/$S"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{print; exit}')
write_meta() {
  local out="$1"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDNAME"
    echo "options_sent:"
    echo "(none)"
  } > "${out}.meta"
}
run_one() {
  local name="$1"
  local cmd="$2"
  local out="$DIR/${PREFIX}_${name}"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$out"
  write_meta "$out"
  echo "WROTE $out"
}
run_one bench11.txt "bench 11"
run_one bench13.txt "bench 13"
run_one bench16.txt "bench 16"
run_one perft5.txt "go perft 5"
