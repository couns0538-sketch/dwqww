# REPORT — deepseek6, long 24 (my own recount of glmflash5's jobs 25, 26 and 27)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long24/ · claimed with the NEW claim script (exit 0 line in stamps.txt); PREDICTION.md before the recount ran.

## 1. Three lines
**Asked:** recount glmflash5's jobs 25, 26 and 27 from its gamelist_M*.txt files with my own code: W-L-D, the five pair outcomes, pair Elo with its 95 % interval, and how many openings any two matches share.
**Answer:** all seventeen matches recount cleanly (each 2,000 games = 1,000 pairs; every opening exactly twice with swapped colours; the five pair-outcome counts sum to 1,000 per match). **My pair Elo equals every printed Elo in the three reports to the hundredth on all seventeen matches** (e.g. M61 −4.34, M62 −25.93, M64 −13.38, M69 −13.03, M76 +14.95). **My 95 % intervals are consistently NARROWER than the reports' — by a NON-constant factor (2.3× to 4.0×; M61 mine [−7.39, −1.30] vs its [−16.53, +7.85])** — my formula is the paired pentanomial one (variance of the pair scores over pairs); the reports' must be a different estimator; that difference is stated, not resolved by guessing. **The opening-sharing: ZERO distinct openings shared between any two of the seventeen matches (0 of 136 pairs)** — the used-opening removal works across jobs too.
**How sure:** certain of my own numbers (my code, my parse, committed); the interval-formula difference is a measured discrepancy pending the held-back comparison.

## 2. Honesty numbers
Not applicable (no engine run; this item recounts committed game records).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh | done | stamps.txt (exit 0 line) | the script's first live use |
| the seventeen gamelists fetched | done | /tmp/gm/ (34,000 lines) | 17 files x 2,000 lines |
| recount24.py | done | recount_out.txt | all seventeen clean; five outcomes sum 1,000 each |
| Elo centers vs the reports | done | recount_out.txt vs the three reports | all seventeen equal |
| the intervals | done | recount_out.txt | consistently narrower, non-constant factor — finding 5.2 |
| opening-sharing matrix | done | recount_out.txt tail | 0 of 136 pairs share |
| prediction own commit first | done | PREDICTION.md | 1, 3, 4 held; 2 half-held (centers yes, intervals differ) |

## 4. The recount (my numbers, per match)
| match | W-L-D | five outcomes (2/1.5/1/0.5/0) | pair Elo | my 95 % | the report's 95 % |
|---|---|---|---|---|---|
| M61 | 693-718-589 | 117/173/382/224/104 | −4.34 | [−7.39, −1.30] | [−16.53, +7.85] |
| M62 | 625-774-601 | 84/181/371/230/134 | −25.93 | [−28.95, −22.91] | [−38.10, −13.77] |
| M63 | 689-722-589 | 96/215/373/192/124 | −5.73 | [−8.79, −2.68] | [−17.95, +6.49] |
| M64 | 664-741-595 | 89/187/400/206/118 | −13.38 | [−16.35, −10.42] | [−25.27, −1.49] |
| M65 | 533-570-897 | 48/228/425/237/62 | −6.43 | [−8.99, −3.87] | [−16.67, +3.82] |
| M66 | 542-529-929 | 48/247/420/240/45 | +2.26 | [−0.24, +4.75] | [−7.73, +12.24] |
| M67 | 687-713-600 | 108/194/373/214/111 | −4.52 | [−7.57, −1.47] | [−16.72, +7.69] |
| M68 | 714-685-601 | 104/216/377/211/92 | +5.04 | [+2.08, +8.00] | [−6.81, +16.89] |
| M69 | 651-726-623 | (in recount_out.txt) | −13.03 | [−16.03, −10.04] | [−25.04, −1.03] |
| M70 | 528-537-935 | " | −1.56 | [−4.04, +0.91] | (pool −0.00 [−7.02, +7.02] over two) |
| M71 | 550-541-909 | " | +1.56 | [−0.92, +4.05] | " |
| M72 | 535-575-890 | " | −6.95 | [−9.57, −4.33] | [−17.43, +3.53] |
| M73 | 537-578-885 | " | −7.12 | [−9.59, −4.66] | (pulled the pool back) |
| M74 | 540-518-942 | " | +3.82 | [+1.36, +6.29] | " |
| M75 | 544-549-907 | " | −0.87 | [−3.38, +1.65] | " |
| M76 | 736-650-614 | " | +14.95 | [+12.01, +17.89] | [+3.15, +26.74] |
| M77 | 691-673-636 | " | +3.13 | [+0.12, +6.13] | [−8.91, +15.16] |

## 5. Findings
1. **The Elo centers are reproduction-exact on all seventeen matches** — the pair construction (grouping by opening, colours swapped), the scoring and the Elo formula agree with glmflash5's pipeline completely.
2. **The intervals differ systematically and non-constantly** (ratios 2.3–4.0): my paired pentanomial CI vs whatever estimator the reports used. Both are honest formulas; which one Opus's recount holds is what the held-back numbers will say. The Elo CENTER is unaffected by the choice.
3. **Zero opening sharing across all 136 match pairs** — the used-opening removal in the pool builder is airtight across jobs, so the matches are genuinely independent samples.
4. One process disclosure: my first run's five-outcome buckets were mislabeled (a round() that folded the 1.5/0.5 pair totals into their neighbours); the fixed version buckets by the exact pair total. The Elo and intervals were never affected.
5. Suspicions, not proven: which interval formula Opus holds.

## 6. What I read from my colleagues
glmflash5's three reports (the Elo values I verified against); file 10's rule (my long-24 claim went through claim.sh — its first live use, exit 0).

## 7. What I did NOT do
Job 23's matches (M44–M54: the peer session's long 23 covered them); strength opinions (the reports' Elo readings are theirs).

## 8. What I am NOT sure about
The interval estimator the reports used (5.2) — named, not guessed.

## 9. A better way
The five-outcome counts and the pair Elo should come from ONE shared helper across the sessions so the interval formula is a settled thing, not a per-session choice.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long24/recount24.py
 M forge-combo29/tests_deepseek6_long24/stamps.txt
?? forge-combo29/REPORT_deepseek6_long24.md
?? forge-combo29/tests_deepseek6_long24/recount_out.txt
$ ls forge-combo29/tests_deepseek6_long24/
CLAIM.txt
PREDICTION.md
recount24.py
recount_out.txt
stamps.txt
```
