#!/usr/bin/env bash
# ep_pin_engine.sh : the real ep-pin test — send the ep FEN VERBATIM and read the engine's perft 1 move list.
# python-chess drops the ep square from fen() when no ep capture is legal, so a perft count alone cannot
# tell whether the ENGINE accepted the ep field and correctly refused the pinned capture. This does.
set -u
EXE="${1:-$HOME/build/forge}"
echo "exe=$EXE"
sha256sum "$EXE"
"$EXE" <<< "uci
quit" | grep "^id name"

probe() { # name fen  -> engine perft 1 moves, and python-chess's legal moves
  local name="$1" fen="$2"
  echo
  echo "== $name"
  echo "FEN: $fen"
  echo "-- engine (position fen + isready must not answer 'invalid FEN'):"
  printf 'uci\nisready\nucinewgame\nisready\nposition fen %s\nisready\ngo perft 1\nquit\n' "$fen" \
    | timeout 30 "$EXE" | grep -vE "^(option|id|uciok)" | sed 's/^/   engine: /'
  echo "-- python-chess legal moves:"
  PYTHONPATH=/agent/repos/dwqww/forge-combo29/swarm/23/job1 python3 - "$fen" <<'PY'
import sys, chess
fen = sys.argv[1]
b = chess.Board(fen)
print("   ep_square:", chess.square_name(b.ep_square) if b.ep_square is not None else None)
print("   legal:", " ".join(sorted(m.uci() for m in b.legal_moves)))
for m in b.generate_pseudo_legal_ep():
    print("   pseudo-legal ep %s is %s" % (m.uci(), "LEGAL" if m in b.legal_moves else "ILLEGAL (exposes king)"))
PY
}

probe "rank_pin_white"  "8/8/8/KPp4r/8/8/8/7k w - c6 0 1"
probe "rank_pin_black"  "8/8/8/8/kpP4R/8/8/7K b - c3 0 1"
probe "rank_pin_middle" "8/8/8/r2PpK2/8/8/8/7k w - e6 0 1"
echo
echo "== CONTROL (no pin, the ep capture IS legal and must appear in both lists)"
probe "control_no_pin"  "8/8/8/KPp4n/8/8/8/7k w - c6 0 1"
