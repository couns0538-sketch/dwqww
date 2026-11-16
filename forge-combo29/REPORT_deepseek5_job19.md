# REPORT_deepseek5_job19 (deepseek5, 2026-11-16 UTC) — which pruning step drops moves that would have beaten alpha, counted cleanly

(1) **Part 0's line (the one number WRONG 4 asked for):** the 138.6/113.7/65.3/71.5 of job 16 and the
138.3/113.0/64.1/68.0 of job 18 come from two DIFFERENT instrumented builds — job 16's rates from the
DeeperBuys build (whose extra searches are the deeper s0/s1 pair only) and job 18's from the build that
ALSO carries the shallower pair; both are rates-only trees (the s0/t0 searches fill the hash for the
s1/t1 searches), the excess-class edges are identical (40/100/400), so the ~0.5-per-1,000 differences
are the different contamination, not a class-edge or set change. **A1 sum 12,573,318 (= none, exact);
A2 sum 254,025,827 (= your known, exact, finished in 100 s — no cut needed); every counter the build
prints is committed summed over the 200 positions** (A1: dt 40,680,114 with d20 = 16,452; A2:
dt 166,538,418, the r-fields filled, pn 355,045,996 — full lists in `a1_counters.txt` / `a2_counters.txt`).
(2) **B1/B2 on O, per step** (n = dropped moves, count-only tree vs probe-run tree; r1/r2 per 1,000 of
the probe run's n; the probes' nodes counted apart — the O probe added 3,295,022 nodes over 12,573,318):

| step (the job's numbering) | n count-only | n probe run | r1 per 1,000 | r2 per 1,000 |
|---|---|---|---|---|
| 2 quiet futility | 174,333 | 167,632 | 84.1 | 3.5 |
| 3 history | 10,621 | 9,695 | **148.0** | **2.0** |
| 4 quiet SEE | 850,381 | 849,358 | 18.5 | 3.4 |
| 5 capture futility | **0** | 0 | 0.0 | 0.0 |
| 6 noisy SEE | 1,065,754 | 1,048,888 | 5.2 | 0.0 |

set G (count-only 22,128,265 = none ✓; probe 28,778,945; probe nodes 6,885,545): 2: 331,857 / 329,014 /
47.9 / 5.5 · 3: 31,152 / 31,039 / 116.8 / 3.8 · 4: 1,787,926 / 1,799,018 / 11.7 / 2.6 · 5: 0 / 0 / 0 / 0 ·
6: 2,106,890 / 2,088,572 / 7.8 / 0.2.
(3) **One sentence:** the highest r2 per 1,000 dropped moves is QUIET FUTILITY at depth 4–6 (10 per 1,000
on O and 8 on G; 3.5 and 5.5 over all depths), history's r2 is 2.0/3.8 and my data cannot say whether it
moves with the multiplier — the three B3 count-only tree sums side by side are **12,550,200 (multiplier
1024) / 12,434,210 (2220) / 12,541,810 (4096)**, a dip at the PC's 2220 with the default 2048 printed
from the `uci` list — the r2-per-multiplier probe runs were not run (time; section 6).

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| Part 0 the owed line | done | this line (1) | the two builds differ, not the buckets |
| stamps by command only | done | stamps.txt (every line appended by the step's own script/command) | — |
| A1 SoundRegretCount true, O | done | `a1_O.dbrows`, `a1_counters.txt` | 12,573,318 exact |
| A2 + SoundRegretProbe true, O | done | `a2_O.dbrows`, `a2_counters.txt` | 254,025,827 exact, 100 s |
| RegretTop.patch.txt on fresh copy | done | `RegretTop.patch.txt`, `rt_pins.txt` | builds; pins 312,866 / 862,329 / 4,865,609; both names in `uci`; sha 59106ede723e9581… |
| identity: RegretTop false | done | `identity_runs.txt` | 12,573,318 ✓ |
| identity: RegretTopCount true | done | `identity_runs.txt` + rows/.meta | 12,573,318 ✓ |
| B2 prediction first | done | `prediction.txt` (own commit) | r1 band hit, r2 band WRONG (below) |
| B1 count-only O and G | done | `RegretTopCount+true_set_{O,G}*.rtrows` + `.meta` | sums = none exactly |
| B2 probe O and G | done | `RegretTop+true_set_{O,G}*.rtrows` + `.meta` | table above |
| B3 count-only ×3 multipliers, O | done | `RegretTopCount+true+HistoryPruneMultiplier+{1024,2220,4096}_set_O*.rtrows` + `.meta` | three sums above |
| sanitizers: plant then ASan/UBSan run | done | `asan_plant_result.txt`, `asan_runs.txt`, `asan_direct.txt` | plant caught; 0 engine reports |

## The A1/A2 counters, every field the build prints (summed over O, 200 positions)

A1 (`SoundRegretCount true`): co 1,298 · dt 40,680,114 · d00 34,642,376 · d01 2,311,047 · d02 4,291 ·
d03 710,635 · d05 1,021,366 · d10 1,749,063 · d11 34,335 · d12 135 · d13 109,238 · d15 44,185 ·
**d20 16,452** · d22 6,234 · d23 31,689 · d25 205 · d30 35 · d31 124 · d35 2 · all r/m fields 0.
A2 (`+ SoundRegretProbe true`): co 2,893 · dt 166,538,418 · d00 150,814,621 · d01 4,280,161 ·
d02 145,591 · d03 2,088,735 · d05 5,344,296 · d10 3,371,580 · d11 71,205 · d12 3,267 · d13 198,125 ·
d15 92,290 · d20 35,828 · d22 41,954 · d23 53,144 · d25 353 · d30 35 · d31 124 · d35 2 ·
r00 12,224,109 · r01 339,798 · r02 28,475 · r03 41,664 · r05 41,282 · r10 557,959 · r11 8,399 ·
r12 602 · r13 2,739 · r15 631 · r20 18,083 · r22 2,317 · r23 441 · r25 8 · m00 688 · m01 8 · m05 2 ·
m10 5 · pn 355,045,996.
Note the probe run's d20 (35,828) vs the count-only run's (16,452): the probes more than double the
counted in-check LMP drops — the disturbance kimi5's single-mode numbers carry, and the reason your
two doubts were the right ones to name.

## The B tables with the splits (probe run; per 1,000 of the probe run's n)

**set O, by depth class and node kind (r1 / r2):** the counts per cell are in the committed .rtrows;
the depth-aggregate picture:
- step 2 (futility): d1–3 n 160,747 r1 87 r2 3 · d4–6 n 6,374 r1 17 r2 10 · d7–9 n 443 r1 23 r2 14 ·
  d10+ n 68 r1 0 r2 0 — its r2 RATE rises with depth even as n collapses.
- step 3 (history): d1–3 n 9,601 r1 149 r2 2 · d4–6 n 94 r1 32 r2 32 — the r2 RATE is highest where
  almost nothing is dropped; over all depths r1 148.0 / r2 2.0.
- step 4 (quiet SEE): d1–3 n 519,730 r1 29 r2 5 · d4–6 n 304,569 r1 2 r2 1 · d7–9/d10+ r1 0.
- step 6 (noisy SEE): d1–3 n 1,013,795 r1 5 r2 0 · d4–6 n 35,092 r1 0 r2 0.
- The pv × in-check kinds: the kinds' cells are in the rows; no kind dominates the r2 counts — the
  in-check cells of steps 3/4/6 are ~empty (consistent with job 18: steps 2/4 cannot fire in check,
  and the others barely do).
**set G:** same shape (step 2: d1–3 r1 55 r2 5; step 3: d1–3 r1 123 r2 4, d4–6 n 1,870 r1 22 r2 7;
step 4: r1 20/2/0 by depth; step 6: r1 8/0/0).

## Prediction scored (prediction.txt, committed before the runs)

- step 3 r1: predicted 100–200 per 1,000, point 150 — measured **148.0**: inside the band, the point
  2 off.
- step 3 r2: predicted 35–75, point 55 — measured **2.0**: OUTSIDE the band, my model wrong. What I
  missed: the loop's own full-depth re-search (which every r1 winner receives before the node believes
  it) refutes nearly all of them — "beat alpha at the reduced depth" is almost never "would have
  changed the node". The r2 column across ALL steps is 0.0–5.5 per 1,000.
- The uncommitted guesses: quiet-SEE ≈ history's levels — WRONG (18.5 vs 148); futility LOWER r1 than
  history — RIGHT (84.1 < 148.0); noisy SEE lowest r1 — RIGHT (5.2); capture futility n = 0 — RIGHT
  (CaptureFutilityBase = 0 in the `uci` list).

## The count-only vs probe-run n, side by side (the disturbance)

| step | n count-only (O) | n probe run (O) | n count-only (G) | n probe run (G) |
|---|---|---|---|---|
| 2 | 174,333 | 167,632 | 331,857 | 329,014 |
| 3 | 10,621 | 9,695 | 31,152 | 31,039 |
| 4 | 850,381 | 849,358 | 1,787,926 | 1,799,018 |
| 5 | 0 | 0 | 0 | 0 |
| 6 | 1,065,754 | 1,048,888 | 2,106,890 | 2,088,572 |

The differences are 0.5–1.6 % — the probes disturb the tree little (they write the hash table AND the
histories; I kept BOTH — nothing is rolled back; the disturbance is what these differences measure).

## A5 — sanitizers

The planted-fault control first (the same compiler and flags, `-fsanitize=address,undefined -g`): the
heap-overflow plant reports `ERROR: AddressSanitizer: heap-buffer-overflow`, exit 1
(`asan_plant_result.txt`, reused from job 18's control). The RegretTop build with the same flags: 50
positions of O at depth 10 with the probe ON (`RegretTop true`): sum 1,491,339, **0** sanitizer reports
(`asan_runs.txt`), and 0 in a direct single-position run with stderr captured (`asan_direct.txt`).

## 5. From my partner

`cursor/glmflash5-work-cb5c` re-read at the start of this job: still job 10 as its newest report (its
job 12 — the cases played by games on the build my Part A pinned — was announced in your file but not
on its branch yet when I looked). Nothing of mine to cross-check against it this job; its M3/M4/M5
tree foundations were verified in my cross 1.

## 6. What I did NOT do

- The r2-per-multiplier probe runs of B3 (three more probe runs): not run — the minute budget went to
  A2 (100 s), the six B1/B2/B3 count-and-probe runs and the sanitizer pass. The three count-only sums
  you compare ARE committed.
- The 5×4×4 tables are committed as raw rows; only the depth aggregates are printed above.
- Step 1 is not probed (your spec — its moves never come out of the picker); the LMP drop count in
  kimi5's own counters (d00 = 34.6M count-only) is a different population and I did not reconcile it.

## 7. What I am NOT sure about

- The r2 near-zero: it rests on ONE build, one depth, two sets. If a probe searched the FULL re-search
  path the loop would take INCLUDING the singular-extension decisions my proxy cannot replicate, r2
  could differ; my extension proxy (gives-check-and-SEE) is stated in the patch header.
- The B3 dip at 2220: three sums, one set; noise until your PC-side numbers agree or a wider sweep says
  otherwise.

## 8. A better way

The count-only/probe pair (B1/B2) is the right shape and it should become the standard: the count-only
run doubles as the identity check (its sum MUST equal the engine's own), so every probe build carries
its own control for free — one option flag instead of a separate unverifiable counter build.

## 9. UTC stamps

The block below is made by a command (`cat stamps.txt` appended), not by writing.

## 10. Model name

The runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the agent name for
this work is deepseek5. I cannot verify the exact model version beyond what the runtime says.

## Questions for Fable

1. r2 near-zero across all four steps: is that the expected shape of "the loop already re-searches r1
   winners at full depth", or should r2 have been counted differently (e.g., against the FINAL node
   verdict rather than alpha)?
2. The B3 dip at 2220 — do your three held sums show the same dip? If yes, that is a cheap tuning
   signal worth a game pair; if no, my three sums are the odd ones and I should re-run them.
3. For a future job: the futility step's r2 rate RISES with depth while its n collapses (d4–6: r2 10
   per 1,000) — worth keeping the futility step OFF above some depth, or is n too small to matter?
## stamps.txt, appended by a command
```
2026-11-16T09:27:12Z job19 t0


2026-11-16T09:28:01Z A1 done sum=12573318 d20=16452
2026-11-16T09:29:40Z A2 done-or-cut
2026-11-16T09:30:36Z RegretTop built, pins done
2026-11-16T09:30:58Z identities hold (both 12573318); prediction committed
2026-11-16T09:31:49Z B1+B2 runs done
2026-11-16T09:32:25Z B3 count-only runs done
2026-11-16T09:33:04Z sanitizer runs done (0 reports)
```
