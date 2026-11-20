#!/usr/bin/env bash
# Honesty of the partner patch, rebuilt here. No setoption. My script, not theirs.
set -u
S=$(cat "$HOME/grok_seat.txt")
REPO=$(cat "$HOME/grok_repo.txt")
DEST="$REPO/forge-combo29/grok/$S"
EXE=/tmp/forge-build/partner/forge
SHA=$(sha256sum "$EXE" | awk 'NR==1{print $1}')
printf 'uci\nquit\n' | "$EXE" > "$DEST/partner_uci.txt"
ID=$(awk -F 'id name ' '/^id name /{print $2; exit}' "$DEST/partner_uci.txt")
run_one() {
  local stem="$1"
  local cmd="$2"
  {
    echo "started: $EXE"
    echo "sha256: $SHA"
    echo "id name: $ID"
    echo "option lines sent:"
  } > "$DEST/${stem}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DEST/${stem}.txt"
}
run_one partner_bench11 "bench 11"
run_one partner_bench13 "bench 13"
run_one partner_bench16 "bench 16"
run_one partner_perft5 "go perft 5"
{
  echo "partner rebuild honesty, no setoption"
  echo "bench 11: $(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$DEST/partner_bench11.txt" | tail -n 1)"
  echo "bench 13: $(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$DEST/partner_bench13.txt" | tail -n 1)"
  echo "bench 16: $(sed -n 's/.*nodes \([0-9][0-9]*\).*/\1/p' "$DEST/partner_bench16.txt" | tail -n 1)"
  echo "perft 5: $(awk '/^nodes /{print $2}' "$DEST/partner_perft5.txt" | tail -n 1)"
  echo "expected: 312866 862329 3024920 4865609"
} > "$DEST/partner_honesty.txt"
cat "$DEST/partner_honesty.txt"
