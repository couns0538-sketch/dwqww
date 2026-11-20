#!/usr/bin/env bash
# Honesty check of exe B. One fresh process per line. No setoption.
set -u
S=$(cat "$HOME/grok_seat.txt")
REPO=$(cat "$HOME/grok_repo.txt")
DEST="$REPO/forge-combo29/grok/$S"
EXE=/tmp/forge-build/base/forge
SHA=$(sha256sum "$EXE" | awk 'NR==1{print $1}')
printf 'uci\nquit\n' | "$EXE" > "$DEST/uci_b.txt"
ID=$(awk -F 'id name ' '/^id name /{print $2; exit}' "$DEST/uci_b.txt")
write_meta() {
  local stem="$1"
  local sent="$2"
  {
    echo "started: $EXE"
    echo "sha256: $SHA"
    echo "id name: $ID"
    echo "option lines sent:"
    if [ -n "$sent" ]; then
      printf '%s\n' "$sent"
    fi
  } > "$DEST/${stem}.meta"
}
run_one() {
  local stem="$1"
  local cmd="$2"
  write_meta "$stem" ""
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DEST/${stem}.txt"
}
run_one bench11_b "bench 11"
run_one bench13_b "bench 13"
run_one bench16_b "bench 16"
run_one perft5_b "go perft 5"
{
  echo "exe B honesty"
  echo "bench 11: $(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$DEST/bench11_b.txt" | tail -n 1)"
  echo "bench 13: $(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$DEST/bench13_b.txt" | tail -n 1)"
  echo "bench 16: $(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$DEST/bench16_b.txt" | tail -n 1)"
  echo "perft 5: $(awk '/^nodes /{print $2}' "$DEST/perft5_b.txt" | tail -n 1)"
  echo "expected: 312866 862329 3024920 4865609"
} > "$DEST/HONESTY_B.txt"
cat "$DEST/HONESTY_B.txt"
