#!/usr/bin/env bash
# Honesty check on exe B. Fresh process per line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
cd "$REPO"
EXE=/agent/repos/base/forge-combo29/build-rel/forge
OUT="$REPO/forge-combo29/grok/$S"
mkdir -p "$OUT"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{sub(/^id name /,""); print; exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$OUT/${name}.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDNAME"
    echo "id_name_source=separate uci/quit of the same exe path, not this process"
    echo "options_sent=none"
    echo "command=$cmd"
  } > "$OUT/${name}.meta"
}
run_one honesty_b_bench11 "bench 11"
run_one honesty_b_bench13 "bench 13"
run_one honesty_b_bench16 "bench 16"
run_one honesty_b_perft5 "go perft 5"
echo "HONESTY_B_RAN exe=$EXE sha=$SHA id=$IDNAME"
