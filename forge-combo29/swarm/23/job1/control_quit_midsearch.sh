#!/usr/bin/env bash
# control_quit_midsearch.sh : seat-19 broadcast 19-F12 control for MY harnesses.
# Question: can a pipelined `go ... / quit` (or a closed stdin) fabricate a result in my runs?
# My perft harness reads stdout until the "nodes N" line and never sends quit mid-run.
# This script proves that (a) the fabricated-bestmove fault is real on SEARCHES, and
# (b) it does NOT fire on `go perft`, because perft is synchronous (its output is complete
# before the next command is read).
set -u
EXE="${1:-$HOME/build/forge}"
show() { grep -E "info depth|bestmove|^nodes" | tail -3; }

echo "== meta"
echo "exe=$EXE"; sha256sum "$EXE"; "$EXE" <<< "uci
quit" | grep "^id name"

echo
echo "== A. SEARCH: go depth 12 + immediate quit  (broadcast: expect fabricated bestmove, no info lines)"
printf 'uci\nisready\nposition startpos\ngo depth 12\nquit\n' | timeout 30 "$EXE" | show
echo "-- exit=$?"

echo
echo "== B. SEARCH: go depth 12 + quit after 2 s   (broadcast: expect a real bestmove)"
( printf 'uci\nisready\nposition startpos\ngo depth 12\n'; sleep 2; printf 'quit\n' ) | timeout 30 "$EXE" | show

echo
echo "== C. PERFT: go perft 4 + immediate quit  (my harness's shape; expect complete nodes line)"
printf 'uci\nisready\nposition startpos\ngo perft 4\nquit\n' | timeout 60 "$EXE" | show

echo
echo "== D. PERFT: go perft 5 + immediate quit"
printf 'uci\nisready\nposition startpos\ngo perft 5\nquit\n' | timeout 60 "$EXE" | show

echo
echo "== E. PERFT: stdin closed (EOF) right after go perft 4"
printf 'uci\nisready\nposition startpos\ngo perft 4\n' | timeout 60 "$EXE" | show

echo
echo "== F. how many bestmove lines does a perft run emit at all? (expect 0)"
printf 'uci\nisready\nposition startpos\ngo perft 3\n' | timeout 30 "$EXE" | grep -c bestmove
