#!/usr/bin/env bash
# Honesty check of exe B. One fresh process per line. No setoption.
set -eu
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE="/agent/repos/base/forge-combo29/build/forge"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk -F'\n' '/^id name /{print; exit}')
# The awk above prints the whole matching line because FS is newline by default
# when we use a simple pattern. Capture with grep instead if needed.
IDLINE=$(printf 'uci\nquit\n' | "$EXE" | grep -m1 '^id name ' || true)

run_one() {
  local tag="$1"
  local cmd="$2"
  local raw="$OUT/honesty_b_${tag}.txt"
  local meta="$OUT/honesty_b_${tag}.meta"
  # uci is not setoption. It is sent so the raw file contains id name.
  printf 'uci\n%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDLINE"
    echo "options_sent=none"
    echo "command=$cmd"
    echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$meta"
  echo "WROTE $raw"
  grep -E 'bench depth|nodes ' "$raw" | tail -n 3
}

run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
echo HONESTY_B_DONE
