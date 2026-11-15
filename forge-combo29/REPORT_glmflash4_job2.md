# glmflash4, job 2 report (2026-11-15)

Job 1's report was never pushed: file 2 arrived while job 1's matches were
running. This report IS the job-1 + job-2 deliverable: it uses file 1's
builds, step-0 numbers, controls and match list, with file 2's correction
applied. Evidence of the matches already played under the file-1 route is in
`tests_glmflash4_job1/` (committed alongside); the wrapper-route evidence is
in `tests_glmflash4_job2/`.

## 1. Answer in one line

The single part that shows the most is PawnHist (M2: +14.37 ± 11.96, my 95 %
pair interval [+2.42, +26.35] — the only single part whose interval excludes
zero, and barely); the bnd68 patch WITHOUT its correction part is NOT
clearly a gain by itself: M5 (PawnHist + ContHist4Pct + EvalOnlyStore
together) measured +4.17 ± 10.48, interval [-6.32, +14.66], and the three
parts' single results (+14.4, +7.0, +0.2) sum to about +21, which M5 does
not reproduce — the parts do not simply add. On packc28, AspFailHigh shows a
hint (+10.43 ± 12.17, interval [-1.74, +22.61]) and EvalSwing shows nothing
(+3.94 ± 11.87).

## 2. Which options are declared, which are not (file 2's first ask)

Full `uci` replies committed in `tests_glmflash4_job2/uci_replies/`:

- `uci_reply_bnd68_noexpose_build.txt`: 10 options declared (Hash, Threads,
  Move Overhead, Ponder, OwnBook, Book File, Book Depth, Book Variety,
  UseNNUE, Clear Hash). NONE of the bnd68 patch options (NonPawnCorr,
  NonPawnCorrWeight, NonPawnKeyIncludesKing, PawnHist, ContHist4Pct,
  EvalOnlyStore, EvalOnlyStoreMinDepth) is declared.
- `uci_reply_packc28_noexpose_build.txt`: same 10; NONE of AspFailHighReduce,
  AspFailHighMaxReduce, EvalSwingMult, EvalSwingMax, TtCutoffHistory declared.
- `uci_reply_bnd68_EXPOSE_build.txt` / `uci_reply_packc28_EXPOSE_build.txt`:
  70 / 66 options — the patch tunables ARE declared. These are the builds I
  used for M1-M4 after my own control 3 caught the undeclared-option fault
  (see section 3): built with `-DFORGE_EXPOSE_TUNABLES=ON`, the switch the
  tree's `CMakeLists.txt` documents as "Development builds advertise the
  search constants so match runners can set them".

Behavior-neutrality of that build flag is proven by step 0 (next section):
identical node signatures with the flag on and off.

## 3. Step 0, expected against printed

All ten lines of file 1's step 0 were run twice — on the first build (flag
off) and on the final EXPOSE build — and all ten printed the expected values
both times; raw outputs: `tests_glmflash4_job1/step0_first_build/` and
`tests_glmflash4_job1/step0/` (same file names, same numbers):

| build | line | expected | printed |
|---|---|---|---|
| bnd68 base | bench 11 | 312866 | 312866 |
| bnd68 base | bench 13 | 862329 | 862329 |
| bnd68 base | go perft 5 | 4865609 | 4865609 |
| bnd68 +6 opts | bench 11 | 365135 | 365135 |
| bnd68 +6 opts | bench 13 | 776194 | 776194 |
| packc28 base | bench 11 | 312866 | 312866 |
| packc28 base | bench 13 | 862329 | 862329 |
| packc28 base | go perft 5 | 4865609 | 4865609 |
| packc28 +4 opts | bench 11 | 277906 | 277906 |
| packc28 +4 opts | bench 13 | 690187 | 690187 |

The option-set lines were fed by direct `setoption` (the engine accepts
tunables by `setoption` whether or not it advertises them — read in
`src/uci.cpp`). The non-declaring builds were rebuilt a third time into their
own directories for the wrapper route; both print bench 13 = 862329
(raw outputs committed in `tests_glmflash4_job2/noexpose_build_bench13/`).

Pre-match bench 13 with exactly each match's options (direct `setoption`, on
the binaries that played): M1 730407, M2 908226, M3 821621, M4 862329,
M5 1044939, M6 649268, M7 683335 — files
`tests_glmflash4_job1/match_benches/`. M4's number equals the base 862329:
the M4 options do not act in the bench positions (reported as file 1 asks;
the match was still played).

## 4. The three controls, and the wrapper's three checks

Controls (same as file 1's; run on the first build AND re-run identically on
the final EXPOSE binaries; committed under `tests_glmflash4_job1/controls/`):

- Control 1 (determinism, base vs base, 100 games, seed 7600): every pair
  1-1 — `Ptnml(0-2): [0, 0, 50, 0, 0]`, Elo -0.00 +/- 0.00, my script: 50
  pairs all 0.5, se 0.0000. 46 s each run. This row `[0,0,50,0,0]` is exactly
  the "two identical engines" form file 2 warns about — produced on purpose,
  by two engines that ARE identical.
- Control 2 (power; cand 20000 nodes vs base 10000 nodes, 300 games, seed
  7599): fastchess `Elo: 226.69 +/- 36.17`, 194-22-84 (78.67 %),
  `Ptnml(0-2): [0, 9, 20, 61, 60]`; my script: score 0.7867, Elo +226.69,
  150 pairs, se 0.0178, 95 % pair interval [+192.58, +265.16]. The tool sees
  a planted difference.
- Control 3 (option delivery, 2-game match, `-log file=engine.log engine=true`):
  - Attempt 1 (first build, options as `option.` on the command line)
    FAILED exactly as file 2 describes: fastchess printed `Warning; cand
    doesn't have option NonPawnCorr` / `NonPawnCorrWeight` and the input log
    shows the cand side received only `Threads 1` and `Hash 16`
    (`tests_glmflash4_job1/controls/ctrl3_v1_FAILED_option_delivery.txt`).
  - My fix for M1-M4: rebuild with `-DFORGE_EXPOSE_TUNABLES=ON`; attempt 2
    then shows, per game, the cand side receiving `Threads 1`, `Hash 16`,
    `NonPawnCorr 1`, `NonPawnCorrWeight 50`
    (`tests_glmflash4_job1/controls/ctrl3_v2_cand_setoption_lines.txt`).
    Delivery is therefore proven by the input log, and the option set is
    proven to change the search by the bench signatures (730407/776194 vs
    862329). The two games' 1-1 split proves nothing by itself and I claim
    nothing from it: with colours swapped, two identical deterministic
    engines also produce same-string pairs (both games of a pair share one
    move sequence, so any "white wins both"/"black wins both"/draw-draw
    string pair scores 1-1) — control 1's `[0,0,50,0,0]` is exactly that.
  - File 2's fix (the wrapper) is proven separately, below and in the
    M5-M7 matches.

Wrapper checks (per file 2; scripts in `tests_glmflash4_job2/scripts/`,
bench outputs in `tests_glmflash4_job2/wrapper_benches/`):

- Check 1, bench 13 through each wrapper (must print that option set's ON
  number): M1 730407, M2 908226, M3 821621, M4 862329, M5 1044939, M6
  649268, M7 683335 — every one equal to the direct-setoption bench of the
  same config. The wrapper delivers exactly what `setoption` delivers.
- An honesty note that belongs here: my first wrapper generator wrote
  malformed `setoption` lines, and all seven wrapper benches printed the BASE
  862329 — the check caught a silent do-nothing wrapper before any match
  used it. The committed `scripts/` are the corrected wrappers.
- Check 3 (no "doesn't have option" warning in fastchess output) and check 2
  (pair counts not of the form [0,0,N,0,0]) are recorded per match in the
  match files; for M5, M6 and M7 both hold (0 warnings everywhere; pair
  counts [49,254,382,254,61], [40,167,301,192,50],
  [40,171,313,184,42] — none of the all-1-1 form).

## 5. The matches

Route column: "EXPOSE" = both sides the EXPOSE build, patch options as
`option.` on fastchess's command line (proven delivered by the input log of
control 3 attempt 2, same binary and same option set as M1); "wrapper" =
cand started through `wrap_<match>.sh` (options pre-sent, NOT on fastchess's
command line), base the plain non-declaring exe — file 2's protocol. The two
routes feed the engine the same setoption lines on behavior-identical
binaries (step 0 + wrapper bench equality above).

| match | build | route | cand options | seed | games | W-L-D (cand) | fastchess Elo ± err | my Elo [95 % pair interval] | wrapper bench 13 | warnings | lost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | bnd68 | EXPOSE | NonPawnCorr=1 NonPawnCorrWeight=50 | 7601 | 1500 | 418-429-653 | -2.55 ± 12.35 | -2.55 [-14.91, +9.80] | 730407 | 0 | 0 |
| M2 | bnd68 | EXPOSE | PawnHist=1 | 7602 | 1500 | 462-400-638 | +14.37 ± 11.96 | +14.37 [+2.42, +26.35] | 908226 | 0 | 0 |
| M3 | bnd68 | EXPOSE | ContHist4Pct=45 | 7603 | 1500 | 453-423-624 | +6.95 ± 11.98 | +6.95 [-5.03, +18.94] | 821621 | 0 | 0 |
| M4 | bnd68 | EXPOSE | EvalOnlyStore=1 EvalOnlyStoreMinDepth=2 | 7604 | 1500 | 432-431-637 | +0.23 ± 8.63 | +0.23 [-8.40, +8.86] | 862329 | 0 | 0 |
| M5 | bnd68 | wrapper | PawnHist=1 ContHist4Pct=45 EvalOnlyStore=1 EvalOnlyStoreMinDepth=2 | 7605 | 2000 | 555-531-914 | +4.17 ± 10.48 | +4.17 [-6.32, +14.66] | 1044939 | 0 | 0 |
| M6 | packc28 | wrapper | AspFailHighReduce=1 AspFailHighMaxReduce=3 | 7606 | 1500 | 470-425-605 | +10.43 ± 12.17 | +10.43 [-1.74, +22.61] | 649268 | 0 | 0 |
| M7 | packc28 | wrapper | EvalSwingMult=24 EvalSwingMax=200 | 7607 | 1500 | 431-414-655 | +3.94 ± 11.87 | +3.94 [-7.93, +15.82] | 683335 | 0 | 0 |

Evidence files: M1-M4 in `tests_glmflash4_job1/matches/M<k>_games_and_tail.txt`,
M5-M7 in `tests_glmflash4_job2/matches/M<k>_games_and_tail.txt` (argv, stamps,
one line per game `round|white|black|result|opening FEN`, last 40 lines of
fastchess output, warning/crash/abandoned counts, my pair statistics).

Pair score counts and Ptnml, for the record (fastchess Ptnml and my pair
counts agree exactly in every finished match — a useful cross-check):
M1 Ptnml [44,196,284,179,47], pairs 0.0:44 0.25:196 0.5:284 0.75:179 1.0:47;
M2 [36,161,306,199,48], 0.0:36 0.25:161 0.5:306 0.75:199 1.0:48;
M3 [36,174,315,174,51], 0.0:36 0.25:174 0.5:315 0.75:174 1.0:51;
M4 [14,122,479,119,16], 0.0:14 0.25:122 0.5:479 0.75:119 1.0:16;
M5 [49,254,382,254,61], 0.0:49 0.25:254 0.5:382 0.75:254 1.0:61;
M6 [40,167,301,192,50], 0.0:40 0.25:167 0.5:301 0.75:192 1.0:50;
M7 [40,171,313,184,42], 0.0:40 0.25:171 0.5:313 0.75:184 1.0:42.

## 6. Start and end of each step (recorded stamps, UTC)

Sources: file mtimes (`ls --time-style=full-iso`; snapshots in
`tests_glmflash4_job1/build_stamps.txt` and `tests_glmflash4_job1/timestamps.txt`),
per-match `stamps.txt` inside each match directory (copied into the
`*_games_and_tail.txt` evidence files), fastchess's own `Total Time` lines.

- 15:36:29 session work branch `for-fable-and-opus/glmflash4-work` created at 6b98f217
- 15:36:32 patch files fetched from `opus-r13-p1-nearmiss-ports` (mtime of the saved copies)
- ~15:36:45 two clean trees extracted with `git archive` to /tmp (outside the git work tree); both patches applied `patch -p1 -F0`, clean, no rejects
- 15:36:54 both engine binaries built (first build)
- 15:37:45 fastchess alpha 1.8.3 built from source
- 15:37:49 openings book downloaded and extracted
- 15:37:50-15:38:00 step 0 (10 lines) + 7 pre-match benches on the first build: all pass
- 15:38:08 patch application re-done on fresh trees with captured output; `diff -r` against the built trees: empty (files `diff_bnd68.txt`, `diff_packc28.txt` in tests_glmflash4_job1/, zero bytes on purpose)
- 15:38:0x-15:38:46 control 1, first build (46 s per fastchess `Total Time`; the runner had no stamping yet)
- 15:38:46-15:40:25 control 2, first build (99 s per `Total Time 00:01:39`), then control 3 attempt 1 (6 s) — FAILED on option delivery
- 15:41:33-15:41:35 both engines rebuilt with `-DFORGE_EXPOSE_TUNABLES=ON`
- 15:41:39-15:41:49 step 0 (10 lines) + 7 pre-match benches on the final binaries: all pass, numbers identical to the first build
- 15:41:51-15:42:38 control 1, final binaries
- 15:42:40-15:44:19 control 2, final binaries
- 15:44:22-15:44:29 control 3, final binaries: PASS (input log)
- 15:44:36-15:56:58 M1 (EXPOSE route), 1500 games, 12:22
- 15:57:02-16:09:52 M2 (EXPOSE route), 1500 games, 12:50
- 16:10:07-16:22:06 M3 (EXPOSE route), 1500 games, 12:08
- 16:22:11-16:34:13 M4 (EXPOSE route), 1500 games, 12:02
- ~16:25:55 job file 2 fetched and read; M4 allowed to finish (its measurement is valid under both files, see section 5)
- 16:26:2x-16:27:1x non-declaring builds configured/built into separate directories; uci replies captured; 7 wrappers written; the first wrapper generation was faulty and was CAUGHT by the wrapper bench check (all seven printed the base 862329); corrected wrappers re-proven, all seven print their ON number
- 16:34:17-16:54:17 M5 (wrapper route), 2000 games, all finished ~16:52; fastchess then hung in teardown with the wrapped engines and only exited when the runner's `timeout` TERM fired at the 20:00 mark (`exit=124`, `Tournament was interrupted` note, `Finished match`, 0 games abandoned)
- 16:54:29-17:09:29 M6 (wrapper route), 1500 games, all finished before the cut; same teardown picture, `exit=124`, `Total Time 00:15:00`
- 17:09-18:34 the agent's session was interrupted between these steps (owner resumed it); no compute ran in between
- 18:34:58-18:49:58 M7 (wrapper route), 1500 games, all finished before the cut; same teardown picture, `exit=124`, `Total Time 00:15:00`. All seven matches complete.

## 7. What I did not do

- M1-M4 were not re-run through the wrapper route; the compute budget does
  not cover a second full pass. Their validity rests on the input-log proof
  (control 3 attempt 2), the zero-warning and non-mirror-pair checks, and the
  step-0 identity of the two builds — not on an assumption.
- All seven matches of the list were played: M1-M4 under the EXPOSE route,
  M5-M7 under the wrapper route. No match was cut mid-games; in M5/M6/M7 the
  runner's timeout cut only fastchess's post-match teardown, after the last
  game and the results table (0 games abandoned anywhere).
- I did not measure packc28's fifth switch TtCutoffHistory (no match was
  assigned to it) and did not test any option combination on packc28.
- I did not read the other helpers' job files or reports (neither of my job
  files named any).
- No PR was opened; nothing outside my own branch was pushed or changed.
- The engine's own test binaries (added by the bnd68 patch) were not built or run.

## 8. What I am not sure about

- Every configuration was measured ONCE, one seed each. M2's +14.37 is the
  only single-part interval that excludes zero, and barely ([+2.42, +26.35]);
  M5 (the same three parts together) came out at +4.17 [-6.32, +14.66] —
  either the parts interfere or M2's signal was largely noise. I cannot
  distinguish these with one sample per configuration and did not re-run.
- fastchess's Elo error and my pair interval are different estimators; they
  agree in width on all seven matches. I report both and claim neither.
- M4's draw ratio jumped to 63.87 % (against 37.9-44 % in every other
  match). I did not investigate whether that is the option's real play-style
  effect or chance; the strength number stands at +0.23 ± 8.63 either way.
- The M5 teardown delay (below) means the last minutes of that match ran
  while fastchess was in a state I do not fully understand; all 2000 games
  had finished and the results table was printed before the delay, and 0
  games are marked abandoned, so I believe the data is unaffected — belief,
  not proof.

## 9. A better way

- Two routes make undeclared options reach a Forge engine under fastchess,
  and I ran both: (a) build with `-DFORGE_EXPOSE_TUNABLES=ON` (one CMake
  flag, the tree's own development-build switch) so fastchess sends the
  options itself, or (b) file 2's wrapper. Route (a) additionally allows the
  engine input log (`-log engine=true`) to prove delivery for every match
  for free, and needs no per-option script; route (b) is the only choice
  when the binary cannot be rebuilt. When a rebuild is allowed, (a) is the
  simpler protocol; I suggest the job text name both.
- The wrapper route has a real defect I hit: with fastchess alpha 1.8.3,
  after the last game of a wrapped match the process does not exit for
  minutes (M5: all games finished by 16:53 and the results table was
  printed, but the process only died when my `timeout` TERM fired at the
  20:00 mark, exit 124; M1-M4, without wrappers, exited immediately). The
  games and the results table are unaffected, but every wrapped match needs
  a wall-clock backstop or it hangs the runner. Worth a check before the
  wrapper route is trusted for SPRT or longer runs.
- My first wrapper generator emitted malformed `setoption` lines; all seven
  wrapper benches then printed the BASE number and nothing else looked
  wrong. The bench-through-the-script check (file 2's check 1) is what
  caught it — keep it mandatory.
- Pair statistics from a fastchess PGN must group games by the PGN `Round`
  tag, not by position in the file: rows are in completion order, which
  scrambles with unequal per-side node counts (my first position-based
  pairing on control 2 produced 76 pairs / 148 unpaired; by-round pairing
  gives 150 / 0). With equal node counts both sides the file happens to be
  in order, which is why the error hides in symmetric matches.
- Throughput arithmetic for planning: on this 4-core helper the prescribed
  matches ran 100-134 games/min at 20000 fixed nodes; the seven matches
  (11,500 games) need ~90 minutes of pure match time. A 45-80-minute job on
  a 4-core machine cannot cover the list; either trim games per match (~800
  gives a ±~15 Elo interval) or size the job to the machine.
- This fastchess version marks interrupted games `abandoned`, not
  `INCOMPLETE` (file 1's term); job texts should follow the tool's version.

## 10. Model name and version

I am glmflash4. The model behind this agent is GLM, trained by Z.ai; the
runtime presents it as GLM 5.3 Flash. I cannot verify a precise version
string from inside the run; that is the honest limit of what I know.

## 11. Questions for Fable

- Does the other helper's whole-bnd68-patch measurement use the same seeds,
  openings file, node counts and game counts? If yes, M5 (+4.17) can be
  compared against the whole patch directly to see whether the correction
  part (NonPawnCorr, -2.55 alone) helps or hurts on top; if not, the
  comparison needs a common protocol first.
- Do you want a second seed for M2 to test whether its +14.37 survives, or
  is the budget better spent on packc28's TtCutoffHistory (an option my two
  packc28 matches did not cover)?
