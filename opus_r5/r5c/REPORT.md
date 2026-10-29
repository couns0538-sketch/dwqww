# Forge Opus R5C: v4 NNUE (J7 L2=16) engine support + N3 Syzygy / IntendedThreefold / HardDeadline hardening — IN PROGRESS

**Status:** PAUSED at 09:52 Vienna for job R5D (user request: R5D before the next R5C step). Done: 00_baseline, M1. M2: tables sha-verified (290/290), 200-game N3 smoke 200/200 with 0 failures (TB-hit totals in /f/opus_scratch/r5/r5c/smoke/n3/summary.json), prebench pins measured; N3_GATE_SPEC.md not written yet. M3: FNN4_FORMAT.md written; src/nnue_v4.cpp (loader, scalar + AVX2 forward), UCI NNUEv4 / NNUEv4File and the search hook written and compiled (forge_r5c_m3a.exe, 0 warnings, FMA 0), NOT yet tested (no v4 unit test, no parity); M4, M5 not started.

Branch `opus-r5c-netv4` = `origin/forge-bundle-int` b7c1772 + R5C commits. Job folder `opus_r5/r5c/`, scratch
`F:\opus_scratch\r5\r5c\` (exes in `exe\`, sha256 in `EXES.txt`). Machine exclusive: no (live gates, NNUE training
and self-play the whole time). Every build, test and bench at BelowNormal (Git Bash `nice -n 10`), at most 3 threads
in total, engine runs with Threads <= 3 (1 unless a test says otherwise). No Elo claims; no gate run by me.

Time base: the PC clock reads PST but runs 9 h ahead of GitHub's server clock (`gh api -i rate_limit` Date header,
08:19 GMT at 09:20 Vienna); Vienna (CET, UTC+1) = PC "PST" time - 1 h. Every time below is Vienna.
Job start 09:20 Vienna (3 h cap: 12:20 Vienna).

## 00_baseline

Build (job-spec flags, R5B script `tools/build_r5c.sh`, RECIPE=v3: MSYS2 ucrt64 g++ 15.2, 8 units in parallel with
JOBS <= 3 at BelowNormal, static link):
```
RECIPE=v3 bash opus_r5/r5c/tools/build_r5c.sh "$PWD" /f/opus_scratch/r5/r5c/exe/<name>.exe [-D switches]
# g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -mtune=znver5 -pthread -static
```
Check: lock `2_build/uci_check.py <exe> --full` (fresh process, Threads 1, Hash 16, OwnBook false).

## OFF identity after every milestone (rule 7)

| after | exe (F:\opus_scratch\r5\r5c\exe) | sha256 | bench d11 / d13 / d16 / d20 / d22 | perft 5 | kiwipete 5 | FMA | result |
|---|---|---|---|---|---|---|---|
| 00 baseline | forge_r5c_off_v3_b7c1772.exe | 01aed2d9... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_off_v3_b7c1772.log`) |
| M1 | forge_r5c_m1.exe | decc0675... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_m1.log`) |

## M1: N3 hardening (done)

Survey (09:22-09:32 Vienna) of what exists on b7c1772:
- Options: SyzygyPath (string, `syzygy::load`, hash cleared after every load; prints `info string Syzygy: N WDL and M
  DTZ tables, up to K pieces` or `... tablebases off`), SyzygyProbeDepth (1-10), Syzygy50MoveRule (default true),
  IntendedThreefold (check, non-root claim floor at the draw score, no TT cutoffs/stores there), CuckooRep (check,
  upcoming-repetition draw lower bound), HardDeadline (0-1000 ms, watchdog at hard limit + N ms, time-critical).
- Tests already there: tests/syzygy_tests.cpp (empty / missing / junk / truncated / corrupt / partial table folders,
  TB score TT encoding, known answers; real tables via FORGE_SYZYGY_PATH), tests/intended_threefold_tests.cpp,
  tests/cuckoo_tests.cpp, tools/hard_deadline_regression.py (watchdog vs a starved search, forge_debughooks).
- Gap for N3: nothing tests the three N3 options together, IntendedThreefold x CuckooRep, the DTZ root filter near
  the 50-move limit with real 3-4-5 tables, a SyzygyPath change between searches, or the HardDeadline timing of
  `go movetime 50` / `go wtime 100 winc 0` / `go infinite` + `stop` with tables loaded. A wrong SyzygyPath only prints
  "0 WDL and 0 DTZ tables, up to 0 pieces".
- Tables: `D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345` holds 290 files (145 WDL + 145 DTZ); sha check in M2.

What changed (OFF-identical; files: `tests/r5c_n3_tests.cpp`, `tools/r5c_n3_uci.py`, `CMakeLists.txt`, `src/uci.cpp`):
- Engine: one line in the SyzygyPath handler. A non-empty path that loads no table at all now also prints
  `info string SyzygyPath: no tablebase found in "<path>", tablebases off` (the existing
  `info string Syzygy: 0 WDL and 0 DTZ tables, up to 0 pieces` line stays as it was; `tools/uci_options_regression.py`
  matches it exactly). Only reached with a non-empty SyzygyPath, so nodes, perft and the default output are unchanged.
- `tests/r5c_n3_tests.cpp` (CTest `forge_r5c_n3_tests`, real tables via FORGE_SYZYGY_PATH):
  1. IntendedThreefold x CuckooRep, all four combinations: mate in 1 / 2 / 3 at depth 20 give the OFF mate score
     exactly, on a cold and a warm TT; the losing side plays the threefold claim (g8h8, score 0, 64 nodes, the same in
     two runs); the winning side with only repetition chances keeps a winning score (1331-1470 cp, warm TT too).
  2. With the 3-4-5 tables and both draw options on: KQRvK root reported 31870 (TB win; search score 1744, the report
     uses `display_score`); a 6-piece root makes 69 in-search WDL probes; the three blessed losses of the reference are
     reported -2 with Syzygy50MoveRule=true and -31870 with false; DTZ root filtering on 486 reference rows (depth 4):
     every bestmove legal, wins kept, draws not lost, and on 176 wins with the 50-move counter one ply short of the
     fastest win, the chosen move still wins in time with Syzygy50MoveRule=true (dtz + counter <= 101) and wins with
     false.
  3. Wrong paths (missing drive, a folder without tables, separators only) load nothing and every search answers; a
     reload after a wrong path gives the first result again (score 1765, 10680 nodes both times); the empty path gives
     the same startpos depth-10 search as a process that never loaded tables.
  Result: **1397 checks, 0 failures** with the tables (`logs/m1_r5c_n3_tests_local.log`), **52 checks, 0 failures**
  without (`logs/m1_r5c_n3_tests_notables.log`, what CI runs).
- `tools/r5c_n3_uci.py` (CTest `r5c_n3_uci`, CI slack 150 ms): info strings for a missing and an empty folder, `<empty>`
  = off and `bench 13` = 862329 afterwards, real tables 145 / 145 / 5 pieces; then HardDeadline=10 + IntendedThreefold
  + tables, Threads 1, five positions (start, middlegame, KQRvK, a blessed loss, a 6-piece root) x 5 reps x three go
  modes: exactly one legal bestmove each time, slowest go->bestmove 40.8 ms for `go movetime 50` (deadline 50 ms),
  7.3 ms for `go wtime 100 btime 100 winc 0 binc 0` (hard limit 20 ms, deadline 30 ms), 0.7 ms from `stop` for
  `go infinite` (PC run with 5 ms slack: **PASS**, `logs/m1_r5c_n3_uci_pc.log`).

Findings (no bug fixed in the search):
- No wrong draw score and no mate-score corruption in any combination. CuckooRep changes when a mate is found: with
  it on, the KR mate in 3 (`4R3/8/8/k2K4/8/8/8/8 w`) is reported from depth 14, with it off from depth 10 (`go depth
  24`, both report mate 3 afterwards); its draw bounds on the rook shuffles reorder the moves. Not a correctness
  problem, but a CuckooRep gate should know that shallow mates can come a few plies later.
- In TB roots the search score and the reported score differ by design (search 1744 vs reported 31870): tools that
  read `SearchInfo.score` directly must apply `syzygy::display_score` as the UCI layer does.
- The watchdog never had to fire in these runs (the search answered on time by itself); the starved-search case is
  covered by the existing `hard_deadline_regression` (forge_debughooks).

M1 exe `forge_r5c_m1.exe` (v3 recipe, M1 tree): 0 warnings, FMA 0, identity ALL OK (`logs/identity_m1.log`).

## M2: N3 gate pack (in progress; paused for R5D)

- Tables: 290/290 files sha256 OK against opus_r3/R3-1L/syzygy345.sha256 (`logs/m2_syzygy345_sha256_check.log`;
  the checked-out sha list has CRLF, so the check uses an LF copy).
- Book `n3_endgame_book.epd`: 100 of 151 positions with 6-9 pieces, no castling, not in check, from
  tests/data/nnue_selfplay_sample_916.txt (`tools/make_endgame_book.py`).
- Prebench of the candidate (SyzygyPath + IntendedThreefold + HardDeadline=10): 313631 / 866959 / 2460490 /
  11465604 / 31972996, perft5 4865609; only SyzygyPath changes bench (`logs/m2_n3_prebench*.log`).
- Smoke 09:39-09:51 Vienna (`smoke_n3.py`, 200 games 5+0.05, Threads 1, conc 2): games 200/200 with 0 illegal,
  0 crashes, 0 time losses, 0 missing bestmoves; verdict FAIL only from the go/stop stress (96 "illegal bestmove"
  problems): **my runner's bug** - the stress checks legality on a board built from startpos + moves instead of the
  FEN opening. Open items for the resume: (1) fix that board and re-run the stress; (2) the engine prints no
  `tbhits` in its info lines (no `tbhits` in src/), so "count TB hits from info output" needs a small engine change
  (print `tbhits N` only while tables are loaded, OFF output unchanged); the smoke counted 0 for that reason.

## M3: v4 format + engine inference (pending)

## M4: exporter + parity (pending)

## M5: handoff (pending)

## What to gate first (pending)

## What I did not finish (pending)
