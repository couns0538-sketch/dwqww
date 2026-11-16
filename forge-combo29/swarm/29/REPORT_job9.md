# REPORT_job9 - the two TT probe changes together (-0.414 % instructions)

what was asked: my own continuation of job 8. After 29-F12 (removing a dead comparison) I asked whether the rest of
`probe_body`'s hit scan could be made cheaper without changing what it returns.
the answer: yes, twice. Gathering the four cluster keys explicitly and comparing them as four 32-bit lanes, then
confirming occupancy per matching lane in lane order, removes a further 3.37 M instructions. Together with 29-F12 the
removal is **4,513,768,543 -> 4,495,059,980 = -18,708,563 instructions (-0.414 %)** per `bench 13`, with every
correctness check I have passing. There is still **no wall-clock claim** (29-N6: a single timing comparison on this
machine is not trustworthy at these sizes).
how sure: high on correctness given the checks below; explicitly LOW on wall-clock benefit.

## honesty numbers
Clean base `e06310ec...6a83`: 312866 / 862329 / 3024920 / 4865609.
Both patches applied: **312866 / 862329 / 3024920 / 4865609 — all four identical.**

## a table: step | done-partly-not done | evidence | result

| step | done? | evidence | result |
|---|---|---|---|
| first attempt: flat 128-bit load of `cluster.entries` | done, **WRONG, reverted** | `sizeof_ttentry.cpp`, 29-N8 | `sizeof(TTEntry)==16` → load saw 1 slot; nodes became 347176/700414/2333149 |
| corrected: explicit 4-key gather + lane-wise occupancy | done | `tt_slot0_and_vector_probe.patch.txt` | applies to clean base, `patch -p1`, no fuzz |
| four honesty node counts | done | `raw_combo_ir.txt` | 312866 / 862329 / 3024920 / 4865609 |
| 40 positions x depth 10, score+PV+bestmove | done | job2 run, re-run here | **40/40 identical**, 852,430 nodes compared |
| hash-pressure stress, `Hash 1`, 4 positions | done | `raw_tt_stress.txt` | **4/4 identical** |
| legality at Threads 1 / 4 / 8 | done | `raw_tt_threads.txt` | all moves LEGAL |
| exact instruction count | done | `raw_combo_ir.txt` | **-18,708,563 (-0.414 %)** |
| sensitivity control (planted fault) | done, **PARTIAL** | `raw_tt_stress_plant.txt`, `raw_combo_plant.txt` | replacement plant caught 4/4; occupancy plant **NOT** caught — see 29-N9 |

## the change, in words
The old scan walks slots 0..3 comparing `key32` and testing `occupied()`, breaking at the first match. The new one
loads the four `key32` fields into one `__m128i` with `_mm_setr_epi32`, compares them all at once, gets a 4-bit mask,
and then visits only the lanes that matched — in ascending lane order, which is exactly the order the scalar loop
would have visited them, and stops at the first occupied one. Because it keeps the lane order and still requires
`occupied()`, it returns the same entry the scalar scan returned.

## findings
| id | area | one sentence | file | NEW |
|---|---|---|---|---|
| 29-F14 | 9 | Gathering the four TT cluster keys explicitly and comparing them as four lanes removes a further 3.37 M instructions, so the two TT changes together remove **18,708,563 instructions (-0.414 %)** per `bench 13` with all correctness checks identical. | `job8/tt_slot0_and_vector_probe.patch.txt`, `raw_combo_ir.txt` | NEW |

## suspicions, not proven
- Whether an actual `vpgatherdd` (AVX2 gather) would beat the four scalar loads I used: the keys are 16 bytes apart in
  one 64-byte cache line, so four plain loads are already cheap and a gather may well be slower. Seat 19's 19-F11
  found that prefetch request count, not traffic, dominated a similar loop, which argues against adding more
  vector machinery.
- Whether this is worth anything on the PC: `probe_body` is 3.65-4.86 % of deep search (29-F11), so 0.4 % of a bench
  run could plausibly be ~1 % of a deep-search run. Unmeasurable here (29-F9).

## what I did NOT do
- No wall-clock claim. Bench timing was already indistinguishable for the smaller patch and this one is smaller
  still; I will not repeat the N6 mistake.
- Did not touch `snapshot`, the lock path, the generation refresh or the aging arithmetic.
- Did not measure on the PC's net (impossible in this repository).

## what I am NOT sure about
- **The occupancy fault is not covered by my control** (29-N9). If the vector path mishandled an unoccupied
  key-matching slot, my 4 test positions would not show it. The reasoning above says it cannot (the `occupied()`
  test is unchanged and still gates the return), but the empirical control does not prove it. A harness would need
  to construct a cluster with a matching key32 in an unoccupied slot — which needs a deliberate unit test, not
  search output.

times: see stamps.txt
