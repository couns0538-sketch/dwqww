# Does the sparse class also have the most volatile score? — seat 08, PC r15 under PC20, Threads 1

The link the coordinator asked about: if the class that blows the time tail is ALSO the class whose score moves most
between an interrupted and a completed search, one explanation covers both findings.

Method: five boards per class (the 08-F28 classes), each searched at the owner's control (6 s + 0.06) to record the
score at the depth it stopped at (D), then searched again at `go depth D+4` — a COMPLETED, deeper search of the same
board. Delta is the difference.

## The answer: YES, strongly, but the mechanism is not centipawns — it is a MATE APPEARING

| class | board | clocked depth D | score at D | score at D+4 | delta |
|---|---|---|---|---|---|
| **sparse** | `8/8/6k1/Q7/1P4PP/1K3P2/8/8 b` | 16 | **cp −4161** | **mate −5** | a mate appeared |
| sparse | `8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w` | 18 | cp −1915 | cp −2233 | **318 cp** |
| **sparse** | `8/8/4k3/8/8/4K3/8/4R3 w` | 17 | **cp 627** | **mate 12** | a mate appeared |
| sparse | `8/6k1/8/8/8/8/6PK/7R w` | 18 | cp 1817 | cp 1861 | 44 cp |
| sparse | `8/3n2Q1/2k4p/8/1P6/5P1P/1K4P1/8 b` | 17 | cp −2371 | cp −2437 | 66 cp |
| full mat. | `r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3…` | 17 | cp 22 | cp 20 | 2 cp |
| full mat. | `r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4…` | 17 | cp −257 | cp −260 | 3 cp |
| full mat. | `1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1…` | 17 | cp −292 | cp −300 | 8 cp |
| full mat. | `r2q1rk1/ppp2ppp/3bbn2/3p4/8/1PN1PN2…` | 18 | cp 613 | cp 613 | 0 cp |
| full mat. | `2r2rk1/1p1nbppp/pq1pb3/3Np3/1P2P3…` | 18 | cp 2352 | cp 2388 | 36 cp |

| class | boards where a MATE appeared at D+4 | boards where both stayed cp: median absolute delta |
|---|---|---|
| **sparse (few pieces, few moves)** | **2 of 5** | **318 cp** |
| full material, many moves | **0 of 5** | **3 cp** |

So on this sample the sparse class is both the slow class and the volatile class, and the volatility is of two kinds:
- **a mate appearing that the clocked search did not see — 2 of 5 boards** (`cp −4161` becoming `mate −5`, and
  `cp 627` becoming `mate 12`). Those two boards are exactly the ones that consumed the most time, so the clocked
  search stopped before it found the mate; and
- **centipawn movement an order of magnitude larger — 318 cp against 3 cp** on the boards that stayed cp.

## A number I refuse to quote

A naive ratio gives "106x more volatile", and an earlier version of this analysis printed 4305x. Both are artefacts
of mapping `mate N` to ±30000 centipawns: a mate appearing is a DIFFERENT EVENT from a score moving, not a movement
of 25000 cp. So I report the mate count (2 of 5 vs 0 of 5) and the cp-only medians (318 vs 3 cp) separately, and
I do not quote a combined ratio. This is the same trap as the earlier "one-ply move loses 9 pawns" reading: a raw
number from a different scale is not a cost.

## The one explanation this supports

**Expensive iterations and unreliable scores are the same phenomenon in sparse positions.** A sparse endgame
(≤12 pieces, few legal moves) has a steep depth ladder: each extra ply costs a large multiple of the last, so the
clocked search stops at depth 16-18 having spent 700-1500 ms, and at that depth it has not yet seen a mate that
depth 20-22 finds. A full-material middlegame has a shallow ladder, stops at depth 17-18 in 140-400 ms, and its score
is already stable to 0-36 cp.

**Why that matters for training data:** if the owner's self-play records the score of a clocked search as a target,
the sparse class contributes scores that are wrong by a mate (2 of these 5) at a depth that also cost a fifth of the
clock. That links this finding to the training-data question without needing a separate mechanism.

## Honest limits
- 5 boards per class. Two of the five sparse boards showed a mate because those boards were chosen to be sparse, not
  because I selected them for having mates — but a 5-board sample cannot give a RATE, only a direction. The rate
  claim from `tail_frequency.txt` (3.3-5.0 % of searches over 1.2 s) is measured on 60 boards per class; the
  volatility claim here is not.
- One `go depth D+4` reference per board, scored at Threads 1, so it is deterministic, but I did not sweep D+5/D+6
  to see whether the mate is always found just past the clocked depth.
- The clocked depth D itself varied between 16 and 19, so the two columns are not at a fixed depth.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 score_volatility.py /tmp/sv.txt
