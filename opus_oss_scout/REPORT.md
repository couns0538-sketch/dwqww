# REPORT - OSS scout for Forge (2026-11-06)

State: **IN PROGRESS**. Trial results are filled in as they finish; STATUS.md shows what is still open.

## 1. Ranking (step 3)

Score = expected impact (1-5) x chance it works on this PC now (1-5). Impact means effect on Forge strength / speed or on
the crew's test / training throughput. Chance means: licence allowed, builds or runs here, fits the CPU / GPU / disk
rules. Both are judgments made from the catalog evidence, written down so they can be argued with. No row is a measured
Elo or speed claim.

| Rank | Pick (trial) | Catalog | Impact | Chance | Score | Why |
|---|---|---|---|---|---|---|
| 1 | UHO_Lichess_4852_v1 book for gates (T1) | C5 | 4 | 5 | 20 | Games per SPRT scale with 1/nElo^2, so a book with higher nElo per pair shortens every gate. The file is already on the PC and fastchess reads EPD |
| 2 | samply Windows profiler (T3) | D1 | 3 | 5 | 15 | First symbolized sampling profile on Windows; the hotspot list from R7 is old and came from Linux perf |
| 3 | bullet for the K32H3^ HalfKA shape (T4, CPU-only part) | A1 | 5 | 2 | 10 | bullet runs v2 nets at 2.8-4.0M pos/s here, while npt trains HalfKA. Open: HalfKA config, exporter, a GPU window, and the GPL/AGPL crates it links |
| 4 | Fathom as an oracle for Forge's own Syzygy reader (T5) | E1 | 2 | 5 | 10 | Independent check of the R13 P6 reader + probe speed; the tables are already on the PC |
| 5 | clang 18 ThinLTO + IR PGO build of the lock source (T2) | D8 | 3 | 3 | 9 | Free nps if the build is node-identical. Risk: the MSVC ASan build of this source gave bench 16 = 2587341 (not the pin 3024920), so the MSVC ABI may change nodes |
| 6 | permissive tooling pick (T6): Lichess puzzles screen (B8) or chess-library PGN tool (C17) | B8 / C17 | 2 | 4-5 | 8-10 | Chosen when T1-T5 are done |
| - | AMD uProf (not trialled) | D5 | 3 | 2 | 6 | Real Zen 5 counters on Windows, but a system install with a driver: owner decision |
| - | Tracy zones (not trialled) | D2 | 3 | 3 | 9 | Needs source zones behind an off-by-default switch: a Coder job, not a sandbox trial |
| - | llvm-mingw (not trialled) | D9 | 3 | 3 | 9 | Follow-up of T2 if the MSVC-ABI build is not node-identical (same CRT as g++) |
| - | 6-piece Syzygy WDL (not trialled) | E5 | 2-3 | 1 | 2-3 | 67.8 GiB; no drive has the room now |

## 2. Trial results (step 4)

Filled in per trial: tool, licence, exact build / run, measured result with the crew load next to it, SHA256SUMS,
PC-specific tuning ideas (`trials/<name>/TUNING.md`).

(pending)

## 3. Ranked table (step 6)

(pending)

## 4. Ideas only (GPL / AGPL / unlicensed)

(pending)

## 5. Unproven claims and owner items

(pending)
