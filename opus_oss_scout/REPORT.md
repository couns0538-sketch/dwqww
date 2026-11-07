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

Per trial: tool, licence, the exact build / run (`trials/<name>/CMDS.md`), the measured result with the crew load next
to it (`RESULT.md`), `SHA256SUMS`, and PC-specific tuning ideas (`TUNING.md`).

### T1 book resolution (UHO_Lichess_4852_v1 vs 8moves_v3; Stockfish books CC0, fastchess 1.8.2 MIT)
- **T1a, 2:1 node odds** (lock at 20000 vs 10000 nodes, 600 pairs per book; fixed nodes, so the load does not matter):
  - 8moves: nElo +340.5 [+320.9, +360.2].
  - UHO: nElo +296.3 [+276.7, +316.0].
  - Ratio UHO / 8moves 0.870 [0.794, 0.947]: **at a large gap UHO resolves worse**.
- The gates' own regime is different: 8moves at 10+0.1 has 79.7 % draws (gate_tm_scoreloss1_vs_AL1). T1a does not
  test that regime.
- T1b (1.33:1 node odds) follows; see `trials/t1_books/RESULT.md`.

## 3. Ranked table (step 6)

(pending)

## 4. Ideas only (GPL / AGPL / unlicensed)

These may be read to understand them. No code is copied into Forge; mechanisms must be rewritten in own words.

| Source | Licence | Idea worth an own implementation | Owner |
|---|---|---|---|
| nnue-pytorch (A3) | GPL-3.0 | already the live trainer (run-only). Ideas to port into an own or bullet-based pipeline: the feature factoriser, the loss / lambda schedule, `--validation-*` handling | NNUE |
| Stockfish data tools (B5), binpack-rust (B1), pgn2binpack (B2), chess-binpack-utils (B3) | GPL-3.0 | game-chained binpack storage (far smaller than FPOS 32 B rows); filters (skip captures / in-check / TB-decided rows); PGN -> training rows from the gate PGNs, ~2,100 games per gate already on F: | NNUE |
| montyformat / Monty (F4) | AGPL-3.0 | compact game records with policy data (only via bullet; see A-1) | NNUE |
| marlinflow (A6), CudAD (A5) | GPL-3.0 | older trainer designs (Rust loader + PyTorch; CUDA kernels): nothing that bullet lacks | - |
| fishtest (C6) | no root LICENSE | pentanomial SPRT practice, SPSA schedule (a / c decay); its server code names `UHO_Lichess_4852_v1` (GitHub code search: `server/fishtest/views.py`, `rundb.py`, `util.py`, `worker/games.py`) | QA |
| OpenBench (C4) | GPL-3.0 | SPSA with per-parameter c / r end values, workload splitting | Strength |
| spsa (C12), texel-tuner (C13) | GPL-3.0 | Texel tuning of HCE terms against game results: Forge's lock adds HCE + net, so an own permissive Texel tuner could move HCE weights | Strength |
| WDL_model (C14) | GPL-3.0 | fit of win rate vs eval and material, to set the eval scale so that "100 cp = 50 % win chance at some ply" (input for E3 eval post-processing) | Strength / NNUE |
| cutechess (C2), c-chess-cli (C3) | GPL-3.0 | nothing over fastchess for the gates | - |
| Ordo (C15), BayesElo (C16), pgn-extract (C19), python-chess (C18) | GPL | rating lists across many gates; PGN filters. python-chess stays a run-only test tool in the crew venv | QA |
| Very Sleepy (D4) | GPL-2.0 | sampling without admin rights (samply needs elevation) | Coder |
| Syzygy generator (E3), lila-tablebase (E4) | GPL-2.0 / AGPL-3.0 | none needed: the tables are downloadable, and Forge has an own reader | - |
| Grapheus (A4), viriformat repo (B4), lczero-training (F2), lc0-data-packing (F3) | no LICENSE file | Lc0 data conversion details (how T80-T91 became binpacks: TB rescoring, filters) | NNUE |

## 5. Unproven claims and owner items

(pending)
