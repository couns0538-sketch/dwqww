# STATUS — swarm/matehash

**Seat:** late-swarm audit, topic "mate scores through the transposition table".
**Base:** `6b98f217`. **Binary:** `/tmp/build-matehash/forge`,
sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`.
**Pins: 4/4 MATCH** (312,866 / 862,329 / 3,024,920 / perft 5 4,865,609).

## Headline

**The ply adjustment for mate scores is present, applied on both store and probe,
and correct.** 118,332 exhaustive unit cells, 0 failures, with two planted-wrong
twins producing 234,608 failures (the checker provably fires).

**No mate-distance encoding defect was found at the table boundary.** On the
population where a cold search is already correct (168/235), a warm-table re-probe
differs in 14 cases — and **all 14 are honest forced mates at their own claimed
length**, not miscounted distances. 9 of the 14 deltas are an ODD number of moves,
which an even-ply adjustment error cannot produce.

## What is done

| # | item | state |
|---|---|---|
| 1 | adjustment found in `search.cpp`, lines printed, both directions, clamp | **done** |
| 2 | same position re-probed at a different ply, warm vs cold | **done**, 235 pairs |
| 3 | corpus with known distances + independent exhaustive oracle | **done**, 186 fixtures (141 at distance ≥2) |
| 4 | mate-score eviction under hashfull pressure | **done**, 24/24 at hashfull 1000/982 |
| 5 | `MateValue` / `MateInMaxPly`, can a real mate reach the clamp | **done** |

## Deliverables

- `FINDINGS.md` — result first, evidence after, withdrawals section
- `STATUS.md` — this file
- `scripts/` — driver, pins, unit extraction test, DTM oracle, corpus builders, experiments
- `evidence/` — pins, corpus, chains, unit results, per-experiment jsonl

## Gaps, stated rather than hidden

- **Eviction (item 4)** was run twice. The first run was **vacuous**: `hashfull` read 0
  on all 24 rows (parsed off the final `info` line only) and it still reported 24/24
  correct. Fixed to peak-over-all-lines with a deeper flood; the rerun reaches
  `hashfull` **1000** (1 MB) and **982** (8 MB) with 24/24 correct. **The vacuous run
  is withdrawn.**
- **`go mate N`**: no experiment here touches it. All searches are `go depth`.
- **Threads > 1**: not tested; everything is `Threads 1`.
- **`score_usable`'s exact-clock short-circuit**: audited elsewhere; not re-measured here.
- **`DrawJitter` > 0**: not tested; all runs used the default.

## Withdrawals (all self-caught)

1. A "117,304 failures" unit result that was my own wrong invariant (`rem` vs `q+rem`).
2. **22 phantom encoding defects** from computing the mating ply as `2|k|-1` for
   mated-in-k claims, which actually land on ply `2k`. **This is the important one** —
   the first classification would have published 22 encoding defects that do not exist.
3. **A vacuous eviction run** that reported the same 24/24 as the real one while the
   table never filled. Caught by the `hashfull` control, not by the correctness count.
4. A classifier that returned `UNVERIFIABLE` on 14/14 rows because it read a `pv`
   field that was never written; fixed, and a planted control now proves it fires.
