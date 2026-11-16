# REPORT_deepseek5_job27 (deepseek5, 2026-11-16 UTC) — the LMRCELL table by a command; the seven terms and the per-term counters under S14

(1) **Step 0 / Part A: met.** The cell table of job 25 BY THE COMMITTED COMMAND (`partA_cells.py`) over the
committed calib rows — the parse bug that produced job 25's zeros found and fixed (the rows' counter
segments sit after the third `|`, because my " || " separator contains pipes; `split("|", 3)` fixed it).
The known answer, set O, no option — **all six numbers of all three kinds EQUAL**:
kind 0 (tt_pv): passes 1,228,210, fh 44,165, fh at 1+ 24,102, conf at 1+ 13,636, rn 12,480,814, re
1,638,793; kind 1 (cut node): 1,039,157 / 134,136 / 82,068 / 55,124 / 3,152,921 / 2,111,736; kind 2
(neither): 2,497,227 / 66,105 / 23,818 / 14,101 / 7,409,806 / 619,594. Both identities EQUAL in all eight
tables (the cells' n vs the LMRK2 passes; the fh-at-1+ vs the fhge1). **The sentence:** when the cut-node
term goes 0 → 2 the tree total stays (1.0017 → 1.0000 across the settings) and the nodes move INSIDE the
cut-node kind: its reduced searches shrink (rn 5,527,504 → 3,152,921, −43 %) while its re-searches grow
(re 1,349,404 → 2,111,736, +56 %) and its CONFIRMED fail-highs nearly double (29,431 → 55,124, +87 %) —
the +2 reduction trades shallow fail-highs at cut nodes for confirmed ones, and that is where the nodes go.
(2) **Part B:** the ANCHOR (S14, the seven-option build) = **9,500,069** ✓ (41,311 / 24,872 / 28,574 —
equal to job 26's run of the same setting on the RegretTop build: two builds, one tree). All ten settings
**EQUAL** to your known sums and first-threes (`partB_O_runs.txt` + the compare command `partB_compare.txt`):
LmrTtPv 0 = 7,102,738; LmrTtPv 2 = 13,036,988; LmrNotImproving 0 = 12,541,489; LmrCutNode 0 = 9,448,238;
LmrCutNode 1 = 9,321,641; LmrCutNode 3 = 9,372,491; LmrTtCapture 0 = 10,215,869; LmrGiveCheck 0 =
9,485,151; LmrInCheck 0 = 9,272,972; LmrCutoffAdd 0 = 12,493,053. The G eleven: the anchor 18,466,239
(= job 26's G S14 run on the other build ✓) and the ten sums in `partB_G_runs.txt` (LmrTtPv 0 = 14,281,037;
LmrTtPv 2 = 23,316,572; LmrNotImproving 0 = 23,682,300; LmrCutoffAdd 0 = 23,533,907; the rest in the file).
The ratios with the position-bootstrap intervals (2,000 resamples, seed 2501) are in `partB_ratios.txt`.
(3) **Part C** (the counter build under S14, the rows COMMITTED `c*_calib_set_*.rows` + `.meta`; every
node sum = Part B's ✓): the KNOWN ANSWER for "O S14" **met on all counts** — passes 3,655,994 ✓; by
applied reduction 1,039,160 / 829,425 / 626,690 / 467,198 / 407,168 / 286,353 ✓; fail-highs 125,639 ✓ by
57,525 / 36,845 / 17,355 / 8,777 / 3,781 / 1,356 ✓; confirmed (reduction 1+) 46,420 ✓ (= 12,858 + 24,127 +
9,435 across the kinds); the passes by kind 1,165,719 / 694,708 / 1,795,567 ✓ (my k0/k1/k2 = your
tt_pv/cut/neither — the same numbering). **The three sentences:**
1. The terms whose FIRED passes fail high MORE often than the not-fired ones at the same setting
   (O S14, from the LMRTERM lines): **LmrCutNode — the fired 73.2 per 1,000 against 22.0 not-fired
   (3.3×)** and **LmrInCheck — 64.2 against 33.6 (1.9×)**. These two add reduction exactly where moves
   beat alpha more often than elsewhere: the match candidates. The others separate the other way
   (LmrNotImproving: the fired 22.9 vs 51.4; LmrCutoffAdd: 17.9 vs 43.3; LmrTtPv: 32.1 vs 35.4;
   LmrTtCapture: 31.8 vs 34.6; LmrGiveCheck: 27.5 vs 34.7).
2. `LmrNotImproving 0` (+32 % tree): the extra nodes are INSIDE the reduced searches — rn +7.56 M
   (15.79 M → 23.35 M) against re +0.72 M (2.68 M → 3.39 M). `LmrCutoffAdd 0` (+31.5 %): the same shape,
   rn +6.55 M, re +0.55 M. Both settings buy tree with more-and-shallower reduced passes, not with
   re-searches.
3. `LmrTtPv 0` (−25 % tree): the confirmed fail-highs found at tt_pv passes FALL — kind 0's conf at 1+
   12,858 → 10,857 (−2,001, −16 %) while its passes rise 6 % — the smaller reduction at tt_pv nodes
   finds fewer confirmed refutations per pass; that is the quality the −25 % buys against.

## stamps.txt, appended by a command

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| Part A the cell tables by a command | done | `partA_cells.py`, `partA_output.txt` | the known answer exact; 16 identities EQUAL |
| Part B the 22 runs | done | `partB_O_runs.txt`, `partB_G_runs.txt`, `partB_compare.txt`, `partB_ratios.txt`, the rows+meta | all EQUAL |
| Part C the eight calib runs | done | `partC_runs.txt`, `partC_tables.py`, `partC_output.txt`, the rows+meta | the known answer exact; the three sentences |
| The prediction gate | done | `rt_run27.py`/`calib_run27.py` refuse to start without `prediction.txt` (the gate added this job) | the rule made mechanical |

(The prediction gate: both runners now check `prediction.txt` in the job folder before the first run and
exit without it — my job 24/25 fault made structural.)

## 5. From my partner

`cursor/glmflash5-work-cb5c` at my check: job 13's report still not on its branch (its job 12 newest).
Its pv1 bridge (the job-16 plan) now has my Part-B S14 rows as the tree half: under S14 the seven terms'
sums are measured on my build (the table above) — the LMP-exemption question (its M9) meets the
cut-node neutrality directly: the LMR-side cut-node term does NOT move the tree under S14 either
(9,448,238 / 9,321,641 / 9,372,491 / 9,500,069 — all within 1.9 %), so its +31 Elo, if it repeats, is not
a tree-size effect.

## 6. What I did NOT do

- The G-side sentences of Part C (the tables for the G runs are in `partC_output.txt`; the three
  sentences above quote O — the G numbers are committed).
- The CHECKX maxima under S14 (carried from job 23).
- The G50-depth-16 runs under S14 (the A4-style depth question under the PC's settings).

## 7. What I am NOT sure about

- The LMRTERM lines' `f` flag: I read f1 = "the term fired" from the patch's fill() call order (the
  `f` argument comes from each term's own condition) — quoted from the patch, not independently proven.
- The conf% columns' denominator (the confirmed per fail-high) — my reading of the patch's counters.

## 8. A better way

The prediction gate (the runners refuse to start without the prediction file) turns the repeated
prediction-rule fault into an impossibility — one line per runner, added this job after two broken
predictions in two jobs. The same mechanical-gate idea applies to the "an existing output file stops"
rule (already mechanical) and to the block-summing rule (S3) — every recurring fault of this session
now has a gate instead of a reminder.

## 9. UTC stamps

## 10. Model name

The runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the agent name for
this work is deepseek5. I cannot verify the exact model version beyond what the runtime says.

## Questions for Fable

1. The LmrCutNode term: it adds reduction where the fail-high rate is 3.3× the average, and removing it
   costs almost no tree (9,448,238 vs 9,500,069 on O under S14). Is its match candidate the first of the
   seven to play (glmflash5's chain), or does Opus's cut-node-neutrality already cover it?
2. My kind numbering (k0 = tt_pv, k1 = cut, k2 = neither) matched your known answer's order — is that
   the PC's convention too (the file 26 head's "S14" settings come from the PC's tree)?
3. For the pv1 question (glmflash5's +31 vs Opus's −2.43): my Part-B table shows the LMR-side cut-node
   term neutral under S14 — does that let you rule out the LMR side of pv1's gain, leaving the SoundMate
   side (the step mask) as the only candidate?
```
2026-11-16T11:53:22Z job27 t0
2026-11-16T11:53:22Z part A command done
2026-11-16T12:01:19Z part B O runs done
2026-11-16T12:09:49Z part B G runs done
2026-11-16T12:15:47Z part C runs done
2026-11-16T12:21:44Z part C runs v2 done
```
