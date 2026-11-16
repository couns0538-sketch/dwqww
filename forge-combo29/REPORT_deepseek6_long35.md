# REPORT — deepseek6, long 35 (long 17's eleven counters at depth 14 on O under S14)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long35/ · claimed with claim.sh (exit 0); stamps per stage; PREDICTION.md before the counted run.

## 1. Three lines
**Asked:** long 17's eleven counters at depth 14 on O under S14 (the node sum must equal 21,812,100) and the per-counter growth ratios from depth 12 to 14.
**Answer:** the anchor is EXACT (21,812,100). **Every counter grows at or above the tree ratio (2.296x): probcut_enter 3.024 and null_try 2.862 lead; null_ge_beta/null_cut 2.774; razor 2.49/2.50; iir 2.432; gate 2.331 and rfp_ret 2.325 trail at the tree ratio.** So the answer to "which steps grow most": the depth-gated deep statements (ProbCut's entry, the null-move chain) — and, against my own prediction, the razor pair also grew past my assumed frontier band. Predictions: 1, 2, 3, 6 held; 5 killed (razor_ret 2.493 > my 2.4 top); 4 held.
**How sure:** certain of the counts (the same counter build as long 17, one NS17 line per search, 200 searches).

## 2. Honesty numbers
The counter build /tmp/l17_ctr/build/forge (sha b6470525… — the long-17 binary, unchanged).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh | done | stamps.txt | exit 0 |
| the depth-14 run | done | runs/O_s14_d14.rows + .ns17 | 200 searches; the sum EXACT |
| the ratio table | done | totals.txt | below |
| prediction own commit first | done | PREDICTION.md | 1, 2, 3, 6 held; 5 killed (disclosed) |

## 4. The ratio table (d12 totals from long 17; d14 from this run)
| counter | d12 | d14 | ratio d14/d12 |
|---|---|---|---|
| gate | 4,049,383 | 9,440,009 | 2.331 |
| razor_try | 20,834 | 51,992 | 2.496 |
| razor_ret | 20,274 | 50,542 | 2.493 |
| rfp_ret | 2,001,770 | 4,653,722 | 2.325 |
| null_try | 130,889 | 374,602 | 2.862 |
| null_ge_beta = null_cut | 92,956 | 257,858 | 2.774 |
| null_verify | 0 | 1 | — (its first event: depth 9+ presumably) |
| probcut_enter | 65,000 | 196,555 | 3.024 |
| probcut_cut | 15,160 | 45,243 | 2.984 |
| iir | 353,529 | 859,622 | 2.432 |

Tree ratio: 2.296 (21,812,100 / 9,500,069).

## 5. Findings
1. **The depth-gated statements lead the growth**: probcut_enter (+3.02x) and the null chain (+2.86x) outgrow the tree (+2.30x) — two plies of depth multiply the population of the deep, depth-conditioned statements more than the tree itself.
2. **The gate and rfp_ret track the tree ratio almost exactly** (2.331/2.325) — the static-pruning block is a faithful cross-section of the search at every depth.
3. **My frontier assumption was wrong**: the razor pair (depth ≤ 2) grew 2.49x, ABOVE the tree ratio — the extra depth's re-searches also create shallow nodes (the deeper subtrees return to more siblings); a "frontier grows least" heuristic fails here.
4. null_verify's FIRST event ever (1 occurrence at depth 14 on O — long 17 had 0 at depth 12): the depth ≥ 14 forced-verification branch exists and fired once.
5. Suspicions, not proven: the redistribution mechanism (2./3.).

## 6. What I read from my colleagues
Nothing new this item (the reads are on the clock; the peer is on long 25 or later).

## 7. What I did NOT do
The G-set depth-14 counters (the item names O).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
None.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long35/stamps.txt
?? forge-combo29/REPORT_deepseek6_long35.md
?? forge-combo29/tests_deepseek6_long35/runs/
?? forge-combo29/tests_deepseek6_long35/totals.txt
$ ls forge-combo29/tests_deepseek6_long35/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
totals.txt
```
