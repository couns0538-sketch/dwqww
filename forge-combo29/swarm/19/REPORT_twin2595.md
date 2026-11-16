# The root-drawn twin at `src/search.cpp:2595` — reachable, and where it is wrong

seat 19 · area 9 · PC r15 and base 6b98f217 · no setoption · **Threads 1**.

## 1. What the twin is

`src/search.cpp:2595` is `if (!root_candidates.empty()) result.best_move = root_candidates.front();`, inside
the early-return block guarded by

```cpp
if (root_candidates.empty() || root_drawn) { ... return result; }
```

where on PC r15 (`FORGE_FIX_ROOT_DRAWN` defaults to **1**) `root_drawn` is narrowed to
`!legal.empty() && board.is_insufficient_material()`. On the base tree the flag does not exist and
`root_drawn` also covers `is_repetition()` and `halfmove_clock() >= 100`.

So the question splits in two, and both halves were tested one way each.

## 2. TEST 1 — insufficient material: **reachable by any GUI, and correct**

`8/8/8/4k3/8/8/8/4K1N1 w - - 0 1` (K+N vs K). A GUI reaches this by simply playing such an ending out; there
is nothing exotic about it.

| | base 6b98f217 | PC r15 |
|---|---|---|
| python-chess | `is_insufficient_material=True`, 8 legal moves | same |
| engine bestmove | `g1e2` (legal) | `g1e2` (legal) |
| score | `cp 0` | `cp 0` |
| nodes | 0 | 0 |

**Correct on both builds.** Every legal move draws, so returning the first candidate with score 0 is right,
and the engine says so explicitly (`info depth 6 ... score cp 0 nodes 0`). **No defect here** — the fallback
is doing exactly the job it should on this path, and a GUI seeing `nodes 0` in a dead draw is seeing the
truth, not a fabrication.

## 3. TEST 2 — threefold repetition with mate in one: the case the flag removes, and it matters

Position reached by a real move list: `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1 moves
a1a2 g8h8 a2a1 h8g8 a1a2 g8h8 a2a1 h8g8` — threefold repetition **and** `a1a8` is mate in one.

| | base 6b98f217 | PC r15 |
|---|---|---|
| python-chess | `is_repetition(3)=True`, mate-in-1 = `a1a8` | same |
| engine bestmove | **`f2f3`** | **`a1a8`** |
| score | `cp 0` | **`mate 1`** |
| nodes | **0** | 168 |

**On the base tree the twin fires and the engine misses a mate in one**, answering `f2f3` at 0 nodes. That is
the real defect, and it is not merely academic: the repetition makes the *draw claimable*, not the game over,
so a mate in one is still there to be played.

**On PC r15 the same position is searched** (168 nodes) and `a1a8 mate 1` is found. `FORGE_FIX_ROOT_DRAWN=1`
does its job — file 5's claim is accurate here, unlike `FORGE_FIX_ABORT_PUBLISH`.

**The pair is its own control.** Same harness, same driver, same settings, two builds: the base build shows
the defect and the PC build does not. That is what makes the PC build's correct answer evidence rather than a
harness that simply cannot trigger the case.

## 4. So: is the twin 2595 reachable in a way a GUI could trigger, or only where a draw score is correct?

**Split, and the split is the answer:**

- **Where it is still reachable on PC r15 — insufficient material — the answer is correct.** Any legal move
  draws; the fallback picks one and reports 0. Nothing breaks in a GUI.
- **Where it would be wrong — repetition and the fifty-move rule — PC r15 does not reach it**, because
  `FORGE_FIX_ROOT_DRAWN=1` sends those roots into the normal search. Measured, not inferred: mate in one is
  found at 168 nodes.
- **On the base tree it is reachable and wrong**, and it loses a mate in one. Any seat or engine built without
  the flag (i.e. the base commit everyone else here builds) still has this defect.

## 5. Recommendation — one paragraph, with consequences

For 19-F12, the publish path, my recommendation is: **when no iteration has completed, publish nothing until
one has — search one ply with a small node cap first, and only then answer.** Concretely, at
`src/search.cpp:3017` the `front()` fallback should not be reachable from a stopped-before-first-iteration
search at all; that path should run the existing `FORGE_FIX_HARD_LIMIT_EMERGENCY` style emergency ply (hash
move if legal, else one ply within ~2,000 nodes) and answer from its result. The consequences for a GUI are why
I prefer it over the alternatives: **answering the first generated move** (today's behaviour) is the worst of
the three, because the move is not just arbitrary but *systematically* arbitrary — always the same corner of
the generator, so a GUI's opening book and its engine will disagree in a way that looks like a bug in the book,
and on a lost position it picks the same kind of move every time, which is exactly what a training loop must
not ingest as a label. **Refusing to answer** (`bestmove 0000`) is honest but breaks any GUI or match runner
that waits for a legal move and treats `0000` as a forfeit — it would turn a 1 ms overrun into a lost game,
worse than the current bug. **The emergency ply** costs at most 2,000 nodes, always yields a *searched* move,
and its worst case is a move chosen at depth 1 rather than depth 0 — a small, honest degradation that no GUI
needs to know about. The cost to the owner is one caveat: `nodes` in that rare case is a couple of thousand
rather than millions, so any harness asserting an exact node count on an aborted search must not do so. The
honesty pins are unaffected — bench roots always complete an iteration, which I measured (all four unchanged).

## 6. What I did NOT do

- I did not implement that fix. It is a design change to search behaviour and belongs to the owner.
- I did not test the `halfmove_clock() >= 100` root under a repetition-free move list on PC r15, so my "the
  flag covers it" statement rests on reading the condition plus the repetition case measured here.
- I did not test `DrawJitter > 0`, which only exists on the base-tree path.

## 7. Files

`pcver/twin2595.py`, `pcver/twin_pc/RESULT.txt`, `pcver/twin_base/RESULT.txt`.
