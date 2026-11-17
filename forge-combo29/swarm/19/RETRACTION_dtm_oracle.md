# RETRACTION: my DTM oracle is WRONG for black-as-strong — 19-F55, 19-F58 and 19-C24 are withdrawn

seat 19 · area 9 · found while surveying mate-score accuracy, and it invalidates three of my findings.

## 1. The three lines

**What happened.** While surveying whether the engine's mate scores are true distances, I noticed every
"over-claim" was exactly **2 plies** — and a uniform 2-ply offset on every comparison is a symptom of **my
instrument**, not the engine. I checked with an independent brute force and the oracle is wrong.

**The proof.** Position `8/8/4k3/6q1/8/8/8/1K6 b - - 0 1` (black to move, black has the queen):

| source | value |
|---|---|
| my oracle's table, black-as-strong | **DTM 9 plies** |
| my oracle's table, after `g5d2` | DTM 8 |
| **independent brute force (written fresh)** | **mate in 5 plies = `mate 3`** |
| the engine (depth 20, PC20) | `mate +5` |

**My oracle over-states the distance by 4 plies on this position.** And the engine's `mate +5` is **closer to
the truth than my oracle's 9** — the opposite of what 19-C24 claimed.

**Consequences: 19-F55, 19-F58 and 19-C24 are RETRACTED.** They all rest on this oracle's DTM values.

## 2. The bug

I traced it to the retrograde loop's **predecessor bookkeeping**:

```python
unsolved_children = {k: len(succ[k]) for k in succ if k not in dtm}   # counts EDGES
...
for p in pred.get(k, ()):
    ...
    unsolved_children[p] -= 1
    if unsolved_children[p] == 0:
        dtm[p] = max(dtm[s] for s in succ[p]) + 1
```

`pred[s]` holds **one entry per edge**, and `succ[p]` can contain **the same successor key more than once** (two
different moves reaching the same board with the same side to move — routine when a queen has many moves to the
same square-class). So `unsolved_children[p]` is decremented **several times for one child**, reaches 0 while
some children are still unsolved, and `max(dtm[s] for s in succ[p])` then takes the max over a **partial set** —
and worse, `max` over `succ[p]` at that moment includes successors with **no value yet**, which would raise, so
the assignments that did happen were from paths where the arithmetic went wrong in a different way.

**Two independent symptoms confirmed the diagnosis:**
- A **mate-in-1** position (`6k1/5ppp/8/8/8/8/5PPP/R5K1 w`) returns **`dtm = None`** — it is not in the table at
  all, even though `a1a8` is mate and 2,448 positions *are* seeded at DTM 1.
- The black-to-move position used in 19-C24 is **not in the table either** (I first hit a `KeyError`), and the
  value I did read came from the *white-strong* table with a sign/convention that does not apply.

**Validation did not catch this** because I only validated the **maximum** DTM (KQvK 19 plies, KRvK 31 plies) —
a statistic that can come out right while individual entries are wrong. **That is the real lesson: I validated a
summary statistic, not the solver.**

## 3. What is retracted, and what (if anything) stands

| finding | status |
|---|---|
| **19-F55** — `go depth 16` mates in 7 where `go nodes 20000` takes 11 | **RETRACTED** — the 7 and 11 came from this oracle. The 19-F56 *trace* (that `nodes 20000` stops after depth 7 because depth 8 costs 27,825 nodes) is **independent of the oracle** and stands as a description of the search. |
| **19-F58** — bare king plays a 17-ply mate where 29 was available | **RETRACTED** — the 17 and 29 came from this oracle. |
| **19-F59** — that the mirror defect is a depth limit | **PARTLY STANDS**: the depth-24 measurement (`go depth 24` → `f6f5` `mate -15`) is an engine observation, not an oracle value, and it stands. The *claim that `f6f5` is the longest defence* came from the oracle and is withdrawn. |
| **19-C24** — seat 05's S-F66 scores are "arithmetically impossible" | **RETRACTED** — and it was actively wrong: the engine's `mate +5` on that board is **closer to the truth (mate 3)** than my oracle's 9. **Seat 05's own PV-length finding is untouched** — it rests on replaying PVs, not on my oracle. |
| 19-F57 / 19-C10 (halfmove window) | **stand as reasoning**, but were applied to oracle values that are now withdrawn. |
| 19-F44–F53 (softnodes, nodes, clock), 19-F15/F20/F26 (tie order), 19-C19 (king lines), 19-C13/C15 (sweeps) | **unaffected** — none used the oracle. |

## 4. What I should have done

I validated the solver on a **maximum** (`max DTM = 19 plies`) and then used **individual entries**. A single
spot-check — brute-force one position and compare — would have caught this immediately, and I even had a brute
force written for the KQvK case. **The check that would have caught it is the one I ran last.**

The general form, which belongs in `HARNESS_TRAPS.md`: **validating a summary statistic does not validate a
table.** If you read individual cells, spot-check individual cells.

## 5. Status of the oracle code

`dtm_bfs.py` is **known broken** and should not be used. The fix is to count **distinct** children
(`len(set(succ[p]))`) and to decrement once per distinct child — and to guard the `max()` against unsolved
children. I have not written the fix, because a repaired solver needs its own per-position validation against
brute force before anything else is measured with it.

## 6. Files

`checks/matesurvey/`, and the independent brute force is quoted inline above.
