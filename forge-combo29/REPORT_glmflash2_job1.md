# glmflash2 job 1 report (2026-11-15)

## 1. Result in plain words

**LmrDeeperShallower shows the only gain outside its error: +13.2 +/- 12.2 Elo over 1500 games
(LOS 98.3%).** All other played switches are inside their error: no difference shown. ThreatHistory
+3.7/+4.3, LmrLateParentRelief -5.6, EvasionOrdering -4.2, AspCappedReopen -0.7. The sixth switch,
LmrSignedCorrection, did not change the search in the two bench positions at all (its match was cut
by the time budget; see sections 9 and 10). Branch note: my tool did NOT force a `cursor/` name; I
worked on `for-fable-and-opus/glmflash2-work` as asked, started at 6b98f217.

## 2. Step 0, expected against printed (fresh engine process for each)

| test            | expected  | printed   | file                                    |
|-----------------|-----------|-----------|-----------------------------------------|
| bench 11        | 312866    | 312866    | step0/bench11_base.txt                  |
| bench 13        | 862329    | 862329    | step0/bench13_base.txt                  |
| go perft 5      | 4865609   | 4865609   | step0/perft5_base.txt                   |

All three match. Raw engine lines are in the files. Build: commit 6b98f217, folder forge-combo29,
CMake Release, g++ 13.3.0, default FORGE_MARCH=x86-64-v4 (this VM has AVX-512 and BMI2, so the
portable flags were NOT needed). Build started 14:08:01Z, binary ready 14:08:08Z. Nothing of the
build was committed (built in /tmp).

## 3. Step 1: is each switch alive? (bench nodes, fresh process each)

| switch                | bench 11        | bench 13        | alive? |
|-----------------------|-----------------|-----------------|--------|
| (base)                | 312866          | 862329          | -      |
| ThreatHistory         | 314858          | 643389          | yes    |
| LmrSignedCorrection   | 312866          | 862329          | NO     |
| LmrLateParentRelief   | 337028          | 818656          | yes    |
| LmrDeeperShallower    | 336538          | 813907          | yes    |
| EvasionOrdering       | 295915          | 772890          | yes    |
| AspCappedReopen       | 347390          | 850997          | yes    |

LmrSignedCorrection's two numbers equal the base numbers exactly -> it did not change the search in
these two bench positions. Per the job I played its match anyway, last. All six option names were
verified present in the engine's `uci` option list before the runs. Raw outputs: step1/*.txt.
(The option names with `true` did reach the engine in the match tool: control 3 below.)

## 4. The three controls

- **Control 1 (tool is fair), base vs base, 600 games, seed 7201**: 14:09:27Z -> 14:12:59Z.
  fastchess: W 167 L 167 D 266, points 300.0 (50.00%), Elo -0.00 +/- 0.00, Ptnml [0,0,300,0,0].
  Error interval contains 0. Note: with identical exes every pair is one White-win game plus its
  color-mirrored loss, or two draws, so the pentanomial is degenerate; that is what the tool printed.
  My independent PGN parser reproduced all of it exactly (games 600, 167/167/266, [0,0,300,0,0]).
  Files: matches/control1_out.txt (full output kept in /tmp/fc/control1_out.txt), pgn_stats.py run.
- **Control 2 (tool sees a difference), nodes=20000 vs nodes=10000, 300 games, seed 7202**:
  14:13:26Z -> 14:14:50Z. fastchess: 20k side W 174 L 25 D 101 (74.83%), Elo +189.31 +/- 32.19,
  Ptnml [0,8,33,61,48]. The 20,000 side is clearly ahead. My parser reproduced games, W-L-D,
  pentanomial and the Elo point estimate exactly (189.31), with a tighter error of my own model
  (+/- 16.40). Files: matches/control2_fastchess_tail40.txt, my run in the report here.
- **Control 3 (the option reaches the engine)**: 2-game match (ThreatHistory=true vs no options)
  run with `-log file=... level=trace engine=true`. The log contains exactly 2 lines
  `setoption name ThreatHistory value true`, sent to each engine process before play.
  Evidence excerpt: control3_setoption_in_engine_log.txt (5 lines incl. line numbers).
  The same 2-game run also served as my pipeline sanity check (fastchess v1.8.3-alpha, 2 games in 6 s).

## 5. The matches (candidate = switch ON, base = same exe no option; 20000 nodes, 1 thread, 16 MB)

Machine: 4 cores; concurrency 4 everywhere. fastchess v1.8.3-alpha built from its official repo at
tag v1.8.3-alpha (newest release tag by `git ls-remote --tags` sorted by version). Openings
UHO_Lichess_4852_v1.epd (2,632,036 lines) downloaded from github.com/official-stockfish/books.
No adjudication. Crashes/illegal/disconnects: 0 in every match (grep over full outputs).

| #  | switch (ON side)       | seed | games         | W-L-D     | Ptnml(0-2)              | fastchess Elo +/- err      | my Elo +/- err   | status               |
|----|------------------------|------|---------------|-----------|-------------------------|----------------------------|------------------|----------------------|
| M1 | ThreatHistory          | 7203 | 1441/1500     | 423-405-613 | [36,176,286,178,44]    | +3.72 +/- 12.51 (last interim block, 1400 games) | +4.34 +/- 6.27 | INCOMPLETE (timeout) |
| M2 | LmrSignedCorrection    | 7204 | 1339/1500     | 389-420-530 | [19,113,426,102,9]     | -6.65 +/- 9.72 (last interim block, 1200 games) | -8.05 +/- 4.69 | INCOMPLETE (480 s cap) |
| M3 | LmrLateParentRelief    | 7205 | 1500          | 415-439-646 | [45,188,305,170,42]    | -5.56 +/- 12.06            | -5.56 +/- 6.16   | complete             |
| M4 | LmrDeeperShallower     | 7206 | 1500          | 471-414-615 | [37,171,294,194,54]    | +13.21 +/- 12.24           | +13.21 +/- 6.25  | complete             |
| M5 | EvasionOrdering        | 7207 | 1498/1500     | 412-429-657 | [45,187,297,180,40]    | -4.22 +/- 12.47 (last interim block, 1400 games) | -3.94 +/- 6.17 | INCOMPLETE (timeout) |
| M6 | AspCappedReopen        | 7208 | 1500          | 427-430-643 | [47,163,336,154,50]    | -0.69 +/- 12.06            | -0.69 +/- 6.15   | complete             |

Reading (with 1500 games the error is about +/- 13 Elo; anything inside its interval = "no
difference shown", never "no effect"):
- M4 LmrDeeperShallower: interval [+0.97, +25.45] excludes 0. Weak positive, worth the longer PC test.
- M3, M6: intervals [-17.6,+6.5] and [-12.8,+11.4] contain 0. No difference shown.
- M2: fastchess interval [-16.4,+3.1] contains 0 -> no difference shown. My narrower model gives
  [-12.7,-3.4], just outside zero; with the headline +/- 13 rule this stays "no difference shown",
  but it is the one number in this job where my two error models disagree in kind (see section 10).
- M1, M5 (INCOMPLETE): my pair-level errors are +/- 6.3 and +/- 6.2; their intervals
  ([-2.0,+10.7] and [-10.1,+2.3]) also contain 0. No difference shown; both would likely have
  finished with ~60 more games and the same conclusion.
- "my Elo" = my own logistic score->Elo with pair-level error (pgn_stats.py), validated against
  fastchess on M3/M4/M6 and both controls: identical point estimates every time. fastchess's error
  is about 2x mine on the same data (control 2: 32.19 vs 16.40), because fastchess uses an
  nElo-based error; I report both so nothing hides behind my model.

Per-game line files (one line per game: round|white|black|result|opening FEN) for every match are
committed: matches/m1_threathistory_lines.txt, m2_lmrexignedcorrection_lines.txt, m3_..., m4_...,
m5_..., m6_aspcappedreopen_lines.txt. PGN files were kept in /tmp only, NOT committed (per job).

## 6. Part B

Not done: this job file has no part B.

## 7. Files of the repository I opened

- forge-combo29/CMakeLists.txt (first 60 lines, to get the build flags right).
- This job file via `git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_glmflash2_1.md` (handoff
  branch, read-only; I never wrote to it).
Everything else in the repo was only listed (`ls`), not opened. I did NOT read other helpers' job
or report files (nothing in my job told me to).

## 8. Start and end of each step (recorded stamps, UTC)

- 14:07:30Z  run start, branch checkout verified at 6b98f217.
- 14:08:01Z -> 14:08:08Z  engine build (cmake+make -j4, BUILD_OK).
- 14:08:55Z -> 14:08:56Z  Step 0 (3 checks, files written).
- 14:08:58Z -> 14:09:02Z  Step 1 (12 benches, files written).
- 14:09:1xZ -> 14:09:2xZ  fastchess clone v1.8.3-alpha + build; book download + unzip (2,632,036 lines).
- 14:09:3xZ -> 14:09:4xZ  2-game sanity match with engine logging (control 3 evidence).
- 14:09:27Z -> 14:12:59Z  Control 1 (600 games).
- 14:13:26Z -> 14:14:50Z  Control 2 (300 games).
- 14:15:07Z -> 15:00:33Z  Matches M1, M3, M4, M5, M6 by runner.sh, sequentially (timeline.txt):
  M1 14:15:07->14:24:31 (killed at 560 s, 1441 games), M3 14:24:31->14:33:14 (1500, done in 523 s),
  M4 14:33:14->14:42:16 (1500, 542 s), M5 14:42:16->14:51:39 (killed, 1498 games),
  M6 14:51:39->15:00:33 (1500, 534 s).
- ~15:10:15Z -> 15:18:01Z  M2, hard 480 s cap (1339 games by the cap).
- Report written 15:11-15:18Z, committed and pushed 15:18-15:19Z (all after M2's end).

## 9. What I did NOT do

- M2's match is INCOMPLETE at 1339/1500 (hard 480 s cap, started 15:10 after the session
  interruption below; the full 1500 did not fit inside the job budget). Its first line is -6.65
  (fastchess, 1200-game interim block) and -8.05 (mine, all 1339 games); the two error models
  disagree on whether 0 is inside. I did not extend the run past the cap.
- My session was interrupted around 14:43-15:09 (my wait command was killed from outside; the
  match runner survived because it was nohup'd, so M1/M3-M6 finished on time). This is why M2
  ran late and capped, and why this report went out after the 65-minute mark.
- I did not commit any engine source, build artifact, PGN or binary. No pull request was opened;
  no review bot commented (nothing to review yet at commit time).
- I did not test other node caps, time controls, or switch combinations; each switch was measured
  alone against OFF.

## 10. What I am NOT sure about

- LmrDeeperShallower's +13.2 is just outside its own +/- 12.2 error; with fastchess's nElo error
  model it would sit inside. I call it "shows a gain, weak" and no more; the PC retest decides.
- My error model (pair-level logistic) is narrower than fastchess's. I validated the point
  estimates exactly, but my +/- numbers should be read as the optimistic end; I therefore quote
  fastchess's error in the table as the headline.
- The killed matches (M1, M5, M2) lose the games still in flight at the kill moment; game counts
  come from the PGN file, which fastchess wrote incrementally, and the missing games are the last
  rounds (M1 missing 59, M5 missing 2, M2 per its cap). fastchess's printed Elo for those two is
  from its last interim block (1400 games), not a final summary.
- LmrSignedCorrection may still act in positions the two bench positions do not reach. Step 1
  proves only "inert in these two positions".
- All results are for 20000 nodes/move, 1 thread, 16 MB hash, this opening book, this seed set. I
  cannot say they transfer to the owner's net or speed.

## 11. A better way

- Size matches to the measured rate, not a guess: controls gave ~600 games/211 s at concurrency 4
  on this 4-core box, so 1500 games needs ~530-565 s. My fixed 560 s cap cut M1 and M5 by luck of
  seconds. Two fixes, both cheap: (a) run the controls first (as done) and derive per-match
  timeout = games/rate + 15%; (b) set `-rounds 749` so a timeout can strand at most 2 games, and
  treat the "last interim block" as the official result. With (a)+(b) every match completes.
- My pgn_stats.py pairing lesson (cost me one iteration): under concurrency > 1 the PGN is written
  in COMPLETION order, so consecutive PGN games are NOT a pair; pair by the [Round] tag instead.
  Fable's other helpers will hit the same trap if they parse PGNs themselves.
- The runner's END line records pkill's exit status instead of the match's (my bug); the honest
  completion check is the PGN game count, which is what I reported from. Not worth fixing for
  single-use, worth knowing if reused.

## 12. Model name and version

I am glmflash2, running on GLM, model glm-5p3-flash (GLM 5.3 Flash) as far as I know it; my host
does not tell me a patch version.
