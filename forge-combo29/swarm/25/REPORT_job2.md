# REPORT — seat 25, area 5, job 2 (draw scores)

## What was asked
The score at depth 10 (S14, Threads 1, Hash 16) for 20 positions each of K v K, KN v K, KB v K, KNN v K,
20 with a threefold repetition on the board (reached by a move list), and 20 with the fifty-move counter at 99.

## The answer
K v K, KN v K and KB v K are all exactly 0 (60 of 60) — correct, all three are dead draws.
KNN v K is never 0 (20 of 20 non-zero, +151..+299) — correct, two knights can mate.
Threefold repetitions are all exactly 0 (20 of 20) — correct, and they were genuine threefolds
(verified with python-chess `is_repetition(3)` for every line before use).
The fifty-move group is where it breaks: **16 of 20 report exactly `cp 0` at clock 99, including positions
that have 1 to 5 legal captures and up to 8 legal pawn moves** — i.e. moves that reset the fifty-move
counter and keep the game alive. All three probed boards give a normal score at clock 98 (-112 / -198 /
-215) and collapse to 0 at clock 99, and the engine then plays a king/rook shuffle instead of any of the
6-11 available clock-resetting moves.

## How sure
Very sure of the observation: the clock is the only variable changed, every record carries a parsed score
(0 unparsed), and the Rule-1 plant shows the same harness reading -112 on the same board at clock 98, so a
harness that "sees 0 everywhere" is excluded. Not sure of the exact mechanism inside the search (see below).

## Honesty numbers (this build)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four match (`../HONESTY.txt`).

## What was done

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction written and pushed alone | done | `PREDICTION.md` (commit 2bd3451f6) | committed before any measuring command |
| six position groups built from SEED 2501 | done | `make_draw_sets.py`, `make_sets.txt` | 20 each for A,B,C,D,Control,F; 20 distinct verified threefolds for E |
| E group verified as real threefolds | done | `make_sets.txt` (three examples printed), `analyse_draw.py` | every line confirmed with `is_repetition(3)` |
| 140 depth-10 searches, S14 | done | `draw_d10.jsonl` (140 records), `table_draw.txt` | 0 unparsed scores |
| analyse + loud failure on missing score | done | `analyse_draw.py` | an unparsed score exits 3, never reads as 0 |
| controlled clock sweep 0/50/90/98/99 on the three zero boards | done | `clock_control.txt` | 98 normal, 99 collapses to 0 |
| nature probe: depths 1..16 and `go nodes 50000` | done | `clock99_nature.txt` | 0 at every depth, ~47k nodes, always a non-resetting move |
| Rule-1 plant for this finding | done | `clock_plant.txt` | PASS: -112 at clock 98, 0 at clock 99 |
| checker hardening (seat 19 warning) | done | `../job1/check_pv.py` (now exits 3 on empty input) | empty input now FAILS instead of printing a clean table |

## Predictions, scored
| id | prediction | outcome |
|---|---|---|
| P1 | K v K all exactly 0 | HELD (20/20) |
| P2 | KN v K all exactly 0 | HELD (20/20) |
| P3 | KB v K all exactly 0 | HELD (20/20) |
| P4 | KNN v K not all zero, >=15 of 20 with |score| >= 100 | HELD (20/20, range 151..299) |
| P5 | threefold all exactly 0 | HELD (20/20) |
| P6 | clock 99: at most 5 of 20 exactly 0 | **KILLED** — 16 of 20 are exactly 0 |
| P7 | K+Q vs K control never 0 | HELD (20/20, 3 cp to mate 8) |
P6 being killed is the finding, not a mistake in the prediction: I expected the engine to play on at clock 99,
and it does not.

## Findings

### S-F3 (NEW) — at halfmove clock 99 the engine reports a draw score and refuses to reset the clock
Three boards that all have clock-resetting moves available:
```
r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1   9 resetting moves (1 capture, 8 pawn)
r4rk1/1pR4p/p1b1pbp1/5p2/2n2B2/4Q2P/Pq3PP1/1B3RK1 w - - 99 1  11 resetting moves (5 captures, 6 pawn)
2r3k1/5pb1/4q1np/5Np1/pP1P2P1/4B3/1P1Q1PP1/5RK1 b - - 99 1   6 resetting moves (3 captures, 3 pawn)
```
Every one reports `score cp 0` at depth 1, 4, 8, 12, 16 AND at `go nodes 50000`, and every one plays a
non-resetting shuffle (`a1a2`, `c7g7`, `g6f4`). The same three boards at clock 98 score -112, -198, -215 with
normal node counts. So the fifty-move rule is being applied as if the game were already drawn, one ply early:
at clock 99 the position is NOT drawn, because a capture or pawn move at ply 1 resets the counter.

Shows again:
```bash
python3 forge-combo29/swarm/25/job2/clock_control.py /path/to/forge
python3 forge-combo29/swarm/25/job2/clock99_nature.py /path/to/forge
```
and the plant that proves it is not my harness:
```bash
python3 forge-combo29/swarm/25/job2/clock_plant.py /path/to/forge   # PASS: -112 @98, 0 @99
```
Whole-group evidence: `draw_d10.jsonl` records `F_clock99` #0..#19; 16 of 20 are 0.

Beyond the known list: FABLE_TO_swarm_1 records the fifty-move rule only as "checkmate on the hundredth
half-move still wins; everything else is a draw" (a code comment reading, src/search.cpp:1303). This is a
measured behaviour of that rule at clock 99, which is a different claim.

### S-F4 (NEW, weaker) — the draw rule fires with a tiny node count, so it is a root-level cut, not an eval
At clock 99 the search returns 0 after 399-2279 nodes at depth 12 versus 14k-29k nodes at clock 0 on the same
boards. The engine stops searching as if the root were terminal. That is consistent with a root-level draw
test rather than the evaluation drifting to 0. I did NOT prove which check does it (see below).

## Suspicions, not proven
- The likely site is the root/leaf draw test: `src/search.cpp:1303-1315` has the comment "Checkmate on the
  hundredth half-move still wins; everything else is a draw" and `root_drawn` at `:2251` tests
  `board.halfmove_clock() >= 100`. A `>= 100` test cannot fire at clock 99 by itself, so either a different
  test (a "clock + depth" horizon test) fires, or the leaf score is damped to 0 and the root then reports it.
  I have the location, not the proof.
- `EvalRule50Damp` exists as an option (`option name EvalRule50Damp type check default false`, from the `uci`
  answer). I did NOT test whether turning it on changes this; that is the first thing I would test next.

## What I did NOT do
- I did not read the actual condition that produces the zero (only located candidate lines).
- I did not test `EvalRule50Damp true`, nor clock 100, nor clock 99 with a capture forced as the only legal move.
- The three probed boards are a subset of the 16 zeros; I did not probe all 16 individually.
- Job 3 of my area (checkmated/stalemated roots under ASan+UBSan) is not started.

## What I am NOT sure about
- Whether the 0 is "the engine believes the game is drawn" or "the engine's leaf eval is damped to 0 as the
  clock approaches 100 and the root just reports the damped value". Both produce 0; the node counts suggest
  the former but do not prove it.
- Whether the same happens at clock 99 with castling rights present or in a checking position (my three boards
  are all quiet).

## Times
see `stamps.txt`.

## Last command output
```
$ ls forge-combo29/swarm/25/job2/
A_KvK.fens  B_KNvK.fens  C_KBvK.fens  D_KNNvK.fens  Control_KQvK.fens  E_threefold.moves
F_clock99.fens  PREDICTION.md  analyse_draw.py  clock99_nature.py  clock99_nature.txt
clock99_probe.py  clock99_probe.txt  clock_control.py  clock_control.txt  clock_plant.py
clock_plant.txt  draw_d10.jsonl  make_draw_sets.py  make_sets.txt  run_draw.py  table_draw.txt
```
