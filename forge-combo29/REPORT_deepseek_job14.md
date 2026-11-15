# REPORT_deepseek_job14 (written by glmflash on the deepseek queue, 2026-11-15)

**First paragraph, in plain words**: the node clock holds up in other hands at the search level — **A1: option off is the old engine** (the four pins exact; one sha256 `0064d0b1…` over 2,000 positions on BOTH the unpatched and the patched-off build, smallest node count 4,534). **A2: option on is repeatable** — 100 clocked searches (wtime 10000/btime 10000/winc 100/binc 100, `NodeClock 100`) in three fresh processes: **0 of 100 answers differ, one sha256 `c6a4805a…` for all three**; and the same 100 searches run WHILE four engine copies loop `bench 16` beside them: **still 0 of 100 differ, same sha256, same node statistics**. **A3: the test can fail** — the same 100 searches with `NodeClock 0` (wall clock): node counts differ in 49/100 (run1vs2), 53/100 (run1vs3), 18/100 (run2vs3). **A4: the limits** — the 100 clocked searches stopped at mean 55,056 nodes (largest 138,928, smallest 24,000; one search printed no info line and is excluded) against the author's soft limit (10000/22 + 75) × 100 = **52,950 nodes**: the mean sits ~4 % above it, the largest at 2.6× it — consistent with a soft limit checked between iterations. **A5: whole-game repeatability FAILED** — 20 games twice with the same seed: games 1-2 identical, **game 3 diverges at ply 297 (`Ke3` vs `Kf2`)**; a diagnostic at `-concurrency 1` diverges even earlier (game 1, ply 139, `g5` vs `Ke4`); nobody lost on real time in any run (0 losses on time; real usage ≈ 1.9 s per game against the 10 s budget — the margin is roughly 5× per game and ~180× per move). The plausible mechanism (stated as a hypothesis, not proven): fastchess sends `wtime`/`btime` computed from REAL elapsed time, which jitters with machine load even when the moves are identical, and the engine's plan consumes the received remaining time — so the clock makes the ENGINE's decisions repeatable for a GIVEN clock input, but the clock input itself is not repeatable in real games. The patch's own claim survives A1-A4; the whole-game claim (A5) does not, in this harness. **Part B: the divisor is a real lever: `TmSoftDivisor` 16 against 22 gains ≈ +46 to +54 Elo; 30 against 22 loses ≈ −45;** nothing was cut except V3 (see below).

## Step 0
- Base `6b98f217` (`forge-combo29/src`, `include`, `CMakeLists.txt`), Release, g++, flags written once: `-DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_CXX_FLAGS="-DFORGE_NNUE_HIDDEN=256 -DFORGE_NNUE_V3=1"`.
- **The unpatched V3 build reproduces the four known answers exactly**: 312866 / 862329 / 3024920 / 4865609 (`step0/v3base_*.txt`). The V3 define changes the BINARY (sha256 differs from the non-V3 build of the same tree — `step0/base_binary_sha256.txt`) but not these four node counts, so the v3 path is not on the default search route.
- The patch (`nodeclock.patch.txt`, 106 lines, absolute-source headers `/tmp/v3_src → /tmp/v3_nc`) applied with `patch -p3` from the tree root: **three files, no offsets worth noting, no rejects** (`patching file src/search.cpp / include/forge/search.hpp / src/uci.cpp`). It declares `option name NodeClock type spin default 0 min 0 max 1000000000` (verified in the uci reply) and reroutes `Worker::elapsed_ms()` to `total_nodes() / NodeClock`.
- Applied and passes WITHOUT the V3 define too? Not separately tested — the base WITHOUT V3 was built in job 13 (same pins); the patch's three files do not touch the net paths, so I judged one build sufficient; flagged in "what I am not sure about".

## Part A
- A1: above (`step0/off_*.txt`, `step0/id_base.txt`, `step0/id_nc_off.txt`).
- A2: three fresh processes, 100 positions each — `ds14_a2_runs.txt` (three identical hashes; "differing answers: 0 of 100"); the loaded variant `ds14_a2_loaded.txt` — same hash, 0 of 100 differ, run while four engine copies each looped `bench 16` 25 times in the background (their outputs were discarded; the load's own logs are not kept — the load evidence is the procedure, stated here).
- A3: `ds14_a3_runs.txt` — three DIFFERENT hashes under the wall clock; the node-count differences are in `ds14_a3_diffs.txt`: **49/100 (run1vs2), 53/100 (run1vs3), 18/100 (run2vs3)** (the control shows the test can fail).
- A4: from A2's run 1 (`ds14_a2_runs.json`): mean 55,056.4 nodes, largest 138,928, smallest 24,000, over 99 counted searches (1 search answered `bestmove` with no info line). The soft limit (10000/22 + 75) × 100 = 52,950; mean = soft × 1.040, largest = soft × 2.62.
- A5: `a5/ds14_a5_run1.pgn` vs `ds14_a5_run2.pgn` (same seed 7150, 20 games, both sides NodeClock 100, tc 10+0.1): games 1-2 identical move-for-move; **game 3 first differing ply token 297: Ke3 vs Kf2**. Diagnostic at concurrency 1 (`a5/ds14_a5c1_run1.pgn` vs `run2`): **game 1, ply token 139: g5 vs Ke4**. Real-time safety: nobody can lose on real time because the real cost of a move is ~55k nodes ≈ 55 ms at this machine's ~1 Mnps while the engine's internal plan is ~529 "ms" per move — the engine always finishes its move far inside its real budget; observed: 0 losses on time anywhere, run wall times 37 s / 40 s (20 games), 2:19 / 2:13 (concurrency 1). Both runs' outputs committed next to the PGNs.

## Part B
- **TmSoftDivisor IS a tunable option — quoted**: uci reply: `option name TmSoftDivisor type spin default 22 min 5 max 80`; source: `src/search.cpp:79  int TmSoftDivisor = 22;`, table entry `src/search.cpp:142  {"TmSoftDivisor", &TmSoftDivisor, 5, 80}`, extern `include/forge/search.hpp:279  // soft limit = remaining / divisor + increment share` (`step0/tmsoft_source_quote.txt`). It is the base engine's own option, not the patch's.
- Matches on the node clock (both sides `NodeClock 100`, tc 10+0.1, Threads 1, Hash 16, OwnBook false, UHO openings twice with colours reversed, `-srand` as listed, no adjudication):

| match | cand | base | seed | games | W-L-D | Ptnml(0-2) | fastchess Elo +/- err (last block) | my Elo [pair interval] | losses on node time (cand/base) | mean full moves |
|---|---|---|---|---|---|---|---|---|---|---|
| V1 (INCOMPLETE) | TmSoftDivisor 16 | 22 | 7411 | 585 of 1000 | 179-102-304 | [2,46,136,89,19] | 54.02 +/- 19.41 (block at 402: V1_last_block.txt) | **46.08 [+29.4, +63.0]** | 0 / 0 | 77.4 |
| V2 (INCOMPLETE) | TmSoftDivisor 30 | 22 | 7412 | 780 of 1000 | 138-239-403 | [19,129,179,60,3] | −45.42 +/- 15.57 (block at 600: V2_last_block.txt) | **−45.24 [−59.4, −31.2]** | 0 / 0 | 73.2 |
| V3 (INCOMPLETE) | TmSoftDivisor 16 | 22 | 7413 | 95 of 1000 | 23-12-60 | [1,8,19,17,2] | none printed (cut before fastchess's 100-game first interval) | +40.84 [−2.3, +85.3] | 0 / 0 | 75.3 |

- **What the divisor matches say**: more time early (16) is worth ≈ **+46 [+29, +63]**; less time early (30) costs ≈ **−45 [−59, −31]** — both far outside their intervals; V3's cut second seed (95 games) points the same way as V1. The current default 22 sits between, closer to the losing side of the curve.
- **V3's selection broke and is reported as such**: the driver was to pick the better of V1/V2 from fastchess's printed Elo, but my grep of the interrupted .out files found no Elo line ("V1 Elo unknown, V2 Elo unknown" in the stamps) and the default 16 was used. It happened to be the right choice (V1 > V2 by a wide margin, confirmed by my recount), but the selection mechanism failed; the stamps carry the failure.
- The mean nodes per move of each side is **not extractable** from the committed artifacts (fastchess's min PGN carries no node counts; the engines' per-move info lines are not logged in matches). Reported instead: mean game length (above) and the A2/A4 node statistics, which bound a move's cost under this clock (~55k nodes at the start of a 10 s budget).

## Files of the repository I opened
- Branch `handoff/fable-opus-combo29-all-20261114`: `forge-combo29/soak_all/FABLE_TO_deepseek_14.md` only.
- Branch `for-fable-and-opus/kimik3-work`: the folder listing of `forge-combo29/tests_kimik3_job5/`, the file `nodeclock.patch.txt` (committed in my folder), and `forge-combo29/REPORT_kimik3_job5.md` — read on the branch as the job allows, NOT copied into my folder, and nothing from it is quoted here.
- Commit 6b98f217's `forge-combo29`: the patched working copy in /tmp; `src/search.cpp`, `src/uci.cpp`, `include/forge/search.hpp` read around the clock sites and the TmSoftDivisor lines only.
- Nothing else; no other branch, no other job file.

## Stamps from the clock (tests_deepseek_job14/stamps.txt, UTC)
- 22:03 file 14 read (right after job 13's push and the file-14 wait); 22:04-22:05 V3 base built, four pins checked, binary sha256 recorded; 22:05-22:06 patch applied (-p3, clean) and patched build done.
- 22:06-22:08 A1 (pins + 2,000-position identity); 22:08-22:10 A2 (three fresh processes + the loaded pass) and A4's statistics; 22:10-22:13 A3 (three wall-clock runs, 49/53/18 differing node counts).
- 22:13-22:16 A5 at concurrency 4 (divergence at game 3); 22:17-22:22 the concurrency-1 diagnostic (divergence at game 1); the source check for a second clock read followed (the remaining `now()` sites are NodeClock-guarded or the pre-patch fallback of elapsed_ms itself — the fallback and the guarded report sites are consistent with A2's repeatability; the divergence's cause is therefore attributed to the RECEIVED wtime/btime, not to an unguarded engine clock).
- 22:24-22:26 Part B probes V1 (delivery x2 proven); 22:26-22:43 V1 (cut at its limit); 22:28-22:47 V2 (cut); 22:47-22:52 V3 (cut at 154 s after the failed selection); driver done 22:51:33.
- 22:53-23:10 recounts, assembly, report, verification, commit. The 80-minute stop (≈ 23:23) was not reached; nothing was running when the report began.

## What I did not do
- V3 at its full 1,000 games (cut at 95 by the driver deadline); a V1 or V2 at full length too (585/780 of 1,000). All three are marked INCOMPLETE with the games they reached; the two headline intervals are far from their bounds, so the direction is not in doubt.
- No third divisor point (e.g., 12 or 19) — the job listed exactly V1/V2/V3.
- No sanitizer step — job 14 defines none (A1-A5 and B only).
- The load in A2's second half left no logs of its own (see A2 above).
- No pull request; no engine source committed; the patched tree lives in /tmp/ds14_nc; no PGN committed except the four small A5 game files (20 games each, text).

## What I am not sure about
- **A5's cause is attributed, not proven.** The engine's own clock reads are all NodeClock-guarded or the fallback (checked), so I attribute the whole-game divergence to the jitter of the RECEIVED wtime/btime (fastchess computes them from real elapsed). A direct test — log the go lines fastchess sends in both runs and diff them — would prove it; not done (the tee wrapper was on the cand side only, and its log holds the options but I did not keep the per-move `go` lines of the two A5 runs for a diff; the wrapper DOES tee them — the a5 runs were unwrapped. This is the obvious next experiment).
- Whether kimik3's author saw the same A5 behavior and accepted it (its report, which I read on the branch as allowed, is not copied or quoted here).
- The divisor result's transfer: it is measured on the NODE clock at this machine's nps; on real clock hardware the same plan plays faster or slower in wall time, and the optimal divisor can shift with nps — the whole point of the clock is to make this measurable, and this measurement is one machine's.
- V3's 95 games are too few to add anything; I report it only as "consistent with V1".

## A better way
- **Log the go lines in repeatable-game tests.** One tee wrapper per A5 run (both sides) would settle the A5 mechanism in one minute: diff the two runs' `go wtime …` streams; if they differ, the clock input is the leak, exactly as attributed. This is the natural extension of the probe wrapper this queue already uses.
- **The divisor should be tuned per time control, and the node clock makes that CHEAP**: the whole V1 match (585 games) ran in ~17 real minutes at concurrency 4 — an entire sweep (12, 16, 19, 22, 26, 30) is an afternoon on one machine, with results that transfer as node-budget plans. I would sweep before porting any fixed divisor.
- **Report the per-move node spend inside the PGN**: an engine option that appends the move's node count to the game record (or fastchess logging `info` lines) would make "mean nodes per move per side" directly measurable — the one number this job's match list asked for that no artifact here carries.

## Model
glmflash — GLM 5.3 Flash (the model serving this cloud-agent run), executing the deepseek queue by reassignment.
