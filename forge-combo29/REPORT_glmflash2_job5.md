# glmflash2 job 5 report (2026-11-15)

## 1. Result in plain words

**The gain of packc28 shrinks with depth, and strongly.** Per node: **5,000 nodes +41.5 +/- 9.7**
(M1, 2,993/3,000 games, my 95% pair interval; fastchess +39.91 +/- 9.99), **20,000 nodes +18.7**
(the known two-helper result, not replayed), **80,000 nodes +23.7 +/- 14.1** (M2, the full 1,000
games; fastchess agrees to the tenth). So the drop happens between 5,000 and 20,000 nodes; from
20,000 to 80,000 the intervals overlap and no further shrink is shown - one full seed plus a token
second slice, not proof of a flat tail. **Cut or not reached, first paragraph as asked:** M1 was cut
by its cap with 7 games missing; **M2 COMPLETED all 1,000 games** (the job's "M3 is cut, not M2"
rule - I had to freeze the runner's controller so its baked cap could not cut M2, see section 7);
M3 got only the token remainder (150 of 1,000 games, cut at the 20:22 deadline); **M4 was NOT RUN**
(98 s would have been left - below my 330 s minimum, the runner logged M4_SKIPPED).

## 2. The wrapper check (the four options are not in `uci`)

- The patch's `uci` answer does NOT list AspFailHighReduce / AspFailHighMaxReduce / EvalSwingMult /
  EvalSwingMax (grep count 0 over the full option list; step0/uci_list.txt) - as the job said, so
  the cand side runs through a wrapper script that prints the four `setoption` lines and then passes
  everything on to the engine (runner5.sh, wrapper_packc28.sh; both committed).
- Known answer: `bench 13` through the wrapper prints **690187** exactly
  (step0/bench13_wrapper.txt; re-checked again after the wrapper gained its own evidence log).
- Evidence per match: from 19:24:46Z the wrapper appends every line it sends, with a timestamp, to
  its own log (wrapper_sent.log, 4 option lines per engine start; kept outside the repo, excerpt in
  the report below). fastchess's engine log does NOT record the wrapper's pre-handshake output - I
  found that on M1's probe (its count file says 0) and fixed the evidence gap before M2.
- The patch carries a FIFTH switch, TtCutoffHistory, which my matches never set (stays 0); the four
  set here are the job's four.

## 3. The probes (before every match)

Each probe = the match's exact command, 2 games, engine input log on; same seed as its match, so the
probe's two FENs are the match's first pair. Evidence committed: matches/<name>_probe_openings.txt
and (for M2-M4) the wrapper-lines count files; M1/control's count files read 0 for the reason above.

| match | probe first FEN == match round-1 FEN | openings differ across matches |
|-------|--------------------------------------|--------------------------------|
| control_7250 | yes | yes: four distinct first pairs (control rnbq1rk1/pp1nppbp..., M1 r2qkb1r/ppp1pppp..., M2 r2qk2r/p1pp1pp1..., M3 its own) |
| M1 | yes | |
| M2 | yes | |
| M3 | yes | |
| M4 | not run (match skipped) | |

The "second seed replays the first match" fault did not happen: every match drew different openings.
Wrapper option delivery, per match: the wrapper's own timestamped log (copied to
matches/wrapper_sent_evidence.log, 13 wrapper-start entries) shows the four setoption lines sent at
every wrapper start from 19:24:46Z on (my two bench checks, M2's probe and match, M3's probe and
match - M1 ran with the wrapper version that did not yet keep this log).

## 4. Step 0 (expected against printed)

Build: clean export of d4f43124 (root tree), packc28_port.patch applied with `patch -p1 --fuzz=0`
(113 lines, one hunk each in search.cpp; logs kept), CMake Release, g++ 13.3.0,
`-DCMAKE_CXX_FLAGS="-DFORGE_NNUE_HIDDEN=256"`, no -march (tree default), FORGE_EXPOSE_TUNABLES off.

| check | expected | printed | file |
|-------|----------|---------|------|
| bench 11, no options | 312866 | 312866 | step0/bench11_off.txt |
| bench 13, no options | 862329 | 862329 | step0/bench13_off.txt |
| go perft 5 | 4865609 | 4865609 | step0/perft5_off.txt |
| bench 13 through wrapper | 690187 | 690187 | step0/bench13_wrapper.txt |

## 5. All matches (same exe both sides; cand = wrapper with the four options, base = plain; no adjudication)

Machine: 4 cores, concurrency 4, fastchess v1.8.3-alpha, UHO book. Crashes/illegal/disconnects: 0 in
every match (grep over each full output).

| #  | match | nodes | seed | games | W-L-D | Ptnml(0-2) | fc Elo +/- err | my Elo +/- 95% | crashes |
|----|-------|-------|------|-------|-------|------------|----------------|----------------|---------|
| C  | control 20k vs 10k, no options | 20k/10k | 7250 | 300 | 181-22-97 | [1,5,30,62,52] | +205.04 +/- 33.36 | +205.04 +/- 35.19 | 0 |
| M1 | packc28 ON vs OFF | 5000 | 7251 | 2993/3000 | 1161-806-1026 | [90,265,537,407,197] | +39.91 +/- 9.99 | +41.54 +/- 9.65 | 0 |
| M2 | packc28 ON vs OFF | 80000 | 7252 | 1000 | 283-215-502 | [17,103,203,149,28] | +23.66 +/- 14.07 | +23.66 +/- 14.13 | 0 |
| M3 | packc28 ON vs OFF | 80000 | 7253 | 150/1000 | 45-38-67 | [1,18,31,23,2] | (none: killed at the graceful-stop timeout before its summary) | +16.23 +/- 33.39 | 0 |
| M4 | packc28 ON vs OFF | 5000 | 7254 | NOT RUN | - | - | - | - | - |

(The 20,000-node point stands from the two helpers: +18.7 per node, two seeds; not replayed here.)

## 6. Files of the repository I opened

- The job file (git show on the handoff branch).
- packc28_port.patch (read in full, 113 lines: P8 = root fail-high re-search at depth reduced by
  min(consecutive fail-highs, AspFailHighMaxReduce); P9 = the parent quiet move's eval swing, clamped
  to +/-EvalSwingMax, times EvalSwingMult/16, fed into the parent mover's main history; P10 =
  TtCutoffHistory history update on TT fail-highs - left 0; plus FORGE_ASP_STATS debug counters,
  compile-time only).
- src/uci.cpp of the export (grep only, for the option-registration path).
No other repository file opened.

## 7. Start and end of each step (recorded stamps, UTC)

- 19:11:54Z  job 5 file found; read 19:12:0xZ.
- 19:12:1xZ  branch opus-r13-p1-nearmiss-ports fetched (tip 759acc6dc), patch extracted and applied
  (zero fuzz), export built (BUILD_OK), patch read.
- 19:12:4xZ  Step 0: OFF 312866 / 862329 / 4865609; uci lists none of the four options; wrapper
  bench 13 = 690187 (first wrapper version was wrong - it replaced itself with `cat` and never
  started the engine; output was only my echoed input. Rewritten to pipe into the engine).
- 19:12:45Z  first runner launch - matches died at once ("Error; no TimeControl specified!"): my
  refactored run_one again dropped the per-engine nodes variables from the fastchess line. Fixed.
- 19:14:21Z  runner relaunched clean (timeline cleared; the false start cost ~100 s).
- 19:14:2xZ -> 19:16:3xZ  probe C + control 7250 (300 games, +205.04).
- 19:19:34Z -> 19:32:29Z  probe M1 + M1 (cut at 700 s cap, 2993/3000 games).
- 19:32:3xZ -> 20:16:52Z  probe M2 + M2 (80k nodes): the match ran PAST its baked 1750 s cap. The
  job's rule "M3 is cut, not M2" made me freeze the runner's controller with SIGSTOP at 19:49:56Z
  (its cap would have SIGINTed M2 at ~20:03 with ~880 games); M2 then finished all 1,000 games by
  itself at ~20:16:4xZ; I resumed the controller (SIGCONT 20:16:52Z), it wrote M2's files and moved
  on. M2's rate was 0.40-0.46 games/s, not the 0.72 I had sized the cap from.
- 20:18:57Z -> 20:25:22Z  probe M3 + M3 (cap 308 s = the remainder to the 20:22:00Z deadline):
  150 games; the SIGINT came at ~20:24, the graceful stop exceeded its 75 s wait with 80k games in
  flight, fastchess was killed before it could print a summary - games counted from the PGN.
- 20:25:22Z  M4_SKIPPED (98 s left < 330 s minimum), RUNNER5_DONE.
- Report finalized 20:26-20:31Z, committed and pushed by ~20:32Z.

## 8. What I did NOT do

- I did not replay the 20,000-node point (the job said not to; it is the two helpers' +18.7).
- M4 was not run: after M3 there were 98 s left; my runner skipped it by its own logged rule
  (M4_SKIPPED). The second shallow seed therefore does not exist.
- M3 is a token 150 games (its planned 1,000 did not fit once M2's true rate was known); it has no
  fastchess summary block (killed at the graceful-stop timeout) - its counts come from the PGN, my
  Elo line is computed from those 75 pairs.
- The wrapper's per-match option evidence exists only from 19:24:46Z on; for M1 the proof that the
  options acted is the wrapper known-answer bench (690187) plus the measured effect itself (+40 Elo
  and a very different pair structure than OFF-play).
- No SPRT, no fourth node point, no engine source committed, no PR opened.

## 9. What I am NOT sure about

- The 5,000-node point rests on ONE seed (M4 may add the second if the clock allowed). Its +41.5 is
  far outside the known +18.7 at 20k, so the DIRECTION of the curve is safe, but the exact shallow
  number is one seed's word.
- The 80k point rests on M2's single full seed (+23.7 +/- 14.1) plus M3's token 150 games (+16.2
  +/- 33.4, direction only). Whether the curve is flat from 20k to 80k or still falling cannot be
  resolved by what I ran; the PC's +10 at 250k suggests it keeps falling.
- The 20k comparison leans on the other helpers' +18.7 measured on THIS tree by two of them; I did
  not re-derive its error bar. My curve claim "the drop is between 5k and 20k" treats their number
  as given.
- The wrapper sends the four options BEFORE `uci`; the engine accepts them (the 690187 check), but I
  did not test whether a stricter engine would reject that order. For THIS engine and THIS patch the
  check is direct.
- fastchess treats the wrapper as the engine; the wrapper's stdout lines (the four setoptions) are
  read by fastchess as engine output and ignored. I did not observe any harm (0 crashes everywhere),
  but a pickier GUI could object.
- The SIGSTOP/SIGCONT freeze of the runner controller is a deviation I chose to honor "M3 is cut,
  not M2"; it worked as watched, but a frozen controller also cannot react to anything else while
  frozen (nothing else needed reacting here).

## 10. A better way

- The same refactor bug bit me twice (jobs 4 and 5: per-engine `nodes` dropped from the fastchess
  line when I reshaped run_one). Rule for my future runners: the fastchess command line is built by
  ONE function that takes the full engine spec as a single quoted string per side, and a smoke probe
  MUST print its header line (fastchess echoes "20000 nodes - 10000 nodes" in the results block)
  before the runner proceeds. The control match first, every time, caught it both times.
- When a baked cap would cut the wrong match (here: M2, because its real rate was half my estimate),
  SIGSTOP the runner's controller: the match keeps playing, the controller cannot fire its SIGINT,
  and SIGCONT after the match's natural end lets the runner carry on with the rest of its schedule.
  Verified once here (M2 completed all 1,000 games); it needs the controller's PID and a watcher,
  and it only makes sense when later matches have absolute deadlines anyway.
- Wrapper evidence: fastchess's engine log silently misses pre-handshake output, so a wrapper that
  must prove what it sent should keep its own timestamped log - cheap, and it turns "the options
  were probably sent" into a file.
- The 5k games run at ~4.3 games/s (2,993 in ~770 s wall), not the 4x-of-20k I first estimated;
  fixed per-move overheads dominate at shallow nodes. Size shallow-node match caps from a measured
  probe rate, not from the node ratio.

## 11. Model name and version

I am glmflash2, running on GLM, model glm-5p3-flash (GLM 5.3 Flash) as far as I know it.
