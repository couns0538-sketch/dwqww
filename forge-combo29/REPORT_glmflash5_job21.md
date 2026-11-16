# REPORT glmflash5 — JOB 21 — the PC's check bundle R1 on my tree, 20,000 and 2,000 nodes

Branch `cursor/glmflash5-work-cb5c` (run A). B10 = a CLEAN copy of 6b98f217 + the ChecksLmr
patch extracted from this job file by its own sed command; sha256 of the patch file
d33b27caee1f950ec02783d8222ccfa8a97cbb0231e5a6c2639d33fd5026c19c (31 lines — as specified ✓);
applied from the REPOSITORY ROOT with `patch -p1 --fuzz=0` (dry-run and real outputs committed,
both rc=0). B10 sha256 7621bdfbb3b85f5e5ea37e9a7365adf2be27423e16d55d7b470d8cb7a513a1a6. Both
matches COMPLETE. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: does R1 (CheckExtensionDepth 30 + LmrGiveCheck 0 + LmrInCheck 0 — no check extension
below depth 30, no reduction discount for a checking move, none for a node in check) win games
under S14, at 20,000 and 2,000 nodes.

Answer: **M44 (R1 vs S14, 20,000 nodes, seed 20044): +4.86 Elo, 95 % PAIR interval [−5.34,
+15.07], 1,000 pairs — level, one seed.** **M45 (R1 vs S14, 2,000 nodes, seed 20045): +16.86
[+5.01, +28.72], 1,000 pairs — candidate AHEAD, one seed, and the interval is entirely above
zero: the bundle gains MORE at the self-play depth.** Both inside my filed prediction ranges
(M44 +6 [−6, +18]; M45 +12 [−2, +26]).

How sure: step 0 met on every row (all four S14 rows equal the PC's pre-written numbers TO THE
NODE — including the held-back-style rows S14+R1 8,330,799, S14+gc0ic0 9,143,222, S14+ced30
8,984,130); pins exact; the prediction was its own commit (0f94531eb, 15:42:01Z, hash pasted in
stamps) BEFORE M44's first game; probes show all three option lines arriving 2/2 with values,
base 0, refusals 0; 4,000/4,000 validation rows; identities under every table.

## 2. Step 0 — the four rows beside the PC's (`job21_rows.txt`, driver `job21_rows.py`
COMMITTED)

| setting | first-3 nodes | PC's known | sum over 200 | known |
|---------|---------------|------------|--------------|-------|
| S14 | 41311, 24872, 28574 | same ✓ | 9,500,069 | ✓ |
| S14 + R1 | 15285, 29999, 40991 | same ✓ | 8,330,799 | ✓ |
| S14 + LmrGiveCheck 0 + LmrInCheck 0 | 15453, 32361, 31939 | same ✓ | 9,143,222 | ✓ |
| S14 + CheckExtensionDepth 30 | 19960, 17379, 36773 | same ✓ | 8,984,130 | ✓ |

Pins, no option: 312,866 / 862,329 / 3,024,920 / 4,865,609 ✓; uci:
`LmrGiveCheck type spin default 1 min 0 max 4`, `LmrInCheck type spin default 1 min 0 max 4`
(both count 1). Refusal lines 0. No row differed — no finding to report.

## 3. The prediction, pasted by command

```
$ cat tests_glmflash5_job21/prediction.txt
M44 (S14+R1 vs S14, 20000 nodes, seed 20044, 1000 pairs): R1 removes the check extension below depth 30, the give-check reduction discount and the in-check discount - more complete check searching, bigger tree (8330799 vs 9500069 is SMALLER though - the extension removal dominates); the PCs SPRT first seed passed [0,5]: +6, wrong outside [-6, +18].
M45 (S14+R1 vs S14, 2000 nodes, seed 20045, 1000 pairs): checks matter more when nodes are scarce: +12, wrong outside [-2, +26].
$ git log -1 --format='%h %cI %s' (the prediction commit, pasted into stamps.txt at commit time)
0f94531eb 2026-11-16T15:42:01+00:00 glmflash5 job 21 prediction
```
(also in stamps.txt; the mechanism note in M44's line said "bigger tree" and then corrected
itself against the measured row — the parenthetical stands as written at prediction time.)

## 4. The probes (2 games each, per the first message's form; `probe_M44/M45.log`)

| probe | cand received (all 2/2, with values) | base received | refusals | go-limit |
|-------|--------------------------------------|---------------|----------|----------|
| M44 | CheckExtensionDepth=30, LmrGiveCheck=0, LmrInCheck=0 | its 14 lines ×2 (28 = 14×2 ✓), no extras | 0 | 411/411 `go nodes 20000` |
| M45 | the same three | its 14 ×2 | 0 | 222/222 `go nodes 2000` |

## 5. The matches (B10 both sides; S14 on both; R1's three lines on the candidate only;
nodes as named; Threads 1, Hash 16, OwnBook false, no adjudication, pairs colours swapped,
`-pgnout` in my folder; openings = job 20's file REUSED as the job orders — M44 lines 1–1000
(M42's openings), M45 lines 1001–2000 (M43's); first line of the file
`r2qk2r/ppp1bppp/3p1n2/4n3/4P3/2N2P1P/PPP2P2/R1BQKB1R w KQkq - 1 9`; order sequential;
concurrency 4)

Games by ending FIRST — from `gamelist_M*.txt` by the committed `job21_stats.py` (output
`job21_stats_out.txt`), identities printed by the same command (losses on time BY SIDE 0/0;
illegal/disconnect/crash 0):

| ending | M44 (2000) | M45 (2000) |
|--------|------------|------------|
| White mates | 587 | 739 |
| Black mates | 491 | 634 |
| 3-fold repetition | 642 | 349 |
| fifty moves | 138 | 170 |
| insufficient material | 137 | 102 |
| stalemate | 5 | 6 |
| **identity: mates = wins + losses** | 587+491 = 553+525 = 1078 ✓ | 739+634 = 735+638 = 1373 ✓ |

| match | cand | base | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|------|------|-------|------|-------|-------|----|-------------------------|----------------------|
| M44 | S14+R1 | S14 | 20000 | 20044 | 1000 | 553-525-922 | [47,245,390,269,49] | +4.86 [−5.34, +15.07] | COMPLETE (11:44) |
| M45 | S14+R1 | S14 | 2000 | 20045 | 1000 | 735-638-627 | [87,183,391,224,115] | +16.86 [+5.01, +28.72] | COMPLETE (1:53) |

Beside the PC: its R1 SPRT first seed +10.57 [+4.06, +17.09] (4,800 games) and second −0.65
(1,600) — my +4.9 (20k) and +16.9 (2k) sit inside that spread; the PC's own second seed said
"wait", mine says "the gain grows as nodes shrink" — the same shape pv1's ladder showed.

## 6. From my partners

- kimi5's job-10 quiescence counters (45–49 % of nodes are quiescence; the SEE/futility split) —
  noted for any qsearch tuning job; not used here.
- deepseek6's depth-14 identity rows — the patch chain's stability now extends below/above my
  depth-12 harness.
- Opus's R1 SPRT numbers quoted above; my matches are their third-tree counterpart.

## 7. What I did NOT do

- No second seed of M45 (the +16.9 is one seed; the interval is one-sided which is stronger, but
  the rule stands).
- No R1-without-CheckExtensionDepth decomposition (the bundle was the ask; the three parts'
  separate matches would say which line carries the 2k gain).
- The openings were REUSED from job 20 (lines 1–2000) as the job itself ordered — so M44/M45
  share their openings with M42/M43; the job's design, noted here.

## 8. What I am NOT sure about

- Whether R1's 2,000-node gain (+16.9) survives a second seed (the whole session's pattern says
  gains at low node counts grow; pv1's did, dramatically).
- Whether the 20,000-node level (+4.9) and the PC's mixed SPRT pair (+10.6/−0.65) are the same
  underlying truth (all three inside each other's widths).
- My M44 prediction's mechanism note mis-said "bigger tree" before correcting itself in the
  same line — the tree is SMALLER under R1 (8.33M vs 9.50M); the prediction's NUMBER was filed
  before the rows were seen, which is what matters.

## 9. A better way

- R1 is the first bundle of the session whose 2,000-node gain (+16.9) and 20,000-node level
  (+4.9) BOTH lean positive with the PC's independent +10.6 — a three-tree convergent picture.
  The cheapest sharpening: second seeds of M45 (2 min) and the PC's third seed — before anyone
  bundles R1 into a candidate.

## 10. UTC stamps

times: see stamps.txt (job read + patch extracted 15:41:1xZ, sha verified; applied + built
15:41:4xZ; step-0 rows 15:42:2xZ; prediction commit 0f94531eb at 15:42:01Z (pasted above);
probes 15:42:3xZ; M44 15:42:4xZ–15:54:2xZ (duration 11:44); M45 15:54:2xZ–15:55:54Z (duration
1:53); stats 15:55:5xZ; report after; commit stamped by git).

## 11. Real output of `git status --short` and `ls` of the folder (verbatim, 15:55:57Z)

```
=== git status --short:
?? forge-combo29/tests_glmflash5_job21/ChecksLmr.patch.txt
?? forge-combo29/tests_glmflash5_job21/M44_last40.txt
?? forge-combo29/tests_glmflash5_job21/M44_stdout.txt
?? forge-combo29/tests_glmflash5_job21/M45_last40.txt
?? forge-combo29/tests_glmflash5_job21/M45_stdout.txt
?? forge-combo29/tests_glmflash5_job21/b10_bench11.txt
?? forge-combo29/tests_glmflash5_job21/b10_bench13.txt
?? forge-combo29/tests_glmflash5_job21/b10_bench16.txt
?? forge-combo29/tests_glmflash5_job21/b10_perft5.txt
?? forge-combo29/tests_glmflash5_job21/cmd_M44.txt
?? forge-combo29/tests_glmflash5_job21/cmd_M45.txt
?? forge-combo29/tests_glmflash5_job21/config_M44.json
?? forge-combo29/tests_glmflash5_job21/config_M45.json
?? forge-combo29/tests_glmflash5_job21/exe_sha256_21.txt
?? forge-combo29/tests_glmflash5_job21/gamelist_M44.txt
?? forge-combo29/tests_glmflash5_job21/gamelist_M45.txt
?? forge-combo29/tests_glmflash5_job21/job21_rows.py
?? forge-combo29/tests_glmflash5_job21/job21_rows.txt
?? forge-combo29/tests_glmflash5_job21/job21_stats.py
?? forge-combo29/tests_glmflash5_job21/job21_stats_out.txt
?? forge-combo29/tests_glmflash5_job21/job21_summary.txt
?? forge-combo29/tests_glmflash5_job21/patch_apply.txt
?? forge-combo29/tests_glmflash5_job21/patch_dryrun.txt
?? forge-combo29/tests_glmflash5_job21/probe_M44.log
?? forge-combo29/tests_glmflash5_job21/probe_M45.log
?? forge-combo29/tests_glmflash5_job21/stamps.txt
=== ls tests_glmflash5_job21:
b10_bench11.txt
b10_bench13.txt
b10_bench16.txt
b10_perft5.txt
ChecksLmr.patch.txt
cmd_M44.txt
cmd_M45.txt
config_M44.json
config_M45.json
exe_sha256_21.txt
gamelist_M44.txt
gamelist_M45.txt
job21_rows.py
job21_rows.txt
job21_stats_out.txt
job21_stats.py
job21_summary.txt
M44_last40.txt
M44_stdout.txt
M45_last40.txt
M45_stdout.txt
patch_apply.txt
patch_dryrun.txt
prediction.txt
probe_M44.log
probe_M45.log
stamps.txt
```
(the `??` lines are the job folder's files before this commit — prediction.txt was already
committed by its own commit; the rest joins in this push.)

## 12. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
