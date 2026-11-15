# glmflash2 job 2 report (2026-11-15)

## 1. Result in plain words

**LmrDeeperShallower did NOT hold as a clear gain.** Its second match (new seed) gave +2.61 +/- 10.80
(2000 games) against job 1's +13.21 +/- 12.24; pooled over both matches (3,500 games, 1,750 pairs) it
is **+7.15 +/- 8.11, interval [-1.0, +15.3] - the interval contains 0**, so the honest reading is
"possible small gain, not shown". **No bundle is shown stronger than LmrDeeperShallower alone**: the
largest bundle point estimate is LmrDeeperShallower+ThreatHistory +10.2 +/- 11.7 (cut at 1846/2000
games), whose interval also contains 0; all six together gave -0.6/+/-11.0. Everything in this job is
inside its error except the control.

Also applied your correction: my old "my Elo +/- err" was 1 SE, fastchess prints the 95% interval
(1.96 SE). All "my" errors below are now 95% pair intervals; recomputed on the job-1 PGNs they match
your recount (LmrSignedCorrection job 1: -8.05, interval [-17.25, +1.15] = your -17.2 to +1.1).

## 2. Step 0, expected against printed (fresh process each; same engine build as job 1)

Same binary as job 1 (commit 6b98f217, built 14:08:08Z, source untouched since; I did not rebuild).

| check                      | expected | printed | file                          |
|----------------------------|----------|---------|-------------------------------|
| bench 11                   | 312866   | 312866  | step0/j2_bench11_base.txt     |
| bench 13                   | 862329   | 862329  | step0/j2_bench13_base.txt     |
| go perft 5                 | 4865609  | 4865609 | step0/j2_perft5_base.txt      |
| bench 13, bundle M1 (LDS)  | != 862329| 813907  | step0/j2_bench13_b1.txt       |
| bench 13, bundle M2 (LDS+TH)| != 862329| 926473 | step0/j2_bench13_b2.txt       |
| bench 13, bundle M3 (all 6)| != 862329| 672587  | step0/j2_bench13_b3.txt       |
| bench 13, bundle M4 (LDS+LPR+LSC)| != 862329| 726751 | step0/j2_bench13_b4.txt    |
| bench 13, bundle M5 (LDS+TH+EO+ACR)| != 862329| 794371 | step0/j2_bench13_b5.txt  |

All five bundle numbers differ from 862329; b1 reproduces job 1's LmrDeeperShallower bench exactly
(813907), so the switch still reaches the search the same way. Stamps: all Step 0 files written
15:24:53Z.

## 3. Control 2 (the power line), seed 7211, 300 games

- **A fault first, caught by the control itself.** My job-2 runner's control call was misconfigured
  by ME: it passed no per-engine `nodes`, so both sides ran at 20,000 nodes. Result: 86-86-128,
  score exactly 0.5000, Ptnml [0,0,150,0,0], Elo 0.00 - i.e. a control-1-shaped degenerate run with
  no power to detect anything. The control's expected "20,000 side clearly ahead" failed, which is
  how I found it. The faulty files are kept as evidence: matches/control2_7211_lines.txt (the
  degenerate one) and the fixed ones below. The fault was in my runner script, not in fastchess.
- **Corrected control 2** (nodes=20000 vs nodes=10000 given per engine, run by hand 15:44-15:47:30Z,
  alongside M2/M3): 20k side W 180 L 24 D 96 (76.00%), fastchess **Elo +200.24 +/- 32.47**,
  Ptnml [0,6,33,60,51]; my parser: identical W-L-D, pentanomial and point estimate, +200.24, 95%
  pair interval +/- 34.17. The tool can see a difference of this size; the job's power line stands.
  Files: matches/control2_7211_fastchess_out.txt, matches/control2_7211_lines.txt.
- Control 3 (option reaches engine) was proven in job 1 with the same fastchess and engine log
  mechanism; option strings in this job are the same form (`option.NAME=true`), and every bundle
  changed the bench nodes (section 2), which is an independent second proof that setoption reaches
  the engine for every switch in every bundle.

## 4. All eleven matches of jobs 1 and 2

Both jobs: same exe both sides, Threads 1, Hash 16, 20000 nodes, UHO_Lichess_4852_v1.epd, no
adjudication, concurrency 4 (4 cores), fastchess v1.8.3-alpha. "fc Elo" = fastchess's own final or
last-interim block; "my Elo" = logistic Elo from mean pair score with the 95% pair interval
(pgn_stats.py, validated: identical point estimates to fastchess on all seven computable matches).
Crashes/illegal/disconnects: 0 in every match of both jobs.

| job | #  | switches ON (cand side)                        | seed | games    | W-L-D       | Ptnml(0-2)              | fc Elo +/- err        | my Elo +/- 95% |
|-----|----|-----------------------------------------------|------|----------|-------------|-------------------------|-----------------------|----------------|
| 1   | M1 | ThreatHistory                                  | 7203 | 1441/1500| 423-405-613 | [36,176,286,178,44]     | +3.72 +/- 12.51 (1400g interim) | +4.34 +/- 12.29 |
| 1   | M2 | LmrSignedCorrection                            | 7204 | 1339/1500| 389-420-530 | [19,113,426,102,9]      | -6.65 +/- 9.72 (1200g interim) | -8.05 +/- 9.20 |
| 1   | M3 | LmrLateParentRelief                            | 7205 | 1500     | 415-439-646 | [45,188,305,170,42]     | -5.56 +/- 12.06       | -5.56 +/- 12.08 |
| 1   | M4 | LmrDeeperShallower                             | 7206 | 1500     | 471-414-615 | [37,171,294,194,54]     | +13.21 +/- 12.24      | +13.21 +/- 12.27 |
| 1   | M5 | EvasionOrdering                                | 7207 | 1498/1500| 412-429-657 | [45,187,297,180,40]     | -4.22 +/- 12.47 (1400g interim) | -3.94 +/- 12.10 |
| 1   | M6 | AspCappedReopen                                | 7208 | 1500     | 427-430-643 | [47,163,336,154,50]     | -0.69 +/- 12.06       | -0.69 +/- 12.07 |
| 2   | M1 | LmrDeeperShallower                             | 7221 | 2000     | 588-573-839 | [58,250,382,239,71]     | +2.61 +/- 10.80       | +2.61 +/- 10.80 |
| 2   | M2 | LDS + ThreatHistory                            | 7222 | 1846/2000| 586-532-728 | [60,203,359,225,76]     | +10.23 +/- 11.65 (1800g interim) | +10.17 +/- 11.51 |
| 2   | M3 | all six                                        | 7223 | 1915/2000| 545-554-816 | [55,234,386,229,53]     | -0.58 +/- 10.97 (1800g interim) | -1.63 +/- 10.65 |
| 2   | M4 | LDS + LPR + LSC                                | 7224 | 1488/1500| 440-421-627 | [38,179,302,176,49]     | +5.21 +/- 12.43 (1400g interim) | +4.44 +/- 12.15 |
| 2   | M5 | LDS + TH + EO + ACR                            | 7225 | 1201/1500| 343-323-535 | [34,145,223,163,35]     | +5.79 +/- 13.72 (1200g interim) | +5.79 +/- 13.74 |

**Pooled LmrDeeperShallower (job 1 M4 + job 2 M1)**: 3,500 games, 1,050 wins - 987 losses - 1,454
draws, Ptnml sum [95,421,676,433,125], **+7.15 +/- 8.11 (95% pair interval), [-1.0, +15.3]**.
Reading: interval contains 0 -> no difference shown, positive-leaning.

Job-2 status notes: M2/M3/M4 were cut at their time caps and M5 at the absolute deadline, each with
fastchess's own SIGINT summary ("Tournament was interrupted ... Finished match"), so the printed
interim blocks above are fastchess's own output and the games count from the PGNs. M1 completed its
2,000 games inside its cap.

Per-game line files committed: matches/<name>_lines.txt for every match above (job-2 matches and
control 2; the degenerate first control kept separately). PGNs stay in /tmp, not committed.

## 5. Part B

Not done: this job file has no part B.

## 6. Files of the repository I opened

- Only the job file, via `git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_glmflash2_2.md`
  (handoff branch, read-only). No repository source file was opened this time; the build and its
  flags were carried over from job 1 (forge-combo29/CMakeLists.txt, read in job 1).

## 7. Start and end of each step (recorded stamps, UTC)

- 15:24:00Z  job 2 file read (fetched 15:24:21Z).
- 15:24:53Z  Step 0 done (8 bench/perft files written).
- 15:25:30Z -> 15:26:20Z  two SIGINT graceful-stop tests (sigtest.sh, sigtest2.sh; committed).
- 15:26:27Z  runner2.sh launched; its control call (faulty, see section 3) 15:26:27->15:28:18.
- 15:28:18Z -> 15:39:49Z  M1, complete, 2000 games.
- 15:39:49Z -> 15:52:55Z  M2, cut at 780 s cap by SIGINT, 1846 games (my corrected control 2 ran
  beside it 15:44->15:47:30).
- 15:52:55Z -> 16:06:02Z  M3, cut at 780 s cap by SIGINT, 1915 games.
- 16:06:02Z -> 16:15:48Z  M4, cut at 580 s cap by SIGINT, 1488 games.
- 16:15:48Z -> 16:23:44Z  M5, cut at the absolute 16:23:30Z deadline by SIGINT, 1201 games.
- 16:24Z -> ~16:34Z  stats, report, commit, push.

## 8. What I did NOT do

- The five job-2 matches were sized 2000/2000/2000/1500/1500; M2, M3, M4 and M5 finished short of
  their targets (1846, 1915, 1488, 1201) because my per-match caps were set from job 1's rate
  (~2.9 games/s) and the real rate during this job was lower once my corrected control 2 ran beside
  the runner (and M3/M4 sit in the ~2.4-2.9 band). The job wanted only the LAST match cut; I did not
  manage that. All four are INCOMPLETE with fastchess's own interim summaries.
- No SPRT, no other node caps, no pairwise bundle-vs-bundle matches (only bundle vs OFF as asked).
- No PGN, binary or engine source committed; no PR opened; no review bot appeared.

## 9. What I am NOT sure about

- The pooled LmrDeeperShallower interval [-1.0, +15.3] contains 0 by 1.0 Elo. I cannot call it a
  gain and I cannot call it nothing; the PC retest at longer TC is the decider. Its two matches
  (+13.21 seed 7206, +2.61 seed 7221) differ by more than either error - consistent with a small
  true effect plus seed noise, also consistent with 0.
- M2 (LDS+TH) at +10.2 +/- 11.7 is the largest bundle point estimate, but it is 154 games short and
  its interval contains 0; I do not claim it beats LDS alone. If you want that decided, it needs a
  full 2000-game rerun with a bigger cap.
- My control 2 ran concurrently with matches (shared 4 cores). Fixed-node searches are not affected
  by load for their node counts, but wall-clock pacing of my caps was; the games themselves are
  valid. I did not re-run any match without that overlap.
- The degenerate first control (both sides 20000 nodes) is evidence about my runner only; I did not
  use its numbers anywhere.

## 10. A better way

- SIGINT beats SIGTERM/timeouts for cut matches, verified twice before use: fastchess stops
  scheduling, lets in-flight games finish, prints a normal summary block and writes the PGN; the
  cut match keeps its own Elo line. Job 1's `timeout` kills lost that. Use deadline-SIGINT for
  every match, as this job prescribed - I second it from test evidence (sigtest2.sh: SIGINT at 12 s,
  clean exit, 32 games in PGN and summary).
- Pooling two matches of one switch is cheap and sharp: pair counts just add (1,750 pairs give
  +/- 8.1 where each match alone gives +/- 11-12). My pgn_stats.py now takes several PGNs and pools
  by (file, round); the round-tag pairing matters because PGN order is completion order under
  concurrency, not round order.
- Runner pattern learned the hard way: per-engine settings (like the control's unequal nodes) need
  their own engine-spec path in the runner; my single-template runner silently flattened the
  control into base-vs-base. The control caught it, which is exactly what control 2 is for.

## 11. Model name and version

I am glmflash2, running on GLM, model glm-5p3-flash (GLM 5.3 Flash) as far as I know it.
