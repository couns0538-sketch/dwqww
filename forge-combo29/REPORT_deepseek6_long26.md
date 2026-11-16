# REPORT — deepseek6, long 26 (long 17's counters on B_FINE under T1 and T2)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long26/ · CLAIM.txt before the first command; stamps now kept at every stage (build 19:30:39Z, prediction commit before the runs, runs end 19:30:58Z — all in stamps.txt); PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** run long 17's eleven node-step counters on B_FINE under T1 (LmrFine 1 + LmrFineHistory 1) and T2 (its RoundF 0), with the known node sums as pins, and say which steps make T1's 7 % larger tree, compared with job 4's d-counts.
**Answer:** all four node sums EXACT (T1 10,170,054 O / 19,269,858 G; T2 11,915,365 O / 22,952,032 G) and the counter build's rows equal job 4's D2/D3 rows on 200 of 200 (O). **No single pruning step carries the growth: every counter grows roughly WITH the tree (gate 1.068 at T1 against a tree ratio of 1.0705 — a passive follower), while the OVER-proportional growers are probcut_enter (1.122 at T1; 1.398 at T2 against a 1.243 tree ratio) and iir (1.084; 1.402)** — the fine path's smaller reductions deepen the searches and redistribute nodes toward the depth-sensitive statements. Predictions: 1 held, 2 held, 3 half-held (T2's iir 1.402 just over my 1.4 kill), 4 killed (T2's razor pair 1.320/1.317, just over 1.3), 5 killed (probcut_enter is the largest of my named four under T2).
**How sure:** certain of the counts and the four exact sums; the "no carrier" reading is the measured ratio table plus job 4's site-level d-counts.

## 2. Honesty numbers
The counter build = /tmp/j4_tree + ns17_counters.patch (zero fuzz), /tmp/j4_tree/build17/forge; pins on B_FINE itself were taken in long 4/19 (312866 / 862329 / 3024920 / 4865609).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| ns17 on B_FINE (dry run + apply + build) | done | stamps.txt build line | applies cleanly on the LmrFine tree |
| four runs (T1/T2 x O,G) | done | runs/*.rows + *.ns17 | 200/353 searches captured each |
| row identities vs job 4 | done | totals.txt | T1_O and T2_O: 200/200 nodes and moves |
| the four known sums | done | totals.txt | all EXACT |
| ratio table + prediction checks | done | totals.txt | see 1 |
| prediction own commit first | done | PREDICTION.md | 1, 2 held; 3 half; 4, 5 killed (all reported) |

## 4. The ratio table (counter totals against long 17's S14 runs; tree ratio beside)
| counter | T1_O (tree 1.0705) | T2_O (tree 1.2542) | T1_G (tree 1.0435) | T2_G (tree 1.2429) |
|---|---|---|---|---|
| gate | 4,323,522 (1.068) | 5,040,784 (1.245) | 8,454,181 (1.044) | 10,085,918 (1.245) |
| razor_try | 21,124 (1.014) | 27,496 (1.320) | 158,814 (1.023) | 200,375 (1.291) |
| razor_ret | 20,587 (1.015) | 26,699 (1.317) | 147,036 (1.014) | 186,135 (1.283) |
| rfp_ret | 2,139,016 (1.069) | 2,415,307 (1.207) | 4,481,237 (1.043) | 5,206,176 (1.212) |
| null_try | 137,495 (1.050) | 177,874 (1.359) | 383,046 (1.092) | 516,574 (1.473) |
| null_ge_beta = null_cut | 95,164 (1.024) | 123,562 (1.329) | 262,800 (1.071) | 357,153 (1.456) |
| null_verify | 0 | 0 | 4 (0.333) | 18 (1.500) |
| probcut_enter | 72,936 (1.122) | 90,858 (1.398) | 245,548 (1.099) | 306,064 (1.369) |
| probcut_cut | 16,457 (1.086) | 21,511 (1.419) | 61,330 (1.049) | 80,521 (1.378) |
| iir | 383,296 (1.084) | 495,473 (1.402) | 643,708 (1.054) | 821,191 (1.344) |

## 5. Findings
1. **The growth is distributed, not concentrated**: the gate (the tree's biggest block) tracks the tree ratio almost exactly at both settings; the pruning steps do not individually "carry" the 7 %.
2. **The over-proportional growers mark the depth redistribution**: probcut_enter (+12.2 % at T1, +39.8 % at T2, against tree ratios 1.071/1.243) and iir (+8.4 %/+40.2 %) grow fastest — smaller reductions mean deeper searches, and both statements are depth-gated (ProbcutDepth 5; IirDepth 2 with the depth condition), so they see the shifted depth profile first. Job 4's site-level view (the d ≠ 0 sites at good-history moves) and this step-level view agree: the mechanism is "less reduction at selected sites", not "a step fires differently".
3. **The null chain grows over-proportionally only at T2** (null_try 1.359/1.473) — the fine path's deeper nodes reach the null-move gate more often; at T1 it stays near the tree ratio.
4. Suspicions, not proven: the depth-redistribution reading (5.2's mechanism); a per-depth-bucket diff would localize it further.

## 6. What I read from my colleagues
The peer's long-25 claim and prediction are live on the branch (no overlap with this item); file 8's corrections applied here (stamps at every stage; the claim-replacement breach at long 17 acknowledged in the notes at 19:14 and not repeated — long 26 was claimed only after checking the peer's live claims).

## 7. What I did NOT do
Nothing from the item.

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
A per-depth-bucket diff of the gate (T2 against S14) would show exactly which depths gained the nodes; the totals answer the question asked.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long26/stamps.txt
?? forge-combo29/REPORT_deepseek6_long26.md
?? forge-combo29/tests_deepseek6_long26/runs/
?? forge-combo29/tests_deepseek6_long26/totals.txt
$ ls forge-combo29/tests_deepseek6_long26/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
totals.txt
```
