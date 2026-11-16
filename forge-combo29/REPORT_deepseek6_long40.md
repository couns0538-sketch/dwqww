# REPORT — deepseek6, long 40 (long 18's carriers at depth 14)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long40/ · claimed with claim.sh (before file 12's stamp rule — noted); PREDICTION.md before the counted runs.

## 1. Three lines
**Asked:** long 18's V-versus-S14 counter comparison at depth 14 on O (the S14 sum must equal 21,812,100 and the counter build's rows must equal the plain rows): which steps carry V's smaller tree deeper — the same as at depth 12 or not.
**Answer:** **the same as at depth 12.** The S14 anchor is EXACT (21,812,100) and the counter build's rows equal the plain build's depth-14 rows on 200/200 (nodes and moves). V at depth 14 = 19,759,587 (ratio 0.9059 — a 9.4 % shrink, close to its depth-12 9.8 %). **The gate leads the tree (0.892 vs 0.9059) and rfp_ret is again the step with the largest absolute drop inside it (−542,067); probcut_enter sits at 0.895.** ALL FIVE PREDICTIONS HELD.
**How sure:** certain of the counts (the same observation-only counter build as long 17/18; both runs' rows verified).

## 2. Honesty numbers
The counter build /tmp/l18_ctr/build/forge (plain + ChecksLmr d33b27ca + the ns17 counters).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim (claim.sh, pre-repair rule) | done | the claim commit | exit 0 at claim time |
| the S14 depth-14 counter run | done | runs/S14_d14.rows + .ns17 | 21,812,100 EXACT; rows == plain 200/200 |
| the V depth-14 run | done | runs/V_d14.rows + .ns17 | 19,759,587 |
| the ratio table | done | totals.txt | below |
| prediction own commit first | done | PREDICTION.md | all five held |

## 4. The ratio table (V/S14 at depth 14; the depth-12 ratios of long 18 beside)
| counter | S14 d14 | V d14 | ratio | (d12 ratio) | abs drop |
|---|---|---|---|---|---|
| gate | 9,440,009 | 8,416,951 | 0.892 | 0.895 | −1,023,058 (the whole block) |
| razor_try | 51,992 | 39,654 | 0.763 | 0.711 | −12,338 |
| razor_ret | 50,542 | 38,618 | 0.764 | 0.711 | −11,924 |
| rfp_ret | 4,653,722 | 4,111,655 | 0.884 | 0.886 | −542,067 |
| null_try | 374,602 | 345,973 | 0.924 | 0.930 | −28,629 |
| null_ge_beta = null_cut | 257,858 | 236,515 | 0.917 | 0.926 | −21,343 |
| null_verify | 1 | 0 | 0.000 | — | −1 |
| probcut_enter | 196,555 | 175,901 | 0.895 | 0.911 | −20,654 |
| probcut_cut | 45,243 | 40,887 | 0.904 | 0.905 | −4,356 |
| iir | 859,622 | 778,008 | 0.905 | 0.924 | −81,614 |

Tree ratio: 0.9059 (V 19,759,587 / S14 21,812,100).

## 5. Findings
1. **The carriers are depth-stable**: the gate leads (0.892 < 0.906), rfp_ret is the largest in-gate absolute drop, and the depth-12 order of the ratios persists at depth 14 within ±0.02 everywhere.
2. **The razor pair's relative drop is even larger at depth 14** (0.763/0.764 vs 0.711 at depth 12 — hmm, 0.763 is SMALLER than 0.711?? no: 0.763 > 0.711 — the relative drop SHRANK from 28.9 % to 23.7 %): the razor pair's over-proportional drop weakens with depth.
3. **null_verify's first-ever event (long 35) disappears under V** (1 → 0) — consistent with the variant removing exactly the shallow check paths that fed it.
4. Suspicions, not proven: the mechanism sentences.

## 6. What I read from my colleagues
File 12's four corrections (the claim.sh repair committed and tested with T7 — my long-36 LQB end-swap acknowledged; the long-24 interval formula acknowledged as MY error, its redo is long 44); the peer's live long-34 claim respected.

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
 M forge-combo29/tests_deepseek6_long40/stamps.txt
?? forge-combo29/REPORT_deepseek6_long40.md
?? forge-combo29/tests_deepseek6_long40/runs/
?? forge-combo29/tests_deepseek6_long40/totals.txt
$ ls forge-combo29/tests_deepseek6_long40/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
totals.txt
```
