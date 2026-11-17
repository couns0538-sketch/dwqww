# AUDIT: what process reuse touched across my harnesses

## Trigger
S-F24 (job 20) had to be withdrawn because its harness served 32+ searches from one engine process, and warm
state shifted scores by up to 80 cp on identical requests — manufacturing at least one "the clock changed the
move" that does not exist in fresh processes. Auditing for the same fault found it in other scripts. This
document is the complete list.

## The guard (added in the same pass)
`lib/freshguard.py` — a runtime assertion, because a docstring is not a guard. `SearchCounter` records how many
searches each process performed and refuses to pass unless every process ran exactly one, or the experiment
declares `allow_reuse=True, reason=...`. It also fails when **nothing** was recorded, so a harness that forgets
to use it cannot pass vacuously. Self-test (`python3 lib/freshguard.py`) covers five cases: all-single accepted,
reuse caught, declared reuse accepted, reuse-without-reason caught, nothing-recorded caught.

## Verdict per harness

| harness | discipline | affected? | what happened |
|---|---|---|---|
| **job20/clockgain.py** | ONE process, 32+ searches | **YES — withdrawn** | scores shifted up to 80 cp; S-F24 corrected from 5-of-16 changed / +58 cp median to **1-of-16 / +17 cp**. Fixed: fresh `Eng` per search, reason in the docstring. |
| **job9/mates_run.py** | ONE process, 63 searches | **moves/scores yes, conclusion NO** | Re-ran with a fresh process per search: **57 positive mate claims, 0 not delivered, 0 distance disagreements** — identical to the original. S-F11's *conclusion* stands; the incidental bestmoves and cp values in its raw rows differ. Fixed in the script; corrected data in `job9/out_fresh/`. |
| **job9/negative_mates.py** | ALREADY fresh per call | **no** | Its `search()` spawns a process per call. Re-ran: 4/4 negative claims correct, 8 negative cp, 0 non-negative — reproduces exactly. S-F12 unaffected. |
| checks/check_27f2.py | one process per N, several per process | **no effect on its claim** | Its claim is about *command-level* behaviour (`go nodes N` with N<26), not about cross-search state; it also sends `position startpos` + `isready` before each search and uses `ucinewgame` deliberately. Its N=100000 control (13 info lines, 72,062 nodes) confirms the runner sees output. |
| job16/loneking.py | one process per arm | **label wrong, result null** | Its "warm" arm used `ucinewgame`, which is a cold reset (S-C7), so the arm was never warm and all 38 cold/warm pairs were identical. Null result unaffected; report carries the correction. |
| job17/timealloc.py, job18/plateau.py, job19/clockmoves.py | one process, several searches | **TESTED: one cell shifts, the headline does not** | See "measured, not guessed" below. |
| job5/softnodes.py, job7/pcpath.py, job8/clockpath.py, job10/underreport.py, job12/options_wired.py, job13/book_quality.py, job15/pcfixes.py | mostly fresh or single | **not material** | Their claims are per-search (determinism of the same request repeated, budget caps, book behaviour) and several explicitly use a fresh process; none compares scores across accumulated state. |

## Measured, not guessed: I tested the three clock scripts' shared cell
I first wrote here that job17/18/19 were "likely safe because a systematic shift would cancel". That was a
guess, and the guess was **wrong in one direction and right in another**. Measured on job17's own position at
`go wtime 6000 btime 6000 winc 60 binc 60`:

| discipline | bestmove | depth | nodes | cp |
|---|---|---|---|---|
| single fresh search (three runs) | `g7g6` | **18** | **314,239** | −294 (every time) |
| the same search after 10 earlier searches in one process | `g7g6` | **24** | **331,560** | −318 |

So warm state **does** move a clock cell: depth 18 → 24 on an identical request. The bestmove held, and the
node count moved only 5.5 %, but the *depth* column of job17's table is not comparable across rows because
each row inherited a different amount of warm history.

**But the headline survives.** Sweeping clocks with a fresh process for every cell:

| `go wtime` | fresh: bestmove | depth | nodes |
|---|---|---|---|
| 6,000 | `g7g6` | 17 | 288,912 |
| **10,000** | `e5e4` | **23** | **1,520,334** |
| **15,000** | `e5e4` | **23** | **1,520,334** |
| **20,000** | `e5e4` | **23** | **1,520,334** |
| 30,000 | `e5e4` | 25 | 2,374,143 |

The plateau is **exactly as S-F19 and S-F21 described it**: 10,000 / 15,000 and 20,000 ms give the identical
depth-23, 1,520,334-node search. So the *existence and location* of the plateau is confirmed under the
strict discipline. What is not confirmed is job17's *other* rows (its 6,000 ms cell reported depth 19/882,144
in the grid, where a fresh process gives depth 17/288,912) — those inherit warm history and their depth
column should be treated as approximate.

**Corrected status:**
- **S-F19 and S-F21: the plateau claim STANDS** (verified fresh-per-search above). Their *depth columns for
  individual non-plateau cells* are approximate because of warm history.
- **S-F22: the move-comparison claim is likely safe but not re-run** — its comparison is move identity across
  clocks, and my spot check above shows bestmoves matching between fresh and warm on this position
  (`g7g6` both ways). It still needs the re-run before its percentages are relied on.
- **S-F24: withdrawn and corrected** (1 of 16, +17 cp).

**Action taken:** `lib/freshguard.py` added and self-tested; `job20/clockgain.py` and `job9/mates_run.py`
fixed to fresh-per-search; the remaining clock scripts keep their original data with this document as the
caveat, and the re-run of S-F22 is the outstanding item.

## The rule this audit produces
**A harness that reuses one process across many searches measures a moving target.** Warm state changes node
counts, scores, and sometimes moves. Any comparison of search *results* across positions or settings needs a
fresh process per search, or an explicit cold reset (`ucinewgame`, which is a full cold reset per S-C7) — and
the harness must say which. The guard exists so "I meant to use fresh processes" cannot be a comment that
drifts out of sync with the code.

## Files
`lib/freshguard.py` (guard + self-test), `job20/CORRECTION_S-F24.md`, `job9/out_fresh/` (corrected mate data),
`job9/out_neg_fresh/` (S-F12 reproduction), this document.
