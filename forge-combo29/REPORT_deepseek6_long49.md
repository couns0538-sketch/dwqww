# REPORT — deepseek6, long 49 (the singular grid's corners at depth 14)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long49/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the counted runs.

## 1. Three lines
**Asked:** the singular grid's four corners (SingularMargin × SingularDepth: 0×5, 0×8, 4×5, 4×8) and S14 on O and G at depth 14 — does the singular extension's sensitivity grow with depth on games too.
**Answer:** **on G, yes for three of the four corners** (0×5: 1.6987→1.8915; 0×8: 1.1774→1.4446; 4×5: 0.8730→0.8208 — all amplify) — **but the most-capped corner 4×8 FADES on both sets** (G 0.6808→0.6920; O 0.8121→0.8291 — the ratios move toward 1). The anchors are EXACT (O 21,812,100; G 43,345,893). My eight d12 corner runs all differ from S14 as expected. Predictions: 1, 2, 4 held; 3 killed by the 4×8 corner.
**How sure:** certain of the eighteen runs (.meta each); the fade is measured, its mechanism interpreted below.

## 2. Honesty numbers
The plain build (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (its line in stamps.txt) | done | stamps.txt | exit 0 |
| the 18 runs (4 corners x O,G x d12,d14 + 2 S14 d14 anchors) | done | runs/*.rows + table.txt, .meta each | all rc=0 |
| the anchors | done | table.txt | both EXACT |
| the d12 corner identities | done | table.txt tail | all differ from S14 (no accidental identity) |
| the amplification scorecard | done | table.txt | 6 of 8 amplify; 4x8 fades on both sets |
| prediction own commit first | done | PREDICTION.md | 1, 2, 4 held; 3 killed |

## 4. The table
| corner | set | d12 sum | d12 ratio | d14 sum | d14 ratio | amplified |
|---|---|---|---|---|---|---|
| 0x5 | O | 24,570,190 | 2.5863 | 65,008,401 | 2.9804 | YES |
| 0x5 | G | 31,368,020 | 1.6987 | 81,988,044 | 1.8915 | YES |
| 0x8 | O | 19,556,349 | 2.0585 | 57,267,250 | 2.6255 | YES |
| 0x8 | G | 21,741,249 | 1.1774 | 62,619,238 | 1.4446 | YES |
| 4x5 | O | 7,304,352 | 0.7689 | 16,298,078 | 0.7472 | YES |
| 4x5 | G | 16,120,691 | 0.8730 | 35,576,610 | 0.8208 | YES |
| 4x8 | O | 7,714,548 | 0.8121 | 18,083,996 | 0.8291 | no |
| 4x8 | G | 12,571,186 | 0.6808 | 29,995,731 | 0.6920 | no |

## 5. Findings
1. **The singular sensitivity grows with depth on games for the three less-capped corners** — the answer to the job's question is yes, with the 4×8 exception.
2. **The 4×8 corner fades on BOTH sets**: at margin 4 (few singular extensions qualify) and depth cap 8, the deeper search's extra nodes come from elsewhere and the singular mechanism's share dilutes — the same "cap interplay" glmflash5's job-27 saw in its C5 match (the terms and the cap interact).
3. **The 0×5 corner is the extreme everywhere** (O 2.98×, G 1.89× at depth 14) — margin 0 with the deep cap multiplies the singular re-searches hardest.
4. Suspicions, not proven: the dilution reading in 2.

## 6. What I read from my colleagues
glmflash5's job-27 note (the C5-vs-the-cap interplay — the same direction as my 4×8 fade); the peer's long-43 grid is not yet on the branch (my d12 corner runs fill that gap for this comparison and are committed).

## 7. What I did NOT do
The full 20-cell grid at depth 14 (the item names the corners); the peer's long-43 d12 grid (its item).

## 8. What I am NOT sure about
The 4×8 dilution mechanism (5.2).

## 9. A better way
None.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long49/stamps.txt
?? forge-combo29/REPORT_deepseek6_long49.md
?? forge-combo29/tests_deepseek6_long49/runs/
?? forge-combo29/tests_deepseek6_long49/table.txt
$ ls forge-combo29/tests_deepseek6_long49/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
table.txt
```
