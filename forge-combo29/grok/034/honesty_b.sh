#!/usr/bin/env bash
# Honesty check of exe B. One fresh process per line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE="${1:-/tmp/grok-build/base/forge}"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{sub(/^id name /,""); print; exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DIR/$name.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id name $ID"
    echo "command=$cmd"
    echo "options:"
  } > "$DIR/$name.meta"
}
run_one HONESTY_B_bench11 "bench 11"
run_one HONESTY_B_bench13 "bench 13"
run_one HONESTY_B_bench16 "bench 16"
run_one HONESTY_B_perft5 "go perft 5"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id name $ID"
  for name in HONESTY_B_bench11 HONESTY_B_bench13 HONESTY_B_bench16 HONESTY_B_perft5; do
    echo "===== $name ====="
    cat "$DIR/$name.txt"
  done
} > "$DIR/HONESTY_B.txt"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id name $ID"
  echo "command=bench 11; bench 13; bench 16; go perft 5"
  echo "options:"
  echo "parts=HONESTY_B_bench11 HONESTY_B_bench13 HONESTY_B_bench16 HONESTY_B_perft5"
} > "$DIR/HONESTY_B.meta"
echo "sha256=$SHA"
echo "id=$ID"
grep -H "nodes" "$DIR"/HONESTY_B_bench11.txt "$DIR"/HONESTY_B_bench13.txt "$DIR"/HONESTY_B_bench16.txt
grep -E "^nodes " "$DIR"/HONESTY_B_perft5.txt
