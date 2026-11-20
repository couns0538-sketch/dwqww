#!/usr/bin/env bash
# honesty.sh EXE OUTPREFIX
# One fresh engine process per command. No setoption is sent.
set -u
EXE=$1
OUT=$2
mkdir -p "$(dirname "$OUT")"
run() {
  local name=$1
  shift
  printf '%s\n' "$@" quit | "$EXE" > "${OUT}_${name}.txt" 2>&1
}
run bench11 "bench 11"
run bench13 "bench 13"
run bench16 "bench 16"
run perft5 "go perft 5"
{
  echo "exe: $EXE"
  echo "sha256: $(sha256sum "$EXE" | awk '{print $1}')"
  echo "id name: $(printf 'uci\nquit\n' | "$EXE" | awk -F'id name ' '/^id name /{print $2; exit}')"
  echo "options: none"
  echo "commands: bench 11; bench 13; bench 16; go perft 5"
} > "${OUT}.meta"
echo "wrote ${OUT}_bench11.txt ${OUT}_bench13.txt ${OUT}_bench16.txt ${OUT}_perft5.txt ${OUT}.meta"
