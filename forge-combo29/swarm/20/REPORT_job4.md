# REPORT job4 — seat 20, area 10 job 3: recount of helper glmflash5's match report

**what was asked** — Area 10 job 3: recount helper glmflash5's newest match report from its raw files — W-L-D per
match from its game lists, Elo and interval with the brief's formula over pair scores, and whether the matches'
openings are disjoint.

**the answer** — **Every number reproduces exactly.** All five matches of `REPORT_glmflash5_job27.md` (M73–M77)
recount to the same W-L-D, the same n5 pair histogram, the same Elo to 0.01, and the same 95 % interval to 0.01,
from the committed `gamelist_M*.txt` alone. Both pools (V@20,000 = M54+M59+M73+M74, +1.30 [−3.68,+6.29];
C8@20,000 = M60+M75, −1.39 [−8.51,+5.73]) also reproduce exactly, and the two job-24 n5 arrays their stats script
hardcodes are confirmed to equal those matches' actual game lists. All five matches use disjoint opening sets
(0 openings shared between any two matches; 0 duplicates inside a match). All printed identities hold.

**how sure** — certain: every number here is a deterministic recomputation over committed text, and my script and
its full output are committed with this report.

## Honesty numbers
This job is a **recount**; it runs no engine, so bench pins do not apply to its numbers. The build that is
verified for my other jobs is recorded in `../HONESTY.txt` (4/4 pins). The helper's own step-0 pins are quoted in
their report and their raw files are on their branch; I did not re-run their engine.

## Step table
| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| find the branch + the report | done | `gl/REPORT_job27.md`, `gl/stamps.txt` (commit recorded) | branch `cursor/glmflash5-work-cb5c`, report job 27 |
| dump every raw file | done | `fetch_glm.sh`, `gl/ls_job27.txt` | 42 files of job 27 + 85 gamelists on the branch |
| per-match W-L-D, n5, Elo | done | `recount_glm2.py` §A, `recount_glm.txt` | 5/5 matches exact |
| per-match 95 % interval | done | `recount_glm2.py` §A2 | 5/5 exact with their formula; see note below |
| both pools | done | `recount_glm2.py` §B | V +1.30 [−3.68,+6.29], C8 −1.39 [−8.51,+5.73] — exact |
| hardcoded job-24 arrays verified | done | `recount_glm2.py` §B2 | M54/M59/M60 all EQUAL to their own game lists |
| opening disjointness | done | `recount_glm2.py` §C | 0 cross-match overlaps, 0 intra-match duplicates |
| printed identities | done | `recount_glm2.py` §D | mates = W+L, n5 sums to pairs, W+L+D = 2·pairs: all hold |

## Findings
1. **The recount agrees with every printed number of job 27** — W-L-D, Elo to 0.01 and interval to 0.01, for
   five matches and two pools. Show it again: `python3 recount_glm2.py` in `job4/` (reads only `gl/gamelist_M*.txt`).
2. **The hardcoded n5 arrays for M54/M59/M60 in their `job27_stats.py` are truthful**: they equal the committed
   game lists exactly, so the two pools are not built from remembered numbers.
3. **The openings are disjoint as the report's design says**: 0 openings shared between any two of M73–M77, and
   every match uses 1,000 distinct openings for its 1,000 pairs, so the pairs really are colour-swapped on one
   opening each.
4. **Every identity the report prints holds** in the raw data: white+black mates = wins+losses (1115, 1058, 1093,
   1386, 1364), n5 sums to the pair count, and W+L+D = 2·pairs.

### A note on the two interval formulas (not a defect in their report)
their committed `job27_stats.py` computes `half = 1.959964 * d * sqrt(Vp/(4P))` where `Vp` is the variance of
PAIR scores; the brief writes `sd = 400/(ln10·m(1−m))·sqrt(var/pairs)`. Because `m` is per GAME (half a pair),
the correct conversion is `sqrt(Vp/(4P))`, so **their formula is right and the brief's literal substitution over
pair-score variance would be exactly 2× too wide**. My script prints both and they agree to 0.1 Elo because I
divide the pair variance by 4P rather than P. No error to report; I state it so nobody "corrects" them later.

### Suspicions, not proven
- Nothing about their arithmetic. I did not re-run their matches, so the game *results* are taken as given; what
  I verified is that the report faithfully recounts its own raw files.

## What I did NOT do
- I did not re-run any of the five matches: their engines (B10, sha256 7621bdfb…) are not on this machine and a
  1,000-pair match is outside one command's budget.
- I did not verify their step-0 pins (S14 / V / C8 / V5 / C5 node sums) — that needs their exe and their
  position file, and it is their area's job; I only report that their *game-data* numbers are exact.
- I did not check whether their openings `.epd` build really removed 80,979 duplicate openings.

## What I am NOT sure about
- Whether the pair interval should use a z factor at all for 5 single seeds; that is a statistical judgement, not
  a recount question. Their report already labels the matches "one seed".

## Times: see `gl/stamps.txt` and `stamps.txt`
## The last command's output
```
$ python3 recount_glm2.py | tail -6
  M77: white+black mates 740+624=1364  W+L 691+673=1364  EQUAL;  n5 sum 1000 = pairs 1000;  W+L+D 2000 = 2*pairs 2000: EQUAL
wrote recount_glm.txt
$ ls forge-combo29/swarm/20/job4/
fetch_glm.sh  gl  recount_glm.txt  recount_glm2.py  stamps.txt
```
