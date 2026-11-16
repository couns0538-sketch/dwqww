# REPORT_deepseek5_job24 (deepseek5, 2026-11-16 UTC) — the curve with one depth index; the margin as a setting; file 23's counting build

(1) **Step 0: met.** The runner (rt_run24.py) sends the three setup lines and reads each answer; writes its
own `.meta`; an existing output file STOPS the run (the check fired three times while I mis-directed its
output folder — the guard worked as designed). Known answers: G count-only **22,128,265** with line 127 =
**127,189** ✓; the Hash-32 control line 127 = **127,185** ✓ — your diagnosis confirmed: the job-22
"missing nodes" were the runner's missing `Hash 16` (the engine's default is 32), not a table-clear race;
my race hypothesis is withdrawn. `SeeQuietMultiplier 200` on O = **13,061,442**, line 81 = **120,630** ✓.
**Part A's four sentences** (FULL per 1,000 by k, INSIDE each depth class; the probe runs at Hash 16 —
their sums: O 15,995,636, G 29,103,670; the O one at Hash 32 was 15,995,635):
- **Quiet futility: YES, the rate falls with k inside every depth class** — d1: 63.8 (k1) → 34.9 (k1.5) →
  10.4 (k2) → 0.3 (k3); d2: 53.1 → 33.9 → 0.3. The two cells: d1's k1 = 63.8 and d1's k2 = 10.4.
- **History: YES, steeply** — d1: 107.6 → 19.0 → 2.7 → 0.1; d2: 145.3 → 10.1; d3: 161.9 → 2.7. Your doubt
  (5) was right: job 22's "flat-to-rising" was the DEPTH CONFOUND (the k class was mostly the node's
  depth); with the depth held fixed the history margin separates well.
- **Quiet SEE: NO clean fall — the rate is quantized by piece value.** d1: k1 0.0, k1.5 0.0, k2 16.1,
  k3 2.0 — the mass sits where a full-piece loss lands relative to 24 × lmr_depth² (your arithmetic:
  at lmr_depth 1 a lost pawn is 4.2× the margin); d4–6: k1 19.4, k1.5 14.4, then 1.2.
- **Noisy SEE: YES** — d1: 8.7 → 0.0 by k2; d2: 5.7 → 0.1; d3: 4.8 → 0.0.
The identities: in every run the k cells sum to that run's n and FULL per step (my first check compared
the k array's step indices against the n array's wrongly — the k array holds steps 2/3/4/6 at indices
0–3 while n holds 2–6 at 0–4; the data was consistent, my comparison was not; both raw forms committed).
(2) **Part B** (the count-only sums, Hash 16): 1.5× = **12,323,860** (18,436 / 25,667 / 47,356 — exact);
2× = **12,334,083** (18,593 / 30,125 / 45,934 — exact); HistoryPruneMultiplier 3072 = **12,618,034**
(18,407 / 25,758 / 52,363 — exact). The measured deltas beside the curve's prediction (the curve said
for 1.5×: futility n −36 %, FULL −49 % "if the tree stood still"): measured futility n **−65,828 of
174,333 = −37.8 %**, FULL **−7,297 of 14,315 = −51 %** — the curve's two numbers hold within 2 points
although the tree did NOT stand still (it shrank 2.0 %). 2×: futility n −78 %, FULL −93 %. HPM 3072:
history n −66 % (10,621 → 3,589), FULL −62 % (1,501 → 567); the other steps' FULL moved little
(futility −504, quiet SEE −294, noisy −150 — the tree's shifts).
(3) **Part C** (the counters on the DoubleExt build, counter-only — every node sum of B1 came out again:
O 12,573,318, G 22,128,265, G limit-64 22,026,435): O defaults: fail-low non-PV verifications **9,964**,
candidates 3,934, given 3,934, **refused 0** ✓, the given split by the inherited count
[3,008, 722, 161, 38, 5, 0, 0, 0] — nothing given at 5 or more, none at 7+ ✓. G defaults: fail-low
**60,155**, candidates 46,543, given 46,318, refused **225** — and the M-check: **all 225 refusals are in
the M ≥ 7 searches; 0 in the M ≤ 6 searches** (`partC_G_refused_check.txt`); the split
[19,064, 11,482, 7,105, 4,321, 2,495, 1,345, 506, 0] — nothing at 7+ ✓. G limit 64: refused **0** ✓.

## stamps.txt, appended by a command

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| Step 0 the runner + the four known answers | done | `rt_run24.py`, `step0_runs.txt`, the rows+meta | all met |
| Part A the unified k cells | done | `RegretTopC24.patch.txt`, `partA_runs.txt`, `partA_cells.json` | identities hold; the table above |
| Part B the margin settings | done | `partB_runs.txt`, the rows+meta | three count-only sums exact; the deltas above |
| Part C the singular counters | done | `DoubleExtC24.patch.txt`, `partC_runs.txt`, `partC_G_refused_check.txt` | the identities + the M rule met |

## The segfault I caused and fixed (for the record)

The first Part-A build crashed (SIGSEGV at position 1, three runs): the k arrays were still [4][5][3]
in the header while the new code wrote depth index 4 — an out-of-bounds write. The runner caught it
(rc = −11, the position, the partial rows saved) because of the EOF handling added this job. Fixed by
resizing the arrays; the crash and the fix are in the patch's history, not hidden.

## 5. From my partner

`cursor/glmflash5-work-cb5c`: job 13's report is STILL not on its branch at my check (job 12 newest).
Its announced results (history-off +10.6, futility-off −10.8, SEE-wide −15.4 on its tree) now meet my
Part-B tree numbers: history's drops carry the most full-depth regrets by rate (147/114 per 1,000) —
its +10.6 for history-off is the consistent direction; futility-off −10.8 matches the futility curve's
steepness (the drops it spares are the WORST ones — removing them hurts). No new cross-check this job.

## 6. What I did NOT do

- The G probe run of Part B (only O — the budget); the Part-B probe deltas above are O-only.
- B2's "given split by the inherited count 7 and more" — the split's 7+ cell = 0 everywhere ✓ reported,
  but no run forced it (limit 64's 294 at inherited 7 in the G-limit64 run is the closest look).
- The CHECKX maxima for the switched runs (carried from job 23).

## 7. What I am NOT sure about

- The probe sums' Hash sensitivity (O: 15,995,636 at Hash 16 vs 15,995,635 at Hash 32 — 1 node): real
  but tiny; the G probe at Hash 16 (29,103,670) has no Hash-32 comparison run.
- The k classes' monotonicity relies on the margin tests being nested (they are, by construction).

## 8. A better way

The curve-in-cells form (n and FULL in the same [step][depth][k] cell, both counted at one site inside
the probe) is strictly better than job 22's split counting: one counter family, no depth confound, and
the Part-B predictions come straight from the cells. It should be the standard shape for every
"where on the margin" question.

## 9. UTC stamps

## 10. Model name

The runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the agent name for
this work is deepseek5. I cannot verify the exact model version beyond what the runtime says.

## Questions for Fable

1. The futility margin at 1.5× costs −37.8 % of its drops for −51 % of its FULL regrets AND shrinks the
   tree 2 % — is that worth a game pair now (glmflash5's chain on my DoubleExt... on my RegretTop build),
   or does the futility-all-but-off match of its job 13 (−10.8) already answer it?
2. The quiet-SEE quantization: the k classes are piece-value shadows of lmr_depth — should the SEE
   steps' k axis be re-expressed in "piece values past the margin" in a future curve, or is the current
   form enough?
3. My Part-C counters count the fail-low verifications at non-PV nodes (9,964 on O) — kimi5's V6 counts
   the singular SEARCHES (33,497 on O): the difference (23,533) = the verifications at PV nodes + the
   passing ones — worth one counter for the split, or is the pair enough?
```
2026-11-16T11:05:54Z job24 t0
2026-11-16T11:06:02Z step 0 done
2026-11-16T11:07:05Z step 0 done
2026-11-16T11:09:00Z step 0 done
2026-11-16T11:10:09Z step 0 done
2026-11-16T11:11:20Z step 0 complete
2026-11-16T11:12:46Z part A runs done
2026-11-16T11:13:25Z part A rerun
2026-11-16T11:14:02Z part A rerun v2
2026-11-16T11:14:43Z part A rerun v2
2026-11-16T11:15:19Z part A rerun v3
2026-11-16T11:16:42Z part A rerun v3
2026-11-16T11:19:02Z part B runs done
2026-11-16T11:19:45Z part C runs done
```
