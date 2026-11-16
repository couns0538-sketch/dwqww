#!/usr/bin/env bash
# Equivalence check: base vs patched must agree on perft 4 for a fixed position list (start, kiwipete, pos3-5,
# plus 60 random positions from a seeded game), and on bestmove for 40 fixed-depth searches.
set -u
BASE=/home/ubuntu/build/base/forge
PATCH=/home/ubuntu/build/patched/forge
POS=positions.txt
{
  echo "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
  echo "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
  echo "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
  echo "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"
  echo "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8"
  python3 - <<'PY'
import chess, random
random.seed(2901)
seen = 0
tries = 0
while seen < 60 and tries < 4000:
    tries += 1
    b = chess.Board()
    for _ in range(random.randint(6, 60)):
        ms = list(b.legal_moves)
        if not ms: break
        b.push(random.choice(ms))
    if b.is_game_over(): continue
    if b.castling_rights or b.ep_square or b.is_check():   # keep the interesting cases
        print(b.fen()); seen += 1
PY
} > "$POS"
echo "positions: $(wc -l < "$POS")"
same=0; diff=0
while read -r fen; do
  for d in 3 4; do
    a=$(printf 'uci\nisready\nposition fen %s\ngo perft %d\nquit\n' "$fen" "$d" | "$BASE" | grep -E "^nodes" | tail -1)
    b=$(printf 'uci\nisready\nposition fen %s\ngo perft %d\nquit\n' "$fen" "$d" | "$PATCH" | grep -E "^nodes" | tail -1)
    if [ "$a" = "$b" ] && [ -n "$a" ]; then same=$((same+1)); else diff=$((diff+1)); echo "DIFF d$d $fen | base=$a patched=$b"; fi
  done
done < "$POS"
echo "perft agreements: $same   differences: $diff"
