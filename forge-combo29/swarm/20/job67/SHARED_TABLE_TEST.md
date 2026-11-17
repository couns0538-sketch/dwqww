# seat 20 — job 67: I built the "share one table" fix and ran the acceptance test — it halves the problem, it does not pass

S-F56 stated the requirement: *a real fix must restore main-line depth at large Hash WITHOUT moving the alternate
lines' scores*, with the acceptance test being depth back to ~14 **and** alternate-line scores within tolerance. Two
other seats' fixes were on the table; I named "share one table between the lines" as the direction worth trying. **I
built it and tested it. It fails the second half of its own test.**

## What I changed
`SharedSearchState` gained a borrow constructor so the alternate line uses the **main** table instead of allocating a
second full-size one (keeping its own `stop`/`ponder_hit_ns` atomics):

```cpp
explicit SharedSearchState(TranspositionTable& borrowed) : tt(borrowed) {}
TranspositionTable owned_tt;      // empty when borrowed
TranspositionTable& tt;
...
alt_shared = std::make_unique<SharedSearchState>(shared_.tt);   // was: (hash_mb)
```
Built clean with `-DFORGE_MATE_ALPHA_GUARD=1`.

## The acceptance test at Hash 2048, MultiPV 3, 5 positions

| pos | uncapped depth | **shared depth** | uncapped lines (1/2/3) | **shared lines (1/2/3)** |
|---|---|---|---|---|
| 1 | 1 | **15** | −336 / −339 / −345 | −285 / −288 / −346 |
| 2 | 1 | **12** | −261 / −322 / −348 | −239 / −283 / −340 |
| 3 | 1 | **12** | 201 / 188 / 177 | **292 / 215 / 201** |
| 4 | 1 | **13** | −528 / −536 / −540 | **−643 / −732 / −743** |
| 5 | 1 | **11** | −241 / −278 / −280 | **−474 / −925 / −1185** |

**Verdict: FAILS.**
- **The depth half passes clearly:** 1 → **11–15 plies**, which is the whole point of the exercise.
- **The line-quality half fails:** alternate scores still move by up to **900 cp** (pos 5: −280 → −1185), and in both
  directions (pos 3 improves ~90 cp, pos 5 degrades ~900 cp).

## Why it fails, and what that teaches
Sharing the table is **not** benign: the alternate line's search now probes entries written by the *main* line, so it
re-uses bounds computed for a different root restriction. That changes its tree — which is exactly the mechanism my
S-C23 measured for `searchmoves` restrictions (a restriction perturbs the score because the tree differs). So
**shared storage changes the alternate lines' results by construction**, not by accident.

## So the requirement gets harder, and more precise
My S-F56 acceptance test was right to demand both halves, and this experiment shows **both named directions fail**:
- **fixed 64 MB cap** (S-C42/S-F56): restores depth, moves alternate lines by up to 775 cp → rejected.
- **share one table** (this job): restores depth (11–15), moves alternate lines by up to 900 cp → rejected.

**The surviving requirement is therefore narrower than "remove the second allocation":** the alternate line needs
*its own* table (for independent bounds) that is *cheap to allocate*. That points at **lazy/adaptive sizing** — allocate
the alternate table small and grow it only if the line actually needs the space — which I have **not** built. Or keep
the allocation and accept the depth cost at very large Hash, which is the status quo.

## Honest limits
- 5 positions, Hash 2048, one clock, MultiPV 3, Threads 1, built-in net.
- One implementation of "share": other sharing schemes (disjoint generation stamps per line) might behave differently;
  I did not build them, and I am not claiming this exhausts the idea.
- The build is a scratch experiment; nothing of it goes into the repository except this text description.
