# STATUS — seat claimable

**VERDICT: SHIP.** The deciding number is `bench 11 = 312,866` — identical to the lock, on release
**and** on ASan+UBSan, with all 11 documented pins bit-identical and every one of the three
documented regressions fixed.

| question the brief asked | answer | evidence |
|---|---|---|
| Does the rule go inside the root-drawn path? | **Yes** — one 18-line hunk, after seat 12's mate scan, no leaf change | `patches/claimable_in_root.patch.txt`, `search.cpp` sha256 `2eaf0b5a…` |
| Did the pin cost disappear? | **Yes — 11/11 pins bit-identical** | `evidence/pins/candA_rel/`, `evidence/pins/candA_san/` |
| Was the pin cost removable at all? | **Yes, because it was never in the root path.** Root adjudication disabled → pins unchanged. Deleting only the leaf repetition arm → exactly `353,312 / 979,723 / 2,893,009` | `evidence/pins/rootsrch_rel/`, `evidence/pins/repdiag/` |
| 4 honesty pins on release and ASan+UBSan | **Bit-identical:** 312,866 / 862,329 / 3,024,920 / perft 5 4,865,609, on both | `evidence/pins/candA_san/pins.txt` |
| 7 adversarial families still correct | **7/7** | `evidence/probe/probe_matrix.json` |
| The 3 cases the general rule broke | **All 3 correct** — `cp 0`, `cp 0`, `mate 1` | `evidence/probe/three_cases_five_builds.txt` |
| Control proving attribution | **Lock fails 8 of 20 probes; candidate passes 20/20**, same harness and fixtures | `evidence/probe/probe_matrix.json` |
| Sanitizer claim non-vacuous | `__asan_` × 35, `__ubsan_` × 15; **caught a planted heap-overflow and a planted signed overflow**, negative control clean | `evidence/sanitizer/plant_fault.txt` |
| Leaf rule untouched | `Worker::is_draw` **byte-identical** to the lock, still line 1300, rule still 1302-1304 | diff in `FINDINGS.md` §1(c) |

## The number that decides it

**312,866.** The lock's bench 11, the composed tree's bench 11, and this candidate's bench 11 are the
same integer. A change that reproduces all eleven pins bit-identically, on two build types, twice
each, has no pin cost to weigh against its benefit — which is what the brief asked to establish.

The three documented failure numbers, on the r15-like build that reproduces them: **cp −1,235**,
**cp −501**, **`mate 1` → cp 529**. The candidate returns **cp 0**, **cp 0**, **`mate 1`**.

## What it is worth (and the limit)

At a claimable root the lock returned an **unsearched** move in **14 of 14** measured cases; the
candidate's move matches a real search of the same board one counter-tick earlier in **14 of 14**
(lock: 3 of 14). Scored with a depth-14 oracle: **better in 8, equal in 3, worse in 3, median
+36 cp**, range −290 … +1,211.

**The three negatives are the untouched leaf rule**, attributed directly: relaxing only the leaf
repetition/fifty rule turns one `cp 0` into **`mate 3`**. That is the one-ply-down defect the brief
told me to keep separate, and it is why the claim here is "the ROOT is repaired", not "a claimable
root's score is right".

## Not claimed

- Not a strength claim. The oracle ranks two moves at fixed depth; it is not a tablebase and no match
  was played.
- The repetition arm is covered by named fixtures, not by a bulk sweep — a FEN cannot carry
  repetition history, and this is stated rather than papered over.
- The `X1` reproduction is **−1,235** against the documented **−1,237**. This r15-like build is
  composed + rule + guard-off, not the original r15, which is not reconstructible from the record.
  Sign, magnitude and mechanism match; the last 2 cp are a build difference and are not smoothed.

## One defect found in the record

Seat 12's committed `claimable_draw.patch.txt` **does not compile** (`piece_at(...).type` on a plain
enum). The documented layered numbers were measured on a hand-corrected variant. They reproduce
exactly once corrected, so no published conclusion is wrong — but the artifact was not runnable as
committed, and that is worth knowing before anyone re-runs it.

## Also in this seat's record

My first probe harness hand-wrote fixture copies instead of reading the asserted file and reported a
false failure on seat 63's repetition-mate board — seat 63's own `63-F8` trap recurring. The harness
now reads only `evidence/fixtures.json`, which `scripts/build_fixtures.py` asserts with python-chess,
so nothing is typed twice.

## Files

`patches/claimable_in_root.patch.txt` (ship this) · `patches/01-03_*.txt` (rejected rule + the
settled pair, for reproducibility) · `scripts/` (pins, fixtures, probes, planted fault, three corpus
sweeps, oracle) · `evidence/` (pins × 9 builds, probes × 4 builds, corpus sweeps, sanitizer,
instrumentation) · `FINDINGS.md`
