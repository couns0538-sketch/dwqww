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


## Follow-up: the exact boundary and the mechanism (added after the first version of this report)

`boundary.py` on the first board, clock 96..101, depth 10:

| clock | score | nodes | bestmove | is it really a draw? |
|---|---|---|---|---|
| 96 | -141 | 69581 | d1c1 | no (clock < 100) |
| 97 | -103 | 27326 | d1c1 | no |
| 98 | -112 | 18097 | a1c1 | no |
| 99 | **0** | **399** | **a1a2** | **no — 9 legal moves would reset the clock** |
| 100 | 0 | 0 | b2b3 | yes by rule, but the game should never have reached clock 100 |
| 101 | 0 | 0 | b2b3 | yes by rule |

So the break is exactly at clock 99, one ply before the rule allows it, and at clock 100/101 the engine
returns 0 nodes — a pure root shortcut.

Mechanism tests (`rule50_hypothesis.py`, each toggling ONE thing on the same board at clock 99):
- `EvalRule50Damp true` -> still 0 (384 nodes); `EvalRule50Damp false` -> still 0 (399 nodes).
  So the damp option is NOT the cause.
- depth 1 / 6 / 10 / 20 / 30 -> still 0 at every depth (30 to 17081 nodes). Not a depth horizon effect.
- `UseNNUE false` -> still 0 (714 nodes). The net is not involved.
Conclusion: a hard-coded draw test fires at clock 99, before the fifty-move rule can apply, and it fires
regardless of the options that exist to control clock-dependent behaviour.

**A bug in my own harness, found and fixed here.** My first version of `rule50_hypothesis.py` sent
`position fen` BEFORE `ucinewgame`, so `ucinewgame` reset the board to startpos and every clock value
returned the startpos answer (`d2d4`) with score 24. That looked like "the clock makes no difference".
The file now sends `ucinewgame` first and carries a GUARD that exits 3 if the test board ever answers with
a startpos move. The first (wrong) output is not kept as evidence; the corrected run is
`rule50_hypothesis.txt` and its first line is the guard.

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

## Severity: the fault changes the MOVE, not just the number (`clock99_severity.py`)

| board | move at clock 0 | score at clock 0 | move at clock 99 | cost of the clock-99 move |
|---|---|---|---|---|
| 1 | d1c1 | -158 cp | a1a2 | **-40 cp** |
| 2 | e3e6 | -216 cp | c7g7 | **-999 cp** |
| 3 | g6e7 | -271 cp | g6f4 | **-160 cp** |

Method: take the engine's own bestmove at clock 99, play it from the clock-0 position, and search the
reply with the same engine at depth 12. The "cost" is that line's score minus the engine's own clock-0
score. On board 2 the clock-99 move loses about a queen (-999 cp) relative to the engine's own choice.

So S-F3 is not cosmetic: in any game that reaches a halfmove clock of 99 (which long endgames do), the
engine both reports a draw and plays a move it would never choose without the clock.

Command that shows it again:
```bash
python3 forge-combo29/swarm/25/job2/clock99_severity.py /path/to/forge
```


## Reachability in real games: NOT established (a test that could not answer)
`clock_in_games.py` plays a self-game with random legal moves for the opponent and samples the halfmove
clock every 10 plies for 300 plies. Result: 30 samples, clock max **16**, zero positions at clock >= 99.
That does not mean real games never reach clock 99 — random play captures and pushes pawns constantly, which
resets the clock, so this test simply cannot reach the regime. Long real endgames (KRP vs KR, same-colour
bishops with a fortress) do reach clock 99 routinely. So the reachability question is UNTESTED by me and
S-F3 rests on the constructed positions only. I am recording the null result rather than dressing it up.

### Second reachability attempt: also inconclusive
`endgame_clock.py` played KRP vs K, KP vs K, KR vs K and KB vs K to the end with the engine moving both
sides. All four ended early — threefold repetition at ply 35-38, or checkmate — so **0 positions reached
clock >= 95**. The engine heads for repetition, which ends the game by another rule before the fifty-move
clock becomes relevant.

**So: I did not demonstrate reachability in self-play.** S-F5's practical cost (-40/-999/-160 cp) is real
*in the constructed positions*, but whether a game ever hands the engine such a position is untested by me.
I am leaving S-F5 as "the move is much worse" and NOT claiming it loses games.
