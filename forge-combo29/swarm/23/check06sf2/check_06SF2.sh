#!/usr/bin/env bash
# check_06SF2.sh : independent check of swarm seat 06's S-F2
#   "a FEN whose ep square is unreachable is REFUSED with
#    `info string invalid FEN: inconsistent en-passant square`"
# Written by me from the finding's statement. No engine source is read: only the engine's own answers.
# A refusal is judged by the engine's line, and the REFUSAL IS PROVEN to have taken effect by the position
# the engine then holds (go perft 1), not by the wording alone — a line can be printed and ignored.
set -u
EXE="${1:-$HOME/build/forge}"
OUT="${2:-$HOME/check06sf2}"
mkdir -p "$OUT"
{
  echo "== meta"; echo "exe=$EXE"; sha256sum "$EXE"
  "$EXE" <<< "uci
quit" | grep "^id name"
  echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$OUT/meta.txt"

# probe NAME FEN : send a KNOWN position first, then the test FEN, then perft 1.
# If the test FEN is refused, the engine keeps the known position -> perft 1 = 20 (startpos).
# If it is accepted, perft 1 is that board's own count.
probe() {
  local name="$1" fen="$2"; shift 2
  local in="$OUT/$name.in" out="$OUT/$name.out"
  {
    echo uci; echo isready; echo ucinewgame; echo isready
    echo "position startpos"; echo isready
    echo "position fen $fen"; echo isready
    echo "go perft 1"; echo quit
  } > "$in"
  "$EXE" < "$in" > "$out" 2>&1
  local refusal nodes
  refusal=$(grep -c "invalid FEN" "$out")
  nodes=$(grep -E "^nodes " "$out" | tail -1 | awk '{print $2}')
  printf '%-34s invalid_FEN_lines=%s perft1_nodes=%-4s %s\n' "$name" "$refusal" "${nodes:-?}" \
    "$([ "$nodes" = "20" ] && echo 'KEPT startpos' || echo 'accepted (own board)')"
}

echo
echo "== the finding's three refusal cases (unreachable / inconsistent ep square)"
probe "ep_wrong_rank"      "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1"
probe "ep_origin_occupied" "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e3 0 1"
probe "ep_no_pawn"         "4k3/8/8/8/8/8/8/4K3 w - d6 0 1"

echo
echo "== CONTROLS: a legal ep FEN must be ACCEPTED (and give a count != 20)"
probe "control_ep_legal"   "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"
probe "control_no_ep"      "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

echo
echo "== what python-chess says about each of these FENs (independent opinion, not the referee)"
PYTHONPATH=/agent/repos/dwqww/forge-combo29/swarm/23/job1 python3 - "$OUT" <<'PY'
import sys, glob
import chess
for path in sorted(glob.glob(sys.argv[1] + "/*.in")):
    name = path.rsplit("/", 1)[-1][:-3]
    fen = [l for l in open(path) if l.startswith("position fen ")][0][13:].strip()
    b = chess.Board(fen)
    print("   %-34s python_valid=%-5s ep_square=%s" % (name, b.is_valid(),
          chess.square_name(b.ep_square) if b.ep_square is not None else None))
PY
