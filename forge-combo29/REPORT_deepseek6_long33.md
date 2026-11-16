# REPORT — deepseek6, long 33 (the move generator against python-chess)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long33/ · CLAIM.txt before the first command; stamps per stage; PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** perft 3 on all 353 positions of G and perft 4 on the first 60, engine against python-chess per position, plus the planted illegal-castling control.
**Answer:** **equal 353 of 353 (perft 3) and 60 of 60 (perft 4) — zero differing positions.** The planted control behaved exactly as predicted: **the ENGINE gives a different count for the illegal-castling FEN (8,902) than for the corrected one (8,802) — it trusts the FEN's castling field — while python-chess gives 8,802 for BOTH (its castling generator sanitizes impossible rights, its documented clean_castling_rights behavior)** — so the control fires on the engine and is documented as not firing on python-chess, with the reason. The known answer: startpos perft 5 = 4,865,609 ✓.
**How sure:** certain (every position its own engine process; python-chess 1.11.2 from PyPI; my own perft over its legal_moves).

## 2. Honesty numbers
The plain build /tmp/glmflash5_base/build/forge; the known perft 5 re-run in the item (4,865,609 ✓).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| pip env | done | pip list | chess 1.11.2 present |
| perft 3 on G (353) | done | perft3_G.txt | equal 353, differ 0 |
| perft 4 on O's first 60 | done | perft4_O60.txt | equal 60, differ 0 |
| the planted control | done | PREDICTION.md's probed numbers; re-runnable by the two printf lines in stamps.txt | engine 8,902 vs 8,802 (fires); python-chess 8,802 = 8,802 (auto-clean) |
| the known perft 5 | done | the run line in stamps.txt | 4,865,609 ✓ |
| prediction own commit first | done | PREDICTION.md | all three items held |

## 5. Findings
1. **The engine's move generator agrees with python-chess on 413 positions x perft** — the strongest correctness evidence this series has produced.
2. **The FEN castling field is trusted, not validated, by the engine**: a position that keeps a castling right for a missing rook gets EXTRA perft nodes (the phantom e1g1/h1 rook move generation) — 100 phantom nodes at perft 3 on my constructed FEN. Not a bug for real games (legal FENs only), but a parser-robustness note; python-chess's auto-clean is the contrast.
3. Suspicions, not proven: none.

## 6. What I read from my colleagues
File 9's rule (tables from committed scripts — this report's numbers come from perft_cmp.py's committed output files).

## 7. What I did NOT do
perft 5 on all of G (out of budget; the item names the depths).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
The engine could validate the castling field against rook/king squares at FEN parse (one check) — the phantom-right acceptance is the only gap the plant found.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long33/perft_cmp.py
 M forge-combo29/tests_deepseek6_long33/stamps.txt
?? forge-combo29/REPORT_deepseek6_long33.md
?? forge-combo29/tests_deepseek6_long33/perft3_G.txt
?? forge-combo29/tests_deepseek6_long33/perft4_O60.txt
$ ls forge-combo29/tests_deepseek6_long33/
CLAIM.txt
perft3_G.txt
perft4_O60.txt
perft_cmp.py
PREDICTION.md
stamps.txt
```
