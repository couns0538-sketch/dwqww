#!/usr/bin/env bash
# quitcut.sh — what bestmove does the engine emit when `quit` arrives while a search runs?
# For each case: the FEN, the immediate-quit bestmove, and the same search given time (the real bestmove).
set -u
EXE="${1:?exe}"
run_cut() { # fen or "startpos", go-cmd
  local pos="$1" go="$2"
  { echo uci; echo isready; echo ucinewgame; echo isready; echo "position $pos"; echo "$go"; echo quit; } \
    | timeout 60 "$EXE" 2>/dev/null | grep '^bestmove' | tail -1
}
run_full() {
  local pos="$1" go="$2"
  { echo uci; echo isready; echo ucinewgame; echo isready; echo "position $pos"; echo "$go"; sleep 3; echo quit; } \
    | timeout 60 "$EXE" 2>/dev/null | grep '^bestmove' | tail -1
}
echo "exe=$EXE sha256=$(sha256sum "$EXE" | cut -d' ' -f1)"
echo
printf '%-44s %-10s %-16s %s\n' "position" "go" "quit-immediately" "given 3s"
for pos in "startpos" "startpos moves e2e4" "startpos moves d2d4 d7d5" \
           "fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1" \
           "fen 8/8/8/8/8/8/8/K6k w - - 0 1" ; do
  for go in "go depth 10" "go infinite"; do
    a=$(run_cut "$pos" "$go"); b=$(run_full "$pos" "$go")
    printf '%-44s %-10s %-16s %s\n' "$pos" "$go" "${a:-<none>}" "${b:-<none>}"
  done
done
