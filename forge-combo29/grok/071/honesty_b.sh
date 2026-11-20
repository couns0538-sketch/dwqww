#!/usr/bin/env bash
# Honesty check of exe B: one fresh process per line, no setoption.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
EXE=/tmp/build-base/forge
cd "$DIR"
sha=$(sha256sum "$EXE" | awk '{print $1}')
idname=$(printf 'uci\nquit\n' | "$EXE" | sed -n 's/^id name //p' | head -1)
run_one() {
  local name="$1" cmd="$2"
  {
    echo "exe=$EXE"
    echo "sha256=$sha"
    echo "id_name=$idname"
    echo "command=$cmd"
    echo "options_sent=none"
  } > "$DIR/${name}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DIR/${name}.txt"
}
run_one honesty_b_bench11 "bench 11"
run_one honesty_b_bench13 "bench 13"
run_one honesty_b_bench16 "bench 16"
run_one honesty_b_perft5 "go perft 5"
python3 "$DIR/write_honesty_b.py"
