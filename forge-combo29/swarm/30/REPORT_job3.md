# REPORT — seat 30, area 10 job 3: recount glmflash5's match numbers

## 1. Three lines
**Asked:** recount helper glmflash5's newest match report (branch `cursor/glmflash5-work-cb5c`,
`forge-combo29/REPORT_glmflash5_job24.md`, its game lists in `tests_glmflash5_job22/23/24/`) from
its raw files: W-L-D per match, Elo and interval with the brief's formula
`sd = 400/(ln10·m(1−m))·sqrt(var/pairs)` over pair scores, and whether the matches' openings are
disjoint.
**Answer:** **every number matches exactly.** Six matches (M55..M60) reproduce to the game and to
0.01 Elo with intervals identical to theirs; the three pools reproduce exactly (+6.67 [+1.35,+12.00]
over 5,000 pairs; +6.54 [−0.45,+13.54] over 3,000; +4.26 [−2.86,+11.38] over 2,000); their slice
check is true on all six (6,000-line EPD, slices at 1/1001/2001/3001/4001/5001). **One thing they did
not state: M46/M50 and M53/M54 play identical opening sets** (1,000/1,000 shared each), so those are
re-runs on the same openings, not independent seeds — worth knowing before pooling M53 with M54.
**How sure:** exact — the comparison is closed-form on files they committed, no engine involved.

## 2. Honesty numbers
No engine was run for this job (it recounts someone else's committed data), so the honesty numbers
of my build do not apply. The data files are theirs and unmodified; my scripts read them.

## 3. Step table
| step | done/partly/not | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `job3/prediction.txt` | 6 predictions, 2 of which I got WRONG (below) |
| extract their committed data | done | `~/work/glm22`, `~/work/glm23`, `~/work/glm24` via `git archive` | 15 gamelists, 6,000-line EPD |
| per-match recount | done | `job3/recount_job24.json` | all six exact |
| pool recount | done | `job3/pools_result.json` | all three pools exact |
| opening disjointness | done | `job3/overlap_and_slices.txt` | 2 overlapping pairs found |
| slice check | done | `job3/overlap_and_slices.txt` | all six True |

## 4. Per-match comparison (mine vs their `job24_stats_out.txt`)

| match | theirs W-L-D | mine | theirs Elo | mine | theirs 95 % | mine |
|---|---|---|---|---|---|---|
| M55 | 744-649-607 | same | +16.52 | +16.52 | [+4.63,+28.40] | [+4.64,+28.40] |
| M56 | 692-684-624 | same | +1.39 | +1.39 | [−10.45,+13.23] | [−10.44,+13.22] |
| M57 | 723-655-622 | same | +11.82 | +11.82 | [−0.23,+23.86] | [−0.22,+23.86] |
| M58 | 692-671-637 | same | +3.65 | +3.65 | [−8.49,+15.78] | [−8.48,+15.78] |
| M59 | 559-517-924 | same | +7.30 | +7.30 | [−2.74,+17.34] | [−2.74,+17.33] |
| M60 | 532-543-925 | same | −1.91 | −1.91 | [−11.99,+8.17] | [−11.98,+8.16] |

The remaining differences are 0.01 Elo, i.e. their rounding of the interval ends. **Nothing in the
report's arithmetic is wrong.**

## 5. Pools

| pool | their pairs / Elo / 95 % | mine | openings disjoint? |
|---|---|---|---|
| variant@2000 (M49+M51+M52+M55+M56) | 5,000 / +6.67 / [+1.35,+12.00] | 5,000 / +6.67 / [+1.35,+12.00] | yes |
| CED8alone@2000 (M53+M57+M58) | 3,000 / +6.54 / [−0.45,+13.54] | 3,000 / +6.54 / [−0.45,+13.54] | yes inside the pool |
| variant@20000 (M54+M59) | 2,000 / +4.26 / [−2.86,+11.38] | 2,000 / +4.26 / [−2.86,+11.37] | yes |

## 6. What they did not state (mine, 30-F11)
Their per-match slice check ("first game's FEN == line 1 / 1001 / 2001 / …") is true, and it makes the
six matches of job 24 disjoint. Across the whole 15-match set of jobs 22–24 there are exactly two
overlapping pairs:

| pair | shared openings | games with the same outcome | identical result lines |
|---|---|---|---|
| M46 vs M50 | 1000 of 1000 | 712 of 2000 | 553 of 2000 |
| M53 vs M54 | 1000 of 1000 | 715 of 2000 | 557 of 2000 |

So M50 is a re-run of M46's openings and M54 a re-run of M53's — different results, but NOT
independent seeds. The CED8 rung pools M53 with M57+M58; M58 is disjoint from both, so that pool is
not affected. **Their variant@20000 pool is M54+M59: M59 is disjoint from M54, so also unaffected.**
The overlaps matter for anyone who later pools M46 with M50 or M53 with M54 to double a sample:
those two would not double anything.

## 7. Where my own prediction was WRONG (recorded, not quietly dropped)
- **P3 KILLED.** I predicted their intervals would not match the brief's formula (that they used a
  different variance). They match to 0.01. Their stats script uses the same pair-score variance.
- **P4 KILLED.** I predicted at least one opening overlap *inside job 24*. There is none: the six
  matches partition one 6,000-opening pool exactly. (My prediction was right for the wider set, which
  is where the two overlaps actually are — but the prediction named job 24, so it is killed as
  written.)
- P1, P2, P5, P6 held.

## 8. Suspicions, not proven
- I did not verify that the games themselves were played by the engines the report names (that needs
  the exe hashes and a replay, not the game lists). I verified only the arithmetic from the lists.
- Whether 2,000-node games with 46 % draws measure anything a user would notice is a judgement I do
  not make here.

## 9. What I did NOT do
- Did not re-run any games (that would need their builds; the brief asks for a recount from raw files).
- Did not check jobs 1–21 or the deepseek6-style honesty numbers of the builds these matches used.
- Did not check the `M49`, `M51`, `M52` single-match intervals against a report I did not open; I used
  them only inside the pool the report defines.

## 10. What I am NOT sure about
- Whether the duplicate opening sets (M46/M50, M53/M54) are intentional re-runs (the report calls some
  matches "a second look", which suggests yes) or an accident of slice arithmetic. Nothing in the
  report says which.

## 11. Times: `job3/last_cmd.txt`.
## 12. Last command — `git status --short` and `ls` of the job folder: see `job3/last_cmd.txt`.
