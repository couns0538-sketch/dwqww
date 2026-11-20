#!/usr/bin/env bash
# Honesty check of exe P. One fresh process per line. No setoption.
set -u
S=$(cat "$HOME/grok_seat.txt")
REPO=$(cat "$HOME/grok_repo.txt")
DEST="$REPO/forge-combo29/grok/$S"
EXE=/tmp/forge-build/work/forge
SHA=$(sha256sum "$EXE" | awk 'NR==1{print $1}')
printf 'uci\nquit\n' | "$EXE" > "$DEST/uci_p.txt"
ID=$(awk -F 'id name ' '/^id name /{print $2; exit}' "$DEST/uci_p.txt")
write_meta() {
  local stem="$1"
  {
    echo "started: $EXE"
    echo "sha256: $SHA"
    echo "id name: $ID"
    echo "option lines sent:"
  } > "$DEST/${stem}.meta"
}
run_one() {
  local stem="$1"
  local cmd="$2"
  write_meta "$stem"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DEST/${stem}.txt"
}
run_one bench11_p "bench 11"
run_one bench13_p "bench 13"
run_one bench16_p "bench 16"
run_one perft5_p "go perft 5"
{
  echo "exe P honesty, no setoption"
  echo "bench 11: $(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$DEST/bench11_p.txt" | tail -n 1)"
  echo "bench 13: $(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$DEST/bench13_p.txt" | tail -n 1)"
  echo "bench 16: $(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$DEST/bench16_p.txt" | tail -n 1)"
  echo "perft 5: $(awk '/^nodes /{print $2}' "$DEST/perft5_p.txt" | tail -n 1)"
  echo "expected: 312866 862329 3024920 4865609"
} > "$DEST/HONESTY_P.txt"
cat "$DEST/HONESTY_P.txt"
echo "--- IdeaS10 lines from uci_p.txt ---"
grep -n 'IdeaS10' "$DEST/uci_p.txt"
