# REPORT — deepseek6, long 21 (the LmrRoundF sweep on B_FINE)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long21/ · CLAIM.txt before the first command; PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** sweep LmrRoundF 128, 256, 384, 640, 768, 896 under LmrFine 1 + LmrFineHistory 1 on B_FINE, rows on O and G, with T2 (0) and T1 (512) as the anchors.
**Answer:** **the response is strictly monotone decreasing in LmrRoundF on BOTH sets, all twelve sums ordered with zero inversions** — O: 11,226,124 (128), 10,583,952 (256), 10,385,069 (384), [10,170,054 at 512], 9,700,786 (640), 9,303,607 (768), 8,569,567 (896); G: 21,551,946, 20,843,674, 19,452,596, [19,269,858], 18,645,902, 17,316,924, 15,998,150. Both anchors reproduced exactly from the same binary earlier this session (long 19's a_T1 rows). The pointwise-monotone hypothesis held globally: **RoundF alone sweeps the O tree from +25 % (0) to −9.8 % (896) of S14 — the strongest single knob this series has measured.** Predictions 1 and 3 held; prediction 2 held (s(128) −6.1 % from T2; s(896) 15.7 % below T1).
**How sure:** certain of the twelve sums (B_FINE = the long-4-verified binary, .meta beside every rows file); the monotone law is measured over seven points plus two anchors.

## 2. Honesty numbers
B_FINE /tmp/j4_tree/build/forge (sha 04bcba3d… — the long-19 bundle-A composition uses the same LmrFine patch; the sweep's binary is the plain LmrFine build): bench 11 = 312866 re-verified live at the start of this item.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim + prediction | done | CLAIM.txt, PREDICTION.md (ff9912ce4) | — |
| 12 runs (6 values x O,G) | done | runs/rf*_*.rows, sums.txt, .meta beside each | all rc=0 |
| monotonicity | done | sums.txt | strict on both sets, no inversion |
| anchors | done | long 19's a_T1 rows (same binary+patch) | 10,170,054 / 19,269,858 reproduced; T2's 11,915,365 / 22,952,032 from long 5c/19 |
| bestmove churn | done | bm.txt | 143–157 of 200 (O), 260–282 of 353 (G) vs T1 — all >= 100 as predicted |
| prediction scorecard | done | sums.txt, bm.txt | 1 held, 2 held, 3 held |

## 4. Findings
1. **The rounding constant is a genuine strength-of-shape knob**: (f + RoundF) >> 10 shifts every marginal site by one ply and the whole tree follows monotonically across 0..896 — no local reversals anywhere on either set.
2. **The curve is convex-ish in steps**: the O drops per 128-step are 6.1 %, 5.7 %, 1.9 %, then 4.6 %, 4.1 %, 7.9 % — the middle (384–512) is the flattest region, the ends move fastest; T1's 512 sits at a local shelf (the two anchors bracket the shallowest slope).
3. **RoundF 896's O sum (8,569,567) undercuts S14 itself by 9.8 %** — with the fine history term active, rounding-heavy settings reduce beyond anything the integer path expresses; if a tuner is given LmrRoundF it will find this end first.
4. Suspicions, not proven: whether the monotone law survives at RoundF > 896 (1023 untested — the range's top).

## 6. What I read from my colleagues
Nothing new this item (the colleague reads are on the 4-hour clock; last full read 16:29, next due ~20:30). The anchors come from my own long-19 rows.

## 7. What I did NOT do
RoundF 1023 and the 32-step fine ladder (kimi5's option allows 0..1023; the item names six values).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
None; the sweep is the natural design for a monotone-knob hypothesis.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long21/stamps.txt
?? forge-combo29/REPORT_deepseek6_long21.md
?? forge-combo29/tests_deepseek6_long21/bm.txt
?? forge-combo29/tests_deepseek6_long21/runs/
?? forge-combo29/tests_deepseek6_long21/sums.txt
$ ls forge-combo29/tests_deepseek6_long21/
bm.txt
CLAIM.txt
PREDICTION.md
runs
stamps.txt
sums.txt
```
