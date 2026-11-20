#!/usr/bin/env bash
# Honesty check for exe B. One fresh process per line. No setoption.
set -euo pipefail
EXE=/agent/repos/base/forge-combo29/build/forge
OUT=$(cd "$(dirname "$0")" && pwd)
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDLINE=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{print; exit}')
write_meta() {
  local name="$1"
  local cmds="$2"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDLINE"
    echo "commands=$cmds"
    echo "options=none"
  } > "$OUT/$name.meta"
}
printf 'bench 11\nquit\n' | "$EXE" > "$OUT/honesty_b_bench11.txt"
write_meta honesty_b_bench11 "bench 11"
printf 'bench 13\nquit\n' | "$EXE" > "$OUT/honesty_b_bench13.txt"
write_meta honesty_b_bench13 "bench 13"
printf 'bench 16\nquit\n' | "$EXE" > "$OUT/honesty_b_bench16.txt"
write_meta honesty_b_bench16 "bench 16"
printf 'position startpos\ngo perft 5\nquit\n' | "$EXE" > "$OUT/honesty_b_perft5.txt"
write_meta honesty_b_perft5 "position startpos; go perft 5"
echo "---- bench 11 ----"
grep -n nodes "$OUT/honesty_b_bench11.txt" | head
echo "---- bench 13 ----"
grep -n nodes "$OUT/honesty_b_bench13.txt" | head
echo "---- bench 16 ----"
grep -n nodes "$OUT/honesty_b_bench16.txt" | head
echo "---- perft ----"
grep -n nodes "$OUT/honesty_b_perft5.txt" | head
