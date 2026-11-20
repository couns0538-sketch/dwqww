#!/usr/bin/env bash
# honesty.sh EXE OUTPREFIX
# Fresh process per command. No setoption.
set -u
EXE=$1
OUT=$2
runone() {
  local cmd="$1" file="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$file"
}
runone "bench 11" "${OUT}_bench11.txt"
runone "bench 13" "${OUT}_bench13.txt"
runone "bench 16" "${OUT}_bench16.txt"
runone "go perft 5" "${OUT}_perft5.txt"
sha256sum "$EXE" > "${OUT}.sha256"
printf 'uci\nquit\n' | "$EXE" > "${OUT}_id.txt"
echo "exe $EXE" > "${OUT}.meta"
echo "sha256 $(cut -d' ' -f1 "${OUT}.sha256")" >> "${OUT}.meta"
echo "id $(grep '^id name ' "${OUT}_id.txt" | head -n 1)" >> "${OUT}.meta"
echo "options none" >> "${OUT}.meta"
echo "commands: bench 11; bench 13; bench 16; go perft 5" >> "${OUT}.meta"
