# Forge Opus R5C: v4 NNUE (J7 L2=16) engine support + N3 Syzygy / IntendedThreefold / HardDeadline hardening — IN PROGRESS

**Status:** 00_baseline done; M1 in progress. Last push: see the head commit time (pushes every 10 min).

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

## M1: N3 hardening (in progress)

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

## M2: N3 gate pack (pending)

## M3: v4 format + engine inference (pending)

## M4: exporter + parity (pending)

## M5: handoff (pending)

## What to gate first (pending)

## What I did not finish (pending)
