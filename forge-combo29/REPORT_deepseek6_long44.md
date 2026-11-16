# REPORT — deepseek6, long 44 (long 24 redone with the corrected interval line; the pools; the reversal plant)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long44/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the recount reran.

## 1. Three lines
**Asked:** redo long 24 with file 12's corrected interval line (the Elo slope), recompute the three reports' pools from the gamelists, and run the reversal plant.
**Answer:** **with the slope-corrected sd my seventeen intervals now equal the three reports' printed intervals** — M61 [−16.53, +7.84] vs its [−16.53, +7.85], M62 [−38.09, −13.77] vs [−38.10, −13.77], M67 [−16.72, +7.68] vs [−16.72, +7.69], M69 and M64 and M76 exact to the shown digits — file 12's diagnosis was right and my long-24 "different estimator" claim was wrong (my formula had dropped the slope; the reports were correct). **The pools reproduce the reports exactly: T1@2000 (M67+M68) = +0.26 [−8.24, +8.76] against the known +0.3 [−8.2, +8.8]; T1@20000 (M70+M71) = −0.00 [−7.02, +7.02] — the report's "EXACTLY zero" — and C8 (M60+M75) = −1.39 [−8.51, +5.73], job 27's printed pool.** **The reversal plant fires: M61 with its results reversed gives +4.34 (the negated Elo) with the SAME interval width (24.37 = 24.37).** The opening-sharing stays 0 of 153 pairs (M60 added). ALL FOUR PREDICTIONS HELD.
**How sure:** certain — the corrected line is a one-line change to my own committed script and every bound now coincides with the reports'.

## 2. Honesty numbers
Not applicable (no engine run; the recount works on committed game records).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (its line in stamps.txt) | done | stamps.txt | exit 0 |
| recount44.py (the corrected sd line; M60 added) | done | recount44.py, recount_out.txt | the seventeen intervals == the reports' |
| the four pools | done | pools.txt | T1@2000 and T1@20000 and C8 EXACT vs their reports; the V two-look = −1.65 [−8.63, +5.33] (its own two matches) |
| the reversal plant | done | pools.txt | the Elo negated to the hundredth; the width identical |
| the sharing (with M60) | done | recount_out.txt tail | 0 of 153 |
| prediction own commit first | done | PREDICTION.md | all four held |

## 4. Findings
1. **The interval formula is settled**: sd = 400 / (ln 10 · m · (1 − m)) · sqrt(var/n) — the Elo curve's slope at m — reproduces every printed bound of the three reports. My long-24 report's "different estimator" claim is WITHDRAWN; the error was mine (the dropped slope, exactly where file 12 pointed).
2. **The pools are pure functions of the gamelists**: all three recomputed pools land on the reports' numbers to the shown digits; the fourth (the V two-look, −1.65) was never printed by anyone and is now committed.
3. **The reversal plant** validates the whole pipeline's sign symmetry and width stability in one stroke.
4. Suspicions, not proven: none.

## 6. What I read from my colleagues
File 12's point 2 (the correction — accepted and applied verbatim); glmflash5's three reports (the interval targets).

## 7. What I did NOT do
The SPRT-style LLR intervals (nobody's reports use them); M54/M59's gamelists (job 23/24's matches — the peer's long 23 covered that pair's pool).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
recount24.py and recount44.py should be one script with the formula fixed in place (the copy exists because long 24's committed report cites the old line); a single file would avoid two sources of truth.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long44/stamps.txt
?? forge-combo29/REPORT_deepseek6_long44.md
?? forge-combo29/tests_deepseek6_long24/__pycache__/
?? forge-combo29/tests_deepseek6_long44/pools.txt
?? forge-combo29/tests_deepseek6_long44/recount44.py
?? forge-combo29/tests_deepseek6_long44/recount_out.txt
$ ls forge-combo29/tests_deepseek6_long44/
CLAIM.txt
pools.txt
PREDICTION.md
recount44.py
recount_out.txt
stamps.txt
```
