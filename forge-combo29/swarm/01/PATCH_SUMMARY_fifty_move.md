# Fifty-move root shortcut — patch summary for Opus

**Seat 01, area 1. One page. Applies to commit `6b98f217`.**

## 1. The bug

At a root position whose FEN says `halfmove >= 100`, the engine adjudicates the position as a draw **before
searching**, so it returns 0 nodes and misses a mate that is actually on the board. It is not a "draw score is
wrong" bug: the same board one halfmove earlier finds the mate.

It costs **real games**, not just analysis. With the brief's S14 settings applied and three clock modes, the
mate-in-one board at halfmove 100 answers `bestmove f2f3 / cp 0 / 0 nodes` under `go wtime 1000 btime 1000`,
`go wtime 10000 btime 10000` **and** `go movetime 500`; at halfmove 99 the same board answers `a1a8 / mate 1 /
1344 nodes` under all three (`job2/asan/gameplay_fifty.txt`).

It is not a general terminal-node defect: an already-mated board correctly reports `bestmove 0000 / score
mate 0` at halfmove 0, 98, 99, 100, 101 and 150 (`job2/asan/analyse_halfmove.txt`, Q1 block).

## 2. The one-line change

`forge-combo29/src/search.cpp`, **line 2251** (the line runs onto 2252). Remove `board.halfmove_clock() >= 100`
from the `root_drawn` test:

```c
// before
const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                           board.is_insufficient_material());
// after
const bool root_drawn = !legal.empty() && (board.is_repetition() || board.is_insufficient_material());
```

Patch file: `forge-combo29/swarm/01/job2/fifty_move_mate.patch.txt`, applies with
`patch -p2 --fuzz=0` from the repo root against `6b98f217`.

**Why removing it is safe.** The leaf test `is_draw()` (search.cpp:1302) already returns a win for a mate on
the hundredth half-move, and it already sees the fifty-move draw at `halfmove >= 100` *inside* the tree. The
root shortcut was only ever an optimisation. The more conservative variant that keeps the shortcut when the
side to move has no non-pawn material (so no mate is possible) is also prepared, honesty-checked and in the
same job folder as `job2b/`; this one-line version is the one I recommend because it is the smaller diff.

## 3. Before / after — four commands

Board `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - <H> 1` (white mates with `a1a8`). Run each against the release build
and against the patched build; the `sleep` keeps `quit` from reaching the search thread early.

```sh
# halfmove 99 — unpatched
printf 'position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 99 1\nisready\ngo depth 6\n' | { cat; sleep 1; } | ./forge
# halfmove 99 — patched
printf 'position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 99 1\nisready\ngo depth 6\n' | { cat; sleep 1; } | ./forge-patched
# halfmove 100 — unpatched
printf 'position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1\nisready\ngo depth 6\n' | { cat; sleep 1; } | ./forge
# halfmove 100 — patched
printf 'position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1\nisready\ngo depth 6\n' | { cat; sleep 1; } | ./forge-patched
```

Pasted output (sha256 unpatched `e06310ec…`, patched `81c52608…`):

```
halfmove  99 unpatched:  info depth 6 ... score mate 1 nodes 126 ... pv a1a8     bestmove a1a8
halfmove  99 patched:    info depth 6 ... score mate 1 nodes 126 ... pv a1a8     bestmove a1a8
halfmove 100 unpatched:  info depth 6 ... score cp 0   nodes 0   ... pv          bestmove f2f3   <-- BUG
halfmove 100 patched:    info depth 6 ... score mate 1 nodes 126 ... pv a1a8     bestmove a1a8
```

## 4. Regression evidence: genuine draws stay drawn, and the cost

Boards where no mate exists before the claim — the shortcut was *correct* for these, so the patch must not
break them. Base vs patched, `regress_fifty_patch.py` (`job2/asan/regress_fifty_patch.txt`):

| board | go | base | patched | verdict |
|---|---|---|---|---|
| KQ v K, halfmove 100 | depth 10 | cp 0, 0 nodes | cp 0, 280 nodes, 1.0 ms | still a draw |
| KQ v K, halfmove 100 | movetime 100 | cp 0, 0 nodes | cp 0, 1792 nodes, 1.1 ms | still a draw |
| KQ v K, halfmove 150 | depth 10 | cp 0, 0 nodes | cp 0, 280 nodes, 0.9 ms | still a draw |
| KR v K, halfmove 150 | depth 10 | cp 0, 0 nodes | cp 0, 200 nodes, 0.8 ms | still a draw |
| K v K, halfmove 150 | depth 10 | cp 0, 0 nodes | cp 0, **0 nodes**, 0.7 ms | still a draw |
| mate in 1, halfmove 100 | depth 10 | cp 0, 0 nodes | **mate 1**, 210 nodes | mate found |
| mate in 1, halfmove 100 | movetime 100 | cp 0, 0 nodes | **mate 1**, 1344 nodes | mate found |

**Cost: 0.2–0.6 ms wall and at most 1,792 nodes** on the genuine-draw roots; K v K stays at 0 nodes. Bounded
by the existing time management in a clock search. Note the one-line version gives up the shortcut for *all*
halfmove>=100 roots including bare-king ones; the `job2b` variant keeps it where no mate is possible, which is
why it is offered as the conservative alternative.

## 5. The four pins, before and after

| pin | expected | unpatched | patched |
|---|---|---|---|
| `bench 11` | 312866 | 312866 PASS | 312866 PASS |
| `bench 13` | 862329 | 862329 PASS | 862329 PASS |
| `bench 16` | 3024920 | 3024920 PASS | 3024920 PASS |
| `go perft 5` | 4865609 | 4865609 PASS | 4865609 PASS |

Unpatched: `HONESTY.txt` and `honesty/asan/summary.txt`. Patched: `honesty/fix2/summary.txt`
(one-line patch) and `honesty/fix3/summary.txt` (conservative variant). Each is the pasted output of
`honesty/honesty.py`, one fresh process per check.

## 6. What I have not measured

The cost on roots that are *genuinely* drawn by repetition or by material and also sit at halfmove >= 100 was
not measured board-by-board beyond the table above; the table's K v K row is the bare-king case (0 nodes). I
did not run a game-pair match to price the patch in Elo, and I did not test a root that is *lost* for the side
to move at halfmove >= 100.
