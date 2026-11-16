# REPORT — deepseek6, long 18 (long 17's counters under V and under CED 8 alone)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long18/ · CLAIM.txt before the first command; PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** run long 17's eleven node-step counters under V = S14 + CheckExtensionDepth 8 + LmrGiveCheck 0 + LmrInCheck 0 and under S14 + CED 8 alone, with the known sums as pins, and say which steps carry V's 9.8 % smaller tree.
**Answer:** both knowns EXACT (V on O 8,565,026; CED 8 alone 9,015,167; the counter build is observation-only). **The carriers, by absolute saved nodes on O (V against long 17's S14 run): the gate block as a whole (gate 3,624,001 vs 4,049,383, −425,382, ratio 0.895), with rfp_ret the largest single step inside it (1,774,330 vs 2,001,770, −227,440, ratio 0.886); then iir −26,952 (0.924), razor −6,030 (0.711, the largest RELATIVE drop), null_try −9,182 (0.930), probcut_enter −5,798 (0.911).** CED 8 alone explains roughly half of the gate's drop (0.945); the two LMR-discount removals deepen it to 0.895 — removing the check discounts makes the tree smaller still, because the discounts were re-search enablers. On G the ordering is V 14,633,520 < CED 8 15,120,379 < S14 18,466,239, as on O. All six predictions held. R5: the planted fault reported (ASan, exit 1); the clean sanitizer build over O under V: 0 sanitizer lines / 200 positions.
**How sure:** certain of the counts and the two pins; the "carrier" reading is the measured ratio table, with the mechanism sentence (discounts as re-search enablers) marked as interpretation.

## 2. Honesty numbers (counter build /tmp/l18_ctr/build/forge = plain + ChecksLmr d33b27ca + ns17 counters)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (honesty_*.txt).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| patch set assembled | done | R1.txt | ChecksLmr sha d33b27ca… (B10's own patch, carries BOTH options; kimi5's LmrGiveCheck 0e5b0375… verified as its alternative — using both would collide, B10's chosen for reproducibility of the known sums); ns17 counters on top, zero fuzz |
| counter build + pins | done | honesty_*.txt | four exact |
| V on O | done | runs/V_O.rows, totals.txt | 8,565,026 EXACT |
| CED 8 alone on O | done | runs/CED8_O.rows | 9,015,167 EXACT |
| V and CED 8 on G | done | runs/V_G.rows, runs/CED8_G.rows | 14,633,520 / 15,120,379 committed (no knowns) |
| ratio table | done | totals.txt | all six predictions held |
| R5 planted fault | done | plant_evidence.txt | ASan heap-buffer-overflow, exit 1 |
| R5 clean sanitizer | done | san_V_O.rows | 0 lines / 200 positions |
| prediction own commit first | done | PREDICTION.md | all held |

## 4. The ratio table (V/S14 and CED8/S14, O, counters summed over depth buckets)
| counter | S14 (long 17) | V | V/S14 | CED8 | CED8/S14 |
|---|---|---|---|---|---|
| gate | 4,049,383 | 3,624,001 | 0.895 | 3,826,041 | 0.945 |
| razor_try | 20,834 | 14,804 | 0.711 | 18,105 | 0.869 |
| razor_ret | 20,274 | 14,422 | 0.711 | 17,688 | 0.872 |
| rfp_ret | 2,001,770 | 1,774,330 | 0.886 | 1,877,942 | 0.938 |
| null_try | 130,889 | 121,707 | 0.930 | 128,643 | 0.983 |
| null_ge_beta = null_cut | 92,956 | 86,073 | 0.926 | 91,212 | 0.981 |
| null_verify | 0 | 0 | — | 0 | — |
| probcut_enter | 65,000 | 59,202 | 0.911 | 63,157 | 0.972 |
| probcut_cut | 15,160 | 13,727 | 0.905 | 14,719 | 0.971 |
| iir | 353,529 | 326,577 | 0.924 | 338,891 | 0.959 |

Per-depth bucket lines for all four runs are in totals.txt.

## 5. Findings
1. **The gate carries the saving; inside it, rfp carries the most absolute nodes.** The static-pruning block is where V's 9.8 % tree reduction physically happens (−425 k gated nodes), not in the null/ProbCut machinery (−9 k / −6 k).
2. **The razor pair has the largest RELATIVE drop (−28.9 %)** — the extension changes which nodes sit at depth ≤ 2 — but its absolute weight is 0.5 % of the tree, so it is a marker of the depth-profile shift, not a carrier.
3. **CED 8 alone vs V**: the extension accounts for about half the gate drop (0.945 vs 0.895); the two LMR-discount removals add the rest — and both act by making the tree smaller, i.e. the discounts (−1 reductions for checking moves and in-check nodes) were pure re-search enablers at these settings.
4. Suspicions, not proven: the mechanism sentence in 3; the ratio table is measurement.

## 6. What I read from my colleagues
glmflash5's job 21/22/23 reports (B10's composition: ChecksLmr d33b27ca, sha re-verified; its match numbers unchanged); kimi5's job-7 LmrGiveCheck patch (0e5b0375, sha verified, redundant with ChecksLmr for this option — noted, not stacked). Nothing contradicts this report.

## 7. What I did NOT do
kimi5's LmrGiveCheck-patch-based variant of the same measurement (the recipe named both patch sources; building both would double-define the option — B10's chosen and the choice is stated in the step table).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
The per-depth bucket lines could be diffed (V against S14) to show WHERE the gated nodes vanished by depth; the totals answer the question asked.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long18/stamps.txt
?? forge-combo29/REPORT_deepseek6_long18.md
?? forge-combo29/tests_deepseek6_long18/honesty_bench11.txt
?? forge-combo29/tests_deepseek6_long18/honesty_bench13.txt
?? forge-combo29/tests_deepseek6_long18/honesty_bench16.txt
?? forge-combo29/tests_deepseek6_long18/honesty_perft5.txt
?? forge-combo29/tests_deepseek6_long18/plant_evidence.txt
?? forge-combo29/tests_deepseek6_long18/runs/
?? forge-combo29/tests_deepseek6_long18/san_V_O.rows
?? forge-combo29/tests_deepseek6_long18/totals.txt
$ ls forge-combo29/tests_deepseek6_long18/
CLAIM.txt
honesty_bench11.txt
honesty_bench13.txt
honesty_bench16.txt
honesty_perft5.txt
plant_evidence.txt
PREDICTION.md
runs
san_V_O.rows
stamps.txt
totals.txt
```
