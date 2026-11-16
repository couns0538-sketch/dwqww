# CORRECTION — 19-F18 was measured WARM; in cold state `bench` and R_1911 behave the same

seat 19 · area 9 · written after the coordinator relayed seat 10's state-discipline rule.

## What seat 10's rule says

Two identical unrestricted searches in one process give 56,720 → 4,951 → 4,516 nodes. Three separate
processes give 56,720 each time. **A cold baseline is a fresh process or `ucinewgame`; `Clear Hash` is not
cold** (it gives 40,569, a third value, deterministically).

## What that does to my 19-F18

My R_1911 counters were taken in **one process with no `ucinewgame` between positions** — i.e. WARM. I
measured the same sweep three ways with the same binary (`job4/drive_state.py`):

| mode | probes | hit rate | FULL-table misses | stale_gen |
|---|---|---|---|---|
| **warm** (one process, nothing between) — what I published | 15,184,039 | 35.1 % | 8,310,172 = **54.730 %** | 23,278 |
| **`ucinewgame` before each position** | 13,888,165 | 35.7 % | **142 = 0.001 %** | 0 |
| **fresh process per position** | 13,888,165 | 35.7 % | **142 = 0.001 %** | 0 |

`ucinewgame` and fresh-process agree to the last digit on every counter, which is exactly seat 10's point
about what "cold" means. Warm is a completely different measurement.

## The retraction

**19-F18 is RETRACTED as stated.** I claimed "`bench 13` cannot measure the transposition table's cost,
because bench reaches the replacement scan on 0.006 % of probes while a random-game workload reaches it on
54.7 %". **In cold state the random-game workload reaches it on 0.001 %** — 142 probes in 13.9 million.
`bench 13`'s 50 in 861,904 is 0.006 %; R_1911 cold is 0.001 %. **They are the same order of magnitude, and
the 54.7 % gap does not exist.** The difference I reported was entirely a warm-table artifact: when positions
share one table without `ucinewgame`, entries from earlier positions fill it, and the replacement path fires.

So: **`bench` is not structurally unable to measure the TT.** It reaches the replacement path rarely because
*any* cold workload does. My headline claim, and the "usable substitute" built on it, were wrong.

## What survives, and what does not

**Does NOT survive:**
- 19-F18's claim and its framing ("invalidates a measurement method").
- `RECIPE_tt_validation.md`'s premise and its 54.7 % figure and accept ranges.
- The inference that `probe_body`'s 2.09 % → 5.77 % self-share jump was caused by table pressure. That
  explanation is unsupported; the R_1911 profile was also taken in warm state (my `profD` run used
  `drive_search.py`, one process, no `ucinewgame`), so **the 5.77 % figure itself is warm-state and is not
  comparable to bench's 2.09 % cold figure.** The comparison I drew between them was invalid.
- 19-F19's slot distribution and stale_gen contrast, for the same reason (both are warm vs cold artifacts).

**Survives, and is strengthened:**
- 19-F20 (which pins detect an ordering change) — that ablation used `printf 'bench N\nquit\n'` in fresh
  processes, which is cold, so its node counts are sound.
- 19-F15 / 19-F16 / 19-F17 (tie order, toolchain pins) — all measured with fresh processes.
- 19-F21 (the ±2.29 % noise floor) — `noise_floor.py` starts a **fresh process per sweep**, so both sides were
  cold and consistently so. The node total 286,628 was identical in all 20 runs, which only happens under a
  consistent cold discipline.
- All four honesty numbers, and every check I ran (21-F1, 28-C2, 29-F3, 08-F9, 29-F9) — fresh processes
  throughout, plus `plant_control` proving the harness can see both states.

## The lesson, stated plainly

I had already written "treat a clean result as the first thing to doubt" and then did not apply it: **54.7 %
against 0.006 % was a suspiciously large contrast, and I explained it with a story about workload character
instead of checking the state discipline that would produce it.** A warm table and a cold table are different
experiments; I compared two numbers taken under different ones and called the difference a finding.

The check that would have caught it takes one command and 8 seconds: run the same sweep with `ucinewgame`
before each position and compare the node total. Warm gave 15,238,023 nodes; cold gave 13,925,108. That
difference alone should have stopped me before I wrote a report about the counters.

## What a future seat should do

Redo the TT question **cold**, with a state discipline written into any harness that touches node counts or
table state: `ucinewgame` + `isready` before every `position`, or one process per position. Any table that
does not say which was used is not reusable. My `job4/drive_state.py` implements all three modes and is the
tool for that.

Whether a cold workload *can* be made to reach the replacement path (a longer game sequence, a smaller Hash,
or a deliberately transposition-rich set) is an open question I did not answer — and I am not going to guess at
it twice.
