# glmflash2 job 4 report (2026-11-15)

## 1. Result in plain words (first seeds, 7241-7243)

**Pooled over both seeds, no candidate shows a gain or a loss outside its 95% pair interval:**
TtProbcut 360 **-0.59 +/- 8.56** (2,968 games; its first-seed +6.3 did not replicate - the second
seed came out -7.5), PruneLmrHist 1 **+3.58 +/- 8.69** (2,916 games; the same small positive lean at
both seeds, +3.33 and +3.83), QsMovePrune 3 **-6.26 +/- 9.38** (2,498 games; the same negative lean
at both seeds, -9.05 and -2.58). **Cut or not reached, said here in the first paragraph as asked:**
every first-seed match was cut at its 700 s cap (1,420-1,491 of 2,000 games); M4 and M5 were cut at
their caps (1,477 and 1,453); M6 was cut at the absolute 19:05:00Z deadline (1,078 games). Nothing
else was skipped; all seven runs have fastchess's own summary block.

## 2. Step 0 (expected against printed)

Recipe (same for all three, written once): clean export of d4f43124 (source at the tree ROOT),
`patch -p1 --fuzz=0` (all three applied with zero fuzz, logs kept), CMake Release, g++ 13.3.0,
`-DFORGE_EXPOSE_TUNABLES=ON` (the tree exposes tunables as UCI options only with it), and
`-DCMAKE_CXX_FLAGS="-DFORGE_NNUE_HIDDEN=256"` (the tree has no CMake variable of that name; as a
plain compiler define the static asserts accept it). No -march flag: this tree's default is generic
(the lock tree's FORGE_MARCH does not exist here). Two false starts are recorded in section 8.

| build | side | bench 11 | bench 13 | bench 16 | perft 5 | uci lists option |
|-------|------|----------|----------|----------|---------|------------------|
| c1_prunelmrhist | OFF | 312866 | 862329 | - | 4865609 | yes (spin 0..1, default 0) |
| c1_prunelmrhist | ON (PruneLmrHist=1) | 294465 | 815919 | 2071386 | - | - |
| c2_qsmoveprune | OFF | 312866 | 862329 | - | 4865609 | yes (spin 0..16, default 0) |
| c2_qsmoveprune | ON (QsMovePrune=3) | 363674 | 815943 | 3220620 | - | - |
| c3_ttprobcut | OFF | 312866 | 862329 | - | 4865609 | yes (spin 0..1000, default 0) |
| c3_ttprobcut | ON (TtProbcut=360) | 322040 | 845712 | 2757689 | - | - |

Every OFF number equals the known 312866 / 862329 / 4865609, and every ON number equals the branch's
recorded row, to the node. Files: step0/bench*_*.txt, perft5_*_off.txt, uci_*.txt.

## 3. The probes (before every match) and the openings check

Each probe = the match's exact command, 2 games, engine input log on. Evidence per match committed:
matches/<name>_probe_setoption_lines.txt (the cand-side setoption the engine received) and
matches/<name>_probe_openings.txt (the probe's two FENs = the match's first pair; same seed).

| match | cand-side setoption received | probe first FEN == match round-1 FEN |
|-------|------------------------------|--------------------------------------|
| control_7240 | (none expected: control has no candidate option; the filtered file is empty by construction) | yes |
| M1 | `setoption name PruneLmrHist value 1` (x2, one per game) | yes |
| M2 | `setoption name QsMovePrune value 3` (x2) | yes |
| M3 | `setoption name TtProbcut value 360` (x2) | yes |
| M4-M6 | same pattern (files committed) | yes |

Openings across matches differ, as they must with order=random and different seeds: the four first
pairs are four different FENs (control rnbq1rk1/... , M1 r1bqk2r/... , M2 rnbqkb1r/... ,
M3 r1bq1rk1/...) - the "second seed replays the first match" fault did not happen here.

## 4. All matches (patched exe both sides; option ON vs OFF; 20000 nodes, 1 thread, 16 MB)

Machine: 4 cores, concurrency 4. fastchess v1.8.3-alpha, UHO book, no adjudication. Crashes and
illegal moves: 0 in every match (grep over each full output). fc Elo = fastchess's own final or
last-interim block; my Elo = logistic from mean pair score, 95% pair interval (pgn_stats.py,
validated in jobs 1-3).

| #  | match | seed | games | W-L-D | Ptnml(0-2) | fc Elo +/- err | my Elo +/- 95% | crashes |
|----|-------|------|-------|-------|------------|----------------|----------------|---------|
| C  | base 20k vs base 10k (c1 build, option off) | 7240 | 300 | 186-30-84 | [0,7,36,51,56] | +200.24 +/- 34.25 | +200.24 +/- 36.13 | 0 |
| M1 | PruneLmrHist 1 vs off | 7241 | 1463/2000 | 414-400-649 | [43,167,293,189,39] | +4.22 +/- 12.47 (last interim, 1400g) | +3.33 +/- 12.20 | 0 |
| M2 | QsMovePrune 3 vs off | 7242 | 1420/2000 | 384-421-615 | [40,196,278,153,43] | -9.45 +/- 12.58 (last interim, 1400g) | -9.05 +/- 12.53 | 0 |
| M3 | TtProbcut 360 vs off | 7243 | 1491/2000 | 426-399-666 | [41,167,301,196,40] | +4.71 +/- 12.34 (last interim, 1400g) | +6.30 +/- 11.99 | 0 |
| M4 | second seed, largest first: TtProbcut | 7253 | 1477/2000 | 398-431-648 | [48,186,291,176,37] | -7.93 +/- 12.57 (last interim, 1400g) | -7.53 +/- 12.24 | 0 |
| M5 | second: PruneLmrHist | 7251 | 1453/2000 | 433-418-602 | [44,168,283,190,41] | +5.71 +/- 12.64 (last interim, 1400g) | +3.83 +/- 12.41 | 0 |
| M6 | third: QsMovePrune | 7252 | 1078/2000 | 311-319-448 | [28,143,205,135,28] | -0.69 +/- 14.58 (last interim, 1000g) | -2.58 +/- 14.18 | 0 |

Pooled over both seeds (pair counts added, interval on the pooled pairs):
- **TtProbcut 360: 2,968 games, -0.59 +/- 8.56** - the +6.3 of the first seed did not replicate; nothing shown.
- **PruneLmrHist 1: 2,916 games, +3.58 +/- 8.69** - the same small positive lean at both seeds (+3.33, +3.83); nothing shown.
- **QsMovePrune 3: 2,498 games, -6.26 +/- 9.38** - the same negative lean at both seeds (-9.05, -2.58); nothing shown.

## 5. My one-sentence reading of each patch

- **c1_prunelmrhist**: in the shallow-depth pruning block the quiet-move futility/history/SEE tests
  use an lmr_depth adjusted by the same clamp(history / LmrHistoryDivisor, -2, 2) term LMR itself
  uses, so a quiet with good history is pruned as a deeper move and a bad-history one as a shallower
  one - exactly what its line says.
- **c2_qsmoveprune**: in quiescence (not in check), once more than N moves have been CONSIDERED at a
  node, a capture that gives no check, is not a promotion and is not a recapture on the previous
  move's to-square is skipped - what its line says, with one nuance: `++move_count` runs before the
  futility test, so the "first three moves" include captures that were then futility-pruned without
  being searched; the option gates by considered captures, not by searched ones.
- **c3_ttprobcut**: at non-PV non-root nodes a TT lower bound at depth >= this depth - 3 whose score
  beats beta by 360 (both non-mate, halfmove clock < 90) cuts the node returning beta + 360 without
  a re-search - what its line says; note it returns beta + margin, not the stored score.

## 6. Files of the repository I opened

- The job file (git show on the handoff branch).
- The three patch files (read in full; quoted in section 5).
- The root CMakeLists.txt of the d4f43124 export (options list, grep only).
- src/uci.cpp of the c1 export (two lines: how tunables become options).
No other repository file was opened.

## 7. Start and end of each step (recorded stamps, UTC)

- 17:50:08Z  job 4 file found; read 17:50:2xZ.
- 17:50:4xZ  branch opus-r15-20261103 fetched (--depth 1; base d4f43124 already local); patches
  extracted (36/35/36 lines); three clean exports made.
- 17:51:0xZ  patches read; first build attempt: FAILED (built the UNPATCHED tree first by mistake,
  and the tree rejected -DFORGE_NNUE_HIDDEN=256 as a CMake variable - static assert "NNUE shape
  mismatch"); recipe corrected to CMAKE_CXX_FLAGS + FORGE_EXPOSE_TUNABLES=ON.
- 17:51:2xZ  c2, c3 built; c1 rebuilt after patching (all three PATCH_OK, zero fuzz).
- 17:51:22Z  Step 0 complete (files stamped): all six known numbers match to the node.
- 17:51:45Z  first runner4a launch: matches died at once ("Error; no TimeControl specified!") - my
  run_one had dropped the per-engine nodes arguments from the fastchess line. Fixed; also cleared
  the polluted timeline.txt.
- 17:53:43Z -> 17:55:33Z  probe C + control 7240 (300 games, +200.24).
- 17:55:37Z -> 18:07:26Z  probe M1 + M1 (cut at cap, 1463 games).
- 18:07:26Z -> 18:19:16Z  probe M2 + M2 (cut at cap, 1420 games).
- 18:19:16Z -> 18:31:01Z  probe M3 + M3 (cut at cap, 1491 games).
- 18:31:36Z  runner4b launched (second seeds, ranked TtProbcut > PruneLmrHist > QsMovePrune);
  M4 cap 700 s, M5 cap 700 s, M6 absolute deadline 19:05:00Z.
- 18:43:29Z -> 18:55:20Z  probe M4 + M4 (cut at cap, 1477 games); then probe M5 + M5 (cut at cap,
  1453 games, ended 18:55:20Z).
- 18:55:20Z -> 19:05:0xZ  probe M6 + M6 (cut at the absolute deadline, 1078 games); RUNNER4B_DONE.
- Report drafted from 18:33Z; pooled numbers computed 19:05:2xZ; committed and pushed 19:06-19:07Z.

## 8. What I did NOT do

- No first-seed match reached its full 2,000 games (all cut at the 700 s cap; the job set the cap
  rule, the counts are in the table). M6 runs to the absolute deadline 19:05:00Z and is the one cut
  by design; M4/M5 were cut by their own caps.
- No SPRT, no other node counts, no Elo-vs-nodes curve, no combination matches (each candidate
  alone against OFF, as the job asked).
- The patch files, build logs and probe logs are committed as text; PGNs stay outside the repo.

## 9. What I am NOT sure about

- All point estimates sit inside their intervals; with ~1,450-1,500 games per match the 95% pair
  interval is about +/- 12, so a true +/- 8 Elo effect could hide in any of the three. The second
  seeds exist to shrink that; their pooled rows are the answer I stand behind, the single rows are
  not.
- QsMovePrune's negative lean (-9) could be real (it cuts real captures in quiescence) or noise;
  I did not look for a tactical regression test, that was not in the job.
- The bench-16 ON numbers for c2/c3 (3220620 / 2757689) match the branch's records exactly, which
  also pins that my recipe builds the same search the branch measured.
- My control used the c1 build; the job allowed "any of the three builds with the option off".

## 10. A better way

- The two false starts cost ~4 minutes of a 90-minute budget and both were MY errors (built the
  unpatched tree; dropped per-engine nodes in a refactor). A 20-second smoke test of each new runner
  (one 2-game probe first, read its output) before trusting it would have caught the second one
  before the whole roster ran through it. My runner now effectively does this via the probes, but
  the probe cannot catch a missing nodes= (the match-level control can): put the control match
  FIRST, always - it was first, and it caught it.
- The probe-then-match pattern doubles as the setoption evidence AND as the openings-differ check in
  one 8-second run; cheap enough to keep for every future match job.

## 11. Model name and version

I am glmflash2, running on GLM, model glm-5p3-flash (GLM 5.3 Flash) as far as I know it.
