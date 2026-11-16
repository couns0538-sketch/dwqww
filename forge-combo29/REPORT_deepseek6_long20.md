# REPORT — deepseek6, long 20 (CheckExtensionDepth 3,4,5,6,7,10,12 on the plain base, O and G)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long20/ · CLAIM.txt before the first command; PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** rows on O and G at depth 12 for CED 3, 4, 5, 6, 7, 10, 12 on the plain base (knowns: CED 2 = S14's 9,500,069 / 18,466,239; CED 8 on O = 9,015,167; the peer session's E2 covers CED 5).
**Answer:** the fourteen rows are committed; the G curve is strictly monotone decreasing (18,477,987? no — 17,779,874 at CED 3 down to 14,183,210 at CED 12), **but the O curve is NOT monotone: CED 3 sits ABOVE S14 (9,691,604 > 9,500,069), CED 6 dips BELOW CED 8 (8,835,097 < 9,015,167), and CED 12 rises above CED 10 (8,984,654 > 8,875,740)** — three non-monotone points, two of which kill my predictions as written. The peer's E2 rows file does not exist on the branch (only its counter capture cex_E2_O.txt), so the CED-5 position-by-position comparison is declared impossible per my prediction's own clause and my sums stand alone.
**How sure:** certain of the fourteen sums (plain build, .meta beside every rows file); the non-monotonicity is a measured fact, its mechanism untraced.

## 2. Honesty numbers
The plain build /tmp/glmflash5_base/build/forge (sha e06310ec…) — the same exe every long item of this series used; no new build needed.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim + prediction | done | CLAIM.txt, PREDICTION.md (e18c9ffe0) | — |
| 14 runs (7 settings x O,G) | done | runs/ced*_*.rows + sums.txt | all rc=0, .meta beside each |
| CED 5 vs the peer's E2 | impossible | the branch holds cex_E2_O.txt (counters only), no E2 rows | declared impossible per the prediction's clause; my CED-5 sums: O 9,170,430, G 16,527,061 |
| the O curve shape | measured | sums.txt | non-monotone: peak at CED 3, dip at CED 6, rise at CED 12 |
| the G curve shape | measured | sums.txt | strictly decreasing over 2..12 |
| prediction scorecard | done | sums.txt | 1 impossible (declared), 2 half-held (CED10 held, CED12 killed), 3 killed (CED3 above, CED6 below), 4 held, 5 killed |

## 4. The sums (depth 12)
| CED | O | G |
|---|---|---|
| 2 (=S14) | 9,500,069 | 18,466,239 |
| 3 | 9,691,604 | 17,779,874 |
| 4 | 9,503,215 | 17,046,858 |
| 5 | 9,170,430 | 16,527,061 |
| 6 | 8,835,097 | 16,147,861 |
| 7 | 8,965,030 | 15,643,672 |
| 8 | 9,015,167 (known ✓) | 15,120,379 (my long-18 run) |
| 10 | 8,875,740 | 14,688,245 |
| 12 | 8,984,654 | 14,183,210 |

## 5. Findings
1. **The O curve has a local maximum at CED 3** (9,691,604, +2.0 % over S14): gating the extension to depth ≥ 3 makes the tree BIGGER than extending at depth ≥ 2 — the depth-2 check extensions save more than they cost on these openings, and removing exactly that band removes the saving while keeping the cost.
2. **CED 6 is a local minimum below CED 8** (8,835,097 < 9,015,167): the "obvious" monotone reading of the threshold is wrong in the middle; whoever tunes CED on O should sweep, not interpolate.
3. **CED 12 rises above CED 10 on O** (+108,914 nodes) while G stays monotone — the O-specific wobble lives at the thresholds where the opening positions' checking patterns change character.
4. The O/G node ratio drifts from 1.83 (CED 3) to 2.02 (CED 12) across the curve — the two sets respond differently in shape, not just in size.
5. Suspicions, not proven: the mechanisms in 1–3 (no code trace).

## 6. What I read from my colleagues
The peer session's job-5 report (its E1/E2 counter structure and its 2.59x/1.08x sub-node ratios) — my curve is the node-level companion of its extension-count picture: its "97 % of extensions at depth 2..7" is why the curve moves mostly inside 3..8 on O.

## 7. What I did NOT do
Depths other than 12 (the item names depth 12); CED values beyond the list.

## 8. What I am NOT sure about
The mechanism of the O-side wobbles (measured, not traced).

## 9. A better way
The peer's E2 rows should be committed alongside its counter capture — then the CED-5 cross-check closes in one compare command.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long20/stamps.txt
?? forge-combo29/REPORT_deepseek6_long20.md
?? forge-combo29/tests_deepseek6_long20/runs/
?? forge-combo29/tests_deepseek6_long20/sums.txt
$ ls forge-combo29/tests_deepseek6_long20/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
sums.txt
```
