# Forge Opus round 5A: gate-ready singles (CorrMargins, CorrExt, CorrHistPlus variants, NetScale) — IN PROGRESS

**Status:** M1, M2 done; M3 smoke running (corrmargins1 near done); M4 written (refreshed per smoke result); M5 code written, verify at the smoke pause. Last push 02:23 Vienna.

Branch `opus-r5a-singles` = `origin/forge-bundle-int` b7c17722 + the commits listed per milestone. Job started 01:52 Vienna
(2026-10-29), hard stop 04:52 Vienna. No Elo claims: node counts are not strength; gates decide. Machine exclusive: no
(gates, NNUE training and self-play kept running; all my work at BelowNormal, at most 3 threads in total).

Time base: the PC clock reads PST but runs 9 h ahead of GitHub's server clock (`gh api -i rate_limit` Date header);
Vienna (CET, UTC+1) = PC "PST" time - 1 h. Every time below is Vienna.

## 00_baseline (01:52-02:00 Vienna)

Build (PC lock recipe flags from the job spec; script `tools/build_r5a.sh`, 3 parallel compiles at BelowNormal):
```
bash opus_r5/r5a/tools/build_r5a.sh "$PWD" /f/opus_scratch/r5/r5a/exe/forge_r5a_base_b7c1772.exe
# g++ 15.2 ucrt64: -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math
#                  -march=x86-64-v3 -mtune=znver5 -pthread -static
```
Exe `F:\opus_scratch\r5\r5a\exe\forge_r5a_base_b7c1772.exe`, sha256 `82d414ba9a3f670287090f11ada392e46f415df9e1da46b362324c90314b6768`
(also in `EXES.txt` here and next to the exe), 0 compiler warnings, FMA count 0.

Identity (lock `uci_check.py --full`: Threads 1, Hash 16, OwnBook false), log `logs/identity_base_b7c1772.log`:

| check | got | pin | result |
|---|---|---|---|
| bench d11 | 312866 | 312866 | OK |
| bench d13 | 862329 | 862329 | OK |
| bench d16 | 3024920 | 3024920 | OK |
| bench d20 | 12389307 | 12389307 | OK |
| bench d22 | 34048354 | 34048354 | OK |
| perft 5 startpos | 4865609 | 4865609 | OK |
| perft 5 kiwipete | 193690690 | 193690690 | OK |
| FMA instructions | 0 | 0 | OK |

PC safety note (temperature rule): `tools/cpu_temp.sh` reads the live HWiNFO64 sensor log (read-only). The rule's
"CPU hot spot" is taken as HWiNFO's **CPU IOD Hotspot** sensor (~49-50 C). HWiNFO's Tctl/Tdie (control temperature)
already read 79.8-81.1 C at 121 W package power from the PC's own load (gates + training) in the ten minutes before
my first command (01:43-01:52 Vienna), i.e. the CPU regulates at about 80 C by itself; my 3-thread build added at
most +0.5 C. If the owner meant Tctl/Tdie, every step of this job ran with Tctl at about 80 C (logged per milestone).

## M1 per-option audit + ON benches (01:58-02:01 Vienna) — DONE

No engine change. Tool `tools/m1_option_bench.py` (one fresh process per config, Threads 1 / Hash 16 / OwnBook false):
setoption ON -> record every line printed before `readyok` -> bench d11/d13/d16 -> `go depth 10` on 4 positions
(after `ucinewgame` each) -> setoption back to the default -> the same benches and searches again, which must equal
the OFF pins and a fresh all-default process. Log `logs/m1_bench_base.log`, data `logs/m1_bench_base.json`
(exe `forge_r5a_base_b7c1772.exe` 82d414ba..., 53 s at BelowNormal, one thread).

How each option reaches the search (read on b7c17722):

| option | storage | read where | protection |
|---|---|---|---|
| CorrMargins 0..1 | global `options::corr_margins` (uint8) | once per aspiration pass at the root of every worker (`iterative.inc:178`) to pick the CorrMargins instance `search_corr_margins` (alphabeta.inc compiled with FORGE_SEARCH_CORR_MARGINS=1; hooks at RFP :165, null move :179, futility :344, LMR :491); weights `CorrRfpPct 50, CorrFutilityPct 100, CorrNullMovePct 50, CorrLmrPct 25` (unlisted tunables) | stop-before-setoption |
| CorrExt 0..1 | global `options::corr_ext` (uint8) | same switch (`iterative.inc:178`), instance `search_corr_ext` (singular extension :427, path budget :454); weights `CorrExtDoublePct 12, CorrExtTripleCorr 48, CorrExtTripleMargin 100, CorrExtBudget 7` | stop-before-setoption |
| CorrHistPlus 0..7 | global `options::corr_hist_plus` (uint8) | every static eval and correction update (`evaluation.inc:158/175` -> `correction_plus.inc`), and once per search in `fb2::effective` (`searcher.inc:51`, drops CorrHistV2 when nonzero) | stop-before-setoption + UCI exclusivity with CorrHistV2 (both orders refused) |
| NetScale 50..150 | global `net_scale::percent` | every NNUE static eval (`evaluation.inc:123`); a changed value clears the hash (TT holds static evals) | stop-before-setoption |
| HistRework 0..3 | global `search_options::hist_rework` | per node (alphabeta.inc :290/:552, history.inc, evaluation.inc, qsearch.inc) | stop-before-setoption |

None of the five is in the per-search `fb2_` snapshot (that holds only CorrHistV2 / LmrTableV2 / TtPruneV2). They are
safe by the stop-before-setoption rule: `setoption`, `position`, `ucinewgame` and `go` all call `stop_search()`
first (sets the stop flag, `searcher.stop()`, joins the search thread); `Searcher::search` joins every helper before it
returns, and `bench` runs synchronously on the UCI thread after `stop_search()`. So no search thread reads a value
while the UCI thread writes it. Echo: all five are silent on a valid setoption (no `info string`); M2 adds the
per-`go` echo.

ON benches (d11 / d13 / d16) and the same-process restore:

| config | d11 | d13 | d16 | `go depth 10` x4 (startpos, kiwipete, endgame, QGD) | set back to default: bench + go |
|---|---|---|---|---|---|
| OFF (pins) | 312866 | 862329 | 3024920 | 13102 / 33339 / 12301 / 21762 | — |
| CorrMargins=1 | 343365 | 858019 | 2522546 | 12915 / 34832 / 12286 / 23787 | RESTORED |
| CorrExt=1 | 312961 | 838790 | 2891507 | 13102 / 33339 / 12301 / 21762 (= OFF at depth 10) | RESTORED |
| CorrHistPlus=2 | 296553 | 824640 | 2914749 | 21533 / 32305 / 14257 / 21130 | RESTORED |
| CorrHistPlus=4 | 340927 | 734347 | 2794671 | 18245 / 34693 / 12421 / 22136 | RESTORED |
| CorrHistPlus=6 | 357478 | 747883 | 2544596 | 15825 / 34689 / 8727 / 16382 | RESTORED |
| NetScale=97 | 319148 | 829133 | 2700789 | 19059 / 32300 / 9215 / 20392 | RESTORED |
| NetScale=99 | 308948 | 917342 | 2601047 | 11913 / 42889 / 11399 / 19206 | RESTORED |
| NetScale=101 | 347380 | 900398 | 3454424 | 13103 / 33369 / 10639 / 21147 | RESTORED |
| NetScale=103 | 317530 | 848894 | 2953687 | 12217 / 51977 / 12869 / 33734 | RESTORED |
| HistRework=1 | 373261 | 1043893 | 3399770 | 10174 / 38159 / 13578 / 21656 | RESTORED |
| HistRework=3 | 336192 | 869621 | 3052885 | 12434 / 51016 / 12817 / 16282 | RESTORED |

Cross-checks: CorrMargins=1, CorrExt=1, CorrHistPlus=2/4, NetScale 99 (d11) and HistRework=1/3 equal the pins recorded in
`opus_r3/R3-1/OPTIONS.md` for the R3 stack, so the bundle-int port did not move these instances. CorrHistPlus=6 and
NetScale 97/101/103 had no earlier pins (new here). CorrExt equals OFF at `go depth 10` on these four positions: its
singular-extension hooks need depth >= SingularDepth with a TT move and a correction, so it acts only deeper (bench
d11+ differs). Node counts are not strength.

NetScale value for M4: **99**. S41 (`opus_round1/sol_S41/EVALSCALE_20261027.md`) measured the lock net s198 +1.2% wider
than h256_e12, the scale the search margins were tuned on; 99 maps it back (R3-3 proposal R3-11). 97/101/103 have no
such measurement behind them (101/103 widen an already wide net).

## M2 effective-settings echo + conflict guards (02:02-02:15 Vienna) — DONE

What changed (engine, all OFF-identical):
- `include/forge/r5a_options.hpp` + `src/search/r5a_options.inc` (included last in `src/search.cpp`, so no new
  .cpp: the 8-file PC/QA build recipe is unchanged): `forge::r5a::active_search_options()` lists every search option
  that is not at its default as `Name=value` in UCI spelling and `uci` listing order (forge::options, HistRework,
  NetScale, CorrHistV2/LmrTableV2/TtPruneV2, UseNNUE), then every tunable that differs from its compiled-in value
  (`tune_defaults()`, captured during static initialisation, before main). "" at the defaults.
  `combination_warning(bundle)`: the CorrMargins + TtPruneV2 warning text, "" otherwise.
- `src/uci.cpp`: every `go` (not `go perft`) prints one `info string active: <list>` line when the list is not
  empty, before the search starts (the UCI layer appends NNUEFile, SyzygyPath and, in switch builds, NnueInt16 /
  NnueLazyAcc / TtChildPrefetch). At the defaults nothing is printed, so OFF logs stay byte-identical.
  The warning `info string warning: CorrMargins=1 with TtPruneV2=true (BundlePreset Bx): both move the
  reverse-futility and futility margins of the CorrMargins search instance; never gated together (allowed, not
  refused)` is printed when a setoption of CorrMargins, TtPruneV2 or BundlePreset leaves both on (preset name
  only while TtPruneV2 comes from the preset). The BundlePreset branch now releases the output lock before the
  warning (std::mutex is not recursive); its own line is unchanged. Unknown-option handling is untouched.
- CorrHistPlus vs CorrHistV2: the existing guard already refuses every nonzero CorrHistPlus (so bits 2 and 4) while
  CorrHistV2 is on, and CorrHistV2 while CorrHistPlus is nonzero; no code change, now covered by tests for 1/2/4/6 in
  both orders (value unchanged, visible in the echo).
- `tests/r5a_options_tests.cpp` (CMake target `forge_r5a_options_tests`, test `forge_r5a_options_tests <forge>`):
  30 library checks (part A) + 14 UCI transcript checks (part B). Transcripts are left in the test's working dir.

Evidence:
- M2 exe `forge_r5a_m2_0a01ec53.exe` sha256 `fda298e6df180a067c323d0bf68434e365cd2eef55617e671c57b4dea700738a`
  (`build_r5a.sh`, 0 warnings, FMA 0): `uci_check --full` **ALL OK** (`logs/identity_m2_0a01ec53.log`); the M1 table
  re-run on it is identical row for row (`logs/m1_bench_m2_0a01ec53.log`), so the echo changes no search.
- CMake (cmake_build.sh flags, Release, JOBS=3): all 126 targets build; 62 compiler warnings, all in files this job
  did not touch (alphabeta.inc 48, qsearch.inc 12, tt_lockless.inc 2, -Wconversion); none in r5a files or uci.cpp.
- `forge_r5a_options_tests`: **ALL OK** (44/44).
- CTest (`tools/run_ctest_3cpu.cmd`: BelowNormal, affinity 0x700 = 3 logical CPUs, children inherit both): **55/55 passed**,
  every registered test except `forge_tests` (two of its checks search with 4 threads, above the job's 3-thread cap; CI runs it
  with the known-failure check). The SmpExactNodes flake did not occur on 3 CPUs. Log `logs/ctest_m2_dbab5a41.log`.
- GitHub CI: the M2 push is the first normal (non-[skip ci]) commit of the branch; opus-ci run 40799232252
  (e22d3649): linux release success, linux asan success, linux tsan see the final CI line below.

## M3 smoke stability per option (from 02:15 Vienna) — IN PROGRESS

Runner `smoke.py` (my own; python-chess only for move legality), driver `tools/smoke_all.sh`, table
`tools/smoke_table.py` -> `smoke/SMOKE_RESULTS.md`. Exe: the M2 exe `forge_r5a_m2_0a01ec53.exe` (fda298e6...;
search identical to the base and to the M5 head, see M2/M5). Per config:
- 200 games, ON (the option) vs OFF (same exe, defaults), 5+0.05 (Fischer), both Threads 1, Hash 16, OwnBook false;
  100 openings from `8moves_v3.pgn` (read-only; seed per config, indices in summary.json), each played with both
  colours; engines reused across games with `ucinewgame` (as a match runner does), BelowNormal.
- 3 games at once: each game has exactly one engine searching (no pondering), so at most 3 engine threads compute;
  the idle side of each game blocks on stdin (6 engine processes alive, 3 busy).
- Checks per move: bestmove within clock + 3 s, legal (python-chess), side clock >= 0 (wall time go -> bestmove,
  strict, no timemargin; fastchess gates use timemargin=1000), no "ERROR" line, and the M2 echo (ON: exactly one
  `info string active: <opt>` per go; OFF: none). Games end by mate / stalemate / insufficient material / threefold
  or 50-move claim, or at 400 plies (draw).
- Then 50x go/stop stress on the ON engine: `go infinite`, random 10-150 ms, `stop` -> one legal bestmove within
  3 s; `go movetime 300`, random wait, `stop` -> the same; `isready` -> no extra bestmove.
- Measured cost: about 15 s per game (avg ~138 plies), so 200 games take ~16.5 min per config at 3 games at once.
  The 8 configs need ~2.3 h of the 3-thread budget: they run in the job's order (CorrMargins, CorrExt, CorrHistPlus
  2/4/6, NetScale 99, then HistRework 3 and 1 by gate rank) and whatever does not fit is listed under "What I did
  not finish".

Results (PGNs `smoke/<config>/games.pgn`, summaries `smoke/<config>/summary.json`):

<!-- smoke-table -->
(no smoke results yet)
<!-- /smoke-table -->

## M4 gate pack (02:16-02:30 Vienna, written while the smoke ran)

`GATE_SPECS.md` + `gate_specs.json`, both generated by `tools/make_gate_specs.py` from one table (re-run it after
each smoke config to refresh the smoke column). Eight entries R5A-1..R5A-8, one option set each, candidate vs the
same exe all-OFF; fields: name, exe source + sha256 (+ suggested install name; the owner installs), setoption list
(`option.<Name>=<value>`), both-sides Threads 1 / Hash 16 / OwnBook false, primary TC (40+0.4 for CorrExt and
CorrMargins, 10+0.1 otherwise), SPRT `elo0=0 elo1=10 alpha=0.05 beta=0.05 model=normalized`, `cap_games` 3000 (int),
`srand` "" and `openings_start` "" (blank for the queue owner), book 8moves_v3 random, prebench pins (cand_off = lock
pins d11/d13/d16, cand_on = the M1 ON benches), expected echo line, smoke verdict, conflicts with B1-B4, rank reason,
sources. NetScale: one value only (99, S41). A fastchess template with the 3000-game cap (`-rounds 1500 -games 2`)
is at the end of GATE_SPECS.md. Ranking and reasons: "What to gate first" below.

## Milestones
- M1 per-option audit + ON benches: DONE (02:01 Vienna, commit aeb6f093)
- M2 effective-settings echo + conflict guards: DONE (02:15 Vienna)
- M3 smoke stability: not started
- M4 gate pack: written (02:23 Vienna; smoke column refreshes as configs finish)
- M5 SPSA hooks (optional): not started

## What to gate first (ranked; no Elo claims, gates decide; details in GATE_SPECS.md)
1. **R5A-1 CorrHistPlus=4** at 10+0.1: best prior (the related NonPawnCorr+PawnHist pack had a positive LLR in all 4
   of its PC gates, all capped), combinable with B1/B3 (mask 5), cheap. Exclusive with B2/B4 (CorrHistV2).
2. **R5A-2 CorrExt=1** at 40+0.4: independent of all four bundles, so a result transfers; needs the long TC (it equals
   OFF at `go depth 10`; O8 lost at STC).
3. **R5A-3 CorrMargins=1** at 40+0.4: plausible, but it shares the RFP/futility margins with TtPruneV2 (every bundle),
   so a pass needs a combined re-gate with the winning bundle.
4. **R5A-4 CorrHistPlus=2** at 10+0.1: weaker prior; deep trees grow (longer-TC confirm after an H1).
5. **R5A-5 CorrHistPlus=6**: only after 1 and 4.
6. **R5A-6 NetScale=99**: expected about zero (S41 scale mapping); after the option gates, since it moves every margin.
7. **R5A-7 HistRework=3**, 8. **R5A-8 HistRework=1**: conditional on HistRework=2 (B1/B4, R3-08) doing well; 1 fails
   the crew node screen.

## What I did not finish
(filled at the end)
