#!/usr/bin/env bash
# Honesty check of the partner build. One fresh process per line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE="/agent/repos/partner/forge-combo29/build/forge"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{sub(/^id name /,""); print; exit}')

run_one() {
  local name="$1"
  local cmds="$2"
  printf '%s\nquit\n' "$cmds" | "$EXE" > "$OUT/${name}.txt"
  {
    echo "exe $EXE"
    echo "sha256 $SHA"
    echo "id name $ID"
    echo "command:"
    printf '%s\n' "$cmds"
    echo "options: none"
  } > "$OUT/${name}.meta"
}

run_one partner_bench11 "bench 11"
run_one partner_bench13 "bench 13"
run_one partner_bench16 "bench 16"
run_one partner_perft5 "go perft 5"
{
  echo "exe $EXE"
  echo "sha256 $SHA"
  echo "id name $ID"
  echo "---- bench 11 ----"
  cat "$OUT/partner_bench11.txt"
  echo "---- bench 13 ----"
  cat "$OUT/partner_bench13.txt"
  echo "---- bench 16 ----"
  cat "$OUT/partner_bench16.txt"
  echo "---- perft 5 ----"
  cat "$OUT/partner_perft5.txt"
} > "$OUT/HONESTY_PARTNER.txt"
