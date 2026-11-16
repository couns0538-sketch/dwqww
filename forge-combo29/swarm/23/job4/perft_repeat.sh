#!/usr/bin/env bash
# perft_repeat.sh : seat 10's rule applied to perft — does `go perft` give the same count twice in a row
# in ONE process, with and without anything between the two runs?
# If yes, every perft table of mine (one process per file, many positions in it) stands.
# If no, my tables would be measuring warm state and would have to be re-run cold per position.
set -u
EXE="${1:-$HOME/build/forge}"
case_run() { # name, line1, line2, line3, line4, line5, line6
  local name="$1"; shift
  printf '%s\n' "$@" > "/tmp/pr_$name.in"
  "$EXE" < "/tmp/pr_$name.in" > "/tmp/pr_$name.out" 2>&1
  echo "== $name"
  grep -E "^nodes |^info depth" "/tmp/pr_$name.out" | sed 's/^/   /'
}

echo "exe=$EXE"
sha256sum "$EXE"
"$EXE" <<< "uci
quit" | grep "^id name"
echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

RYU="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"

echo
echo "== A. startpos, go perft 4 twice, nothing between (the requested one run, two lines)"
case_run "A_startpos_x2" "uci" "isready" "position startpos" "isready" "go perft 4" "go perft 4" "quit"

echo
echo "== B. startpos, go perft 5 twice (the depth my job 3 uses)"
case_run "B_startpos5_x2" "uci" "isready" "position startpos" "isready" "go perft 5" "go perft 5" "quit"

echo
echo "== C. a mid-game FEN, perft 4 twice (the shape of my engine_R runs: many positions, one process)"
case_run "C_fen_x2" "uci" "isready" "position fen $RYU" "isready" "go perft 4" "go perft 4" "quit"

echo
echo "== D. two DIFFERENT positions back to back, then the first one again (repeat across a position change)"
case_run "D_aba" "uci" "isready" "position fen $RYU" "isready" "go perft 4" "position startpos" "isready" "go perft 4" "position fen $RYU" "isready" "go perft 4" "quit"

echo
echo "== E. control: the seat-10 SEARCH effect, same shape, to show this harness CAN see warm state"
case_run "E_search_x2" "uci" "isready" "position startpos" "isready" "go depth 12" "go depth 12" "quit"
