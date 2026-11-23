PROPOSAL A1: Add an exact training-row round trip, including the final unplayed best move, to P3b before choosing the compact game record for transfer.

KIND: test

EVIDENCE: `source/src/uci.cpp:539–552` records the pre-move FEN, side-to-move score and best move before checking for a low-score draw. Lines 573–576 append to the played move list only after that decision. Lines 581–607 emit the two lists separately. On Astra's Linux build (GCC 14.2.0, AVX-512, r67 net), run this from the checkout root:

```sh
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -Isource/include source/src/*.cpp -o /tmp/forge-astra
{
  sed 's|<the full path of the net file forge65_r0067.fnn3>|loop/forge65_r0067.fnn3|' loop/LOOP_OPTIONS.txt
  printf '%s\n' isready ucinewgame 'position startpos' 'selfgame softnodes 2000 writeminply 0 drawply 0 drawscore 30000 drawcount 1 evallimit 30000 maxply 2' quit
} | /tmp/forge-astra
```

Raw local output:

```text
sg 0 24 e2e4 rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
sgend result 0 reason drawadj plies 0 run 1 searches 1 nodes 2993 fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 moves
```

One training row and zero played moves is correct for this fixture. A checksum can certify delivery of an incomplete encoding. The private codec has not been inspected here.

COST: Minutes on one CPU worker and zero GPU hours. This extends the planned transfer rehearsal and needs no match.

HOW IT IS JUDGED: Feed this fixture through the actual encoder, transfer, decoder and production after-game/filter pipeline. Require equality of every ordered raw row (ply, all six FEN fields, score from the side to move, best move), game result/reason and downstream accepted rows against the canonical original. Include normal production games and a draw-adjudicated game with a kept terminal row. Delete only the unplayed best move in a test copy, recompute the transport checksum, and require the semantic comparison to reject it. Use verified compact records on pass, lossless compressed canonical rows on failure until repaired.

WHAT WOULD CHANGE MY MIND: An existing round-trip test and its raw result proving this exact case and rejecting the deletion would satisfy the item immediately.
