#!/usr/bin/env bash
# check_30F6.sh : independent check of swarm 30's finding 30-F6
#   "`ucinewgame` resets the board to the start position, so `position ...` then `ucinewgame`
#    before `go` searches the START POSITION, not the position it set."
# I wrote this harness from the finding's statement only; I did not copy seat 30's script.
# Discrimination is by perft 1 node count, which differs per position (20 startpos, 30 Ruy Lopez, 28 another).
set -u
EXE="${1:-$HOME/build/forge}"
OUT="${2:-/tmp/check30f6}"
mkdir -p "$OUT"
{
  echo "== meta"
  echo "exe=$EXE"
  sha256sum "$EXE"
  "$EXE" <<< "uci
quit" | grep "^id name"
  echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$OUT/meta.txt"

pos() { # name  "commands..."
  local name="$1"; shift
  printf '%s\n' "$@" > "$OUT/$name.in"
  # every harness run from its file
  "$EXE" < "$OUT/$name.in" > "$OUT/$name.out" 2>&1
  local n
  n=$(grep -E "^nodes " "$OUT/$name.out" | tail -1 | awk '{print $2}')
  printf '%-42s nodes=%s\n' "$name" "${n:-MISSING}"
}

RYUY = 2>/dev/null || true
RUY="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"

echo | tee -a "$OUT/meta.txt"
echo "== A. reference: what each position answers WITHOUT ucinewgame"
pos "A1_startpos"          "uci" "isready" "position startpos" "isready" "go perft 1" "quit"
pos "A2_ruy"               "uci" "isready" "position fen $RUY" "isready" "go perft 1" "quit"

echo
echo "== B. the finding: position THEN ucinewgame"
pos "B1_pos_then_ucinewgame" "uci" "isready" "position fen $RUY" "ucinewgame" "isready" "go perft 1" "quit"

echo
echo "== C. the safe order: ucinewgame THEN position (what my harness does)"
pos "C1_ucinewgame_then_pos" "uci" "isready" "ucinewgame" "position fen $RUY" "isready" "go perft 1" "quit"

echo
echo "== D. second position after a first one, no ucinewgame between (my harness's real shape)"
pos "D1_two_positions"      "uci" "isready" "ucinewgame" "position fen $RUY" "isready" "go perft 1" "position startpos" "isready" "go perft 1" "quit"
