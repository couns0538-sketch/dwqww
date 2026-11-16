# REPORT — deepseek6, long 50 (the tuner's steps: the smallest change that moves the O tree by 2 %)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long50/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the runs; the driver adaptive (halve when the tuner step crosses, double when it does not, at most 6 runs a setting; the c-level ratios reused from long 27, not re-run).

## 1. Three lines
**Asked:** for each of the 14 S14 settings, the smallest change from its S14 value that moves the O tree at depth 12 by at least 2 % in either direction (start at the tuner's step, double or halve, ≤ 6 runs a setting).
**Answer:** **the tuner's steps are mismatched to their settings' sensitivity in both directions.** LmrQuietBase's step (8) is ~8x too large: a ±1 change (values 92/94) already moves O by +2.56 %. HistoryBonusMax's step (180) is also ~8x too large (its 2 % step ≈ 22). HistoryPruneMultiplier's step (200) is ~4x too SMALL (its 2 % step is 800). **LmrNoisyBase has NO 2 % step found within 16x its tuner step** (its +192 arm — value 205 — still moves O less than 2 %; the negative arm is out of range and was skipped, named). The five integer/switch settings need no runs (their step IS the smallest change; long 27's ratios all at or over 2 % except LmpBase's −c end at +0.25 %, whose +c end crosses). Predictions: 1 held (with the LmpBase nuance stated); 2 killed three times (LmrQuietBase, HistoryBonusMax below c/4; HistoryPruneMultiplier above 2c); 3 held; 4 not conclusively tested at the found steps (the driver recorded the level ratios, the per-end values are in the committed rows).
**How sure:** certain of every run (the rows committed with .meta); the c2 values for the halved settings are the last TESTED levels (their true integer steps rounded as stated per setting).

## 2. Honesty numbers
The plain build (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (its line in stamps.txt) | done | stamps.txt | exit 0 |
| the five no-run settings | done | PREDICTION.md item 1 + long 27's ratios | answers = their tuner steps |
| the eight adaptive searches | done | driver_out.txt, runs/*.rows, results.json | see 4 |
| prediction own commit first | done | PREDICTION.md | 1, 3 held; 2 killed x3; 4 partial |

## 4. The table (the 2 % step per setting; "ratio" = the O ratio at the found step)
| setting | tuner c | 2 % step | ratio at it | runs | note |
|---|---|---|---|---|---|
| LmrQuietBase | 8 | **1** (tested 92/94) | 1.0256 | 4 | the tuner step 8x too large |
| LmrQuietDivisor | 12 | 6 | 1.0609 | 2 | about right |
| LmrNoisyBase | 6 | none up to 192 | < 2 % at +192 | 5 | no 2 % step found; the negative arm out of range |
| LmrNoisyDivisor | 20 | 40 | 0.9679 | 1 | about right (the first doubling crossed) |
| LmrHistoryDivisor | 500 | 250 | 1.0477 | 2 | about right |
| HistoryPruneMultiplier | 200 | 800 | 1.0484 | 2 | the tuner step 4x too small |
| HistoryBonusQuadratic | 3 | 6 | 1.0302 | 1 | about right |
| HistoryBonusLinear | 6 | 12 | 1.0310 | 1 | about right |
| HistoryBonusMax | 180 | **22** (tested 2190/2234) | 1.0241 | 4 | the tuner step 8x too large |
| NullMoveBase | 1 | 1 (integer) | 1.0435 | 0 | the step is the minimum |
| LmpBase | 1 | 1 (integer) | 1.0345 (+c) | 0 | the −c end is +0.25 %, the +c crosses |
| SingularDepth | 1 | 1 (integer) | 1.0245/0.9646 | 0 | both ends cross |
| IirDepth | 1 | 1 (integer) | 1.0726/1.1000 | 0 | both ends cross |
| NonPawnCorrection | switch | false | 1.0251 | 0 | the switch itself |

## 5. Findings
1. **The tuner's step table is miscalibrated in both directions**: LmrQuietBase and HistoryBonusMax would move 8x finer; HistoryPruneMultiplier 4x coarser; LmrNoisyBase's step never reaches a 2 % effect even at 16x.
2. **LmrQuietBase is the most sensitive knob in the set**: a ±1 change (2.56 %) already crosses the threshold that other settings need 4-24x their steps to reach.
3. LmrNoisyBase's weak response persists across its whole reachable range (the negative arm clamped out at the min 0 — named per the rules).
4. Suspicions, not proven: none (the table is measurement).

## 6. What I read from my colleagues
Nothing new this item (the colleague reads were done at long 41's start; the next is due ~20:45).

## 7. What I did NOT do
The G-side 2 % steps (the item names the O tree); the sub-integer steps for the integer settings (impossible).

## 8. What I am NOT sure about
Whether LmrNoisyBase crosses 2 % between 96 and 192 (my budget spent its runs doubling; a fine sweep there would find any narrower crossing).

## 9. A better way
The tuner's step table should be derived from exactly this kind of measurement (the item's own point).

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long50/stamps.txt
?? forge-combo29/REPORT_deepseek6_long50.md
?? forge-combo29/tests_deepseek6_long50/driver_out.txt
?? forge-combo29/tests_deepseek6_long50/results.json
?? forge-combo29/tests_deepseek6_long50/runs/
$ ls forge-combo29/tests_deepseek6_long50/
CLAIM.txt
driver_out.txt
l50_driver.py
PREDICTION.md
results.json
runs
stamps.txt
```
