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

Changes after the ranking:
- T2 ran with llvm-mingw (D9), because the installed clang 18 does not compile against the VS 18 STL.
- T6 is the Lichess puzzle screen (B8).
- The final order of section 3 follows the measured results, not these prior scores.

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

### T2 clang build of the lock source (llvm-mingw clang 23.1.5, ISC + LLVM licence)
- The installed LLVM 18 cannot build against the VS 18 STL (STL1000: needs clang >= 20).
- llvm-mingw clang 23 with its own libc++ gives other nodes (bench d11 369996). Cause: libc++ vs libstdc++ tie order
  in the MovePicker's `std::sort`.
- With MSYS2's GCC 15.2 runtime (`--sysroot=C:/msys64/ucrt64 -stdlib=libstdc++ -rtlib=libgcc -unwindlib=libgcc`), the
  ThinLTO + IR-PGO build is **node-identical**: bench d11-d22, perft, net-off and 61 UCI options all equal the lock.
- **Speed vs the lock: +4.72 % [+3.78, +5.66] nps** (bench 20, 10 ABBA pairs on CPU 2 BelowNormal; A/A 1.0052
  [0.9977, 1.0127]). SCREENING on a shared PC (trainer 1.6-1.9 cores on CPUs 0-3).

### T3 profiling on Windows (samply 0.13.1 MIT OR Apache-2.0 + built-in WPR)
- `samply record` needs xperf (Windows ADK): not allowed here.
- `wpr -start CPU` / `wpr -stop` + `samply import` + own `t3_samply_top.py` works with no install.
- Two hotspot tables: the clang bench build with PDB, and the lock exe sampled inside the live gate (COFF symbols).
  - HCE `evaluate_position` 18.6-20.4 %.
  - MovePicker `next` 11.7 % + `std::sort` 3.6-4.8 %.
  - `Move::operator==` 3.4 %.
  - TT probe ~4 % (R7: 10.7 %).

### T4 bullet for the K32H3^ shape (bullet MIT, links GPL-3.0 sfbinpack + AGPL-3.0 montyformat)
- Design check only: every K32H3^ piece has an equivalent in bullet's upstream `examples/advanced`.
- Missing:
  - an exporter to npt's `.nnue` container,
  - one GPU-window run,
  - an owner decision on the GPL / AGPL crates.
- Nothing built (the GPU is busy; bullet has no CPU backend).

### T5 Fathom oracle (MIT) for Forge's own Syzygy reader
- 50,000 random legal 3-5 piece positions: **WDL 50000 / 50000, DTZ 49678 / 49678 exact, AGREE**. That is about
  227x the R13 P6 check, and it uses a permissive oracle.
- Fathom's warm WDL probe is ~1.8x faster (0.54 vs 0.97 us). Small in search.

### T6 Lichess puzzles (CC0) as a fixed-node tactical screen
(pending: runs after T1b)

## 3. Ranked table (step 6)

| Rank | Tool (trial) | Licence | Measured result on grok-pc (load) | Expected Forge gain | Next action | Owner |
|---|---|---|---|---|---|---|
| 1 | clang 23 via llvm-mingw, built against MSYS2 libstdc++, ThinLTO + IR PGO (T2) | ISC (llvm-mingw scripts), Apache-2.0 WITH LLVM-exception (LLVM) | node-identical to the lock (d11-d22, perft, net-off, options); **+4.72 % [+3.78, +5.66]** nps bench 20 vs the g++ LTO+PGO kit exe (A/A SANE, trainer 1.6-1.9 cores on 0xF) | speed only: ~+4-5 % nps if QA confirms; Elo not measured | QA lock path (12k BIT-EXACT, L3b warm identity, Threads 2-4 soak, own ABBA); add a clang line to the kit; try CS-IRPGO and other workloads | QA / Coder |
| 2 | WPR (built-in) + samply import + `t3_samply_top.py` (T3) | Microsoft (WPR), MIT OR Apache-2.0 (samply), own tool | works with no install; symbolized hotspot tables of the bench and of the lock in live gate games | enables targeted speed work: `std::sort` 3.6-4.8 %, `Move::operator==` 3.4 %, HCE 19-20 % | speed crew: bit-exact Move compare; decide on a library-independent move sort (new lock); profile TB / SMP gates the same way | Coder |
| 3 | Fathom (T5) | MIT | **AGREE** with Forge's reader on 50,000 positions; WDL probe 0.54 vs 0.97 us | correctness evidence for the Syzygy line; no Elo by itself | keep as the regression oracle for `syzygy.inc` changes; 50-move / cursed cases next | QA |
| 4 | bullet for K32H3^ (T4) | MIT + GPL-3.0 / AGPL-3.0 crates | design mapping only | if bullet beats npt's ~200-350k pos/s for HalfKA L1 1024, faster net iterations (unmeasured) | exporter to `.nnue` + parity; one GPU-window run (batch 16k / 64k, 2-3 loader threads); licence decision | NNUE |
| 5 | UHO_Lichess_4852_v1 book (T1) | CC0-1.0 | T1a (2:1 node odds): **UHO resolves 13 % worse** (ratio 0.870 [0.794, 0.947]); T1b pending | none shown so far; gate-size changes untested | T1b result; then a near-zero test at gate TC before any book switch | QA |
| 6 | Lichess puzzles (T6) | CC0-1.0 | pending | a fast tactical regression screen (no Elo) | pending | QA / Strength |
| - | AMD uProf 5.3 | proprietary EULA + driver | not tried (system install) | hardware counters on Zen 5 (cache / branch) | owner decision on installing it | Coder |
| - | Tracy | BSD-3-Clause | not tried | SMP / time-management timelines | an off-by-default zone build switch | Coder |
| - | chess-tuning-tools / optuna / nevergrad | Apache-2.0 / MIT / MIT | not tried | few-parameter tuning (time management) beside the own SPSA | optional | Strength |
| - | Lichess eval DB, Stockfish master binpacks, Leela T80-T91 binpacks | CC0 / ODbL / ODbL | not tried (disk) | more or other training data (provenance: other engines' evals) | owner decision on data provenance | NNUE |
| - | 6-piece Syzygy WDL | free tables | not tried (67.8 GiB, no room) | small Elo at 10+0.1 (unmeasured) | when a drive has room | QA |

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

Unproven (labelled so in the trial files):
- T2's +4.72 % is a screening ABBA on a shared PC with a bench-only PGO workload. No QA timing, no 12k BIT-EXACT, no
  warm identity, no Threads 2-4 soak yet. No Elo claim.
- T1: no statement yet about UHO at gate time control or for gate-size changes; T1a covers 2:1 node odds only.
- T4: no HalfKA throughput for bullet on this PC.
- T5's speed ratio is one run on a shared core.

Owner items:
1. **C: disk.** The live npt runs write ~1.4 GB checkpoints to `C:\forge_nnue_train\runs` (C: 65.7 GB at 19:06 ->
   44.5 GB at 20:16). At that rate the disk fills in the evening, which would stop the trainer. Not touched by this job.
2. Licence: every bullet trainer build links GPL-3.0 `sfbinpack` and AGPL-3.0 `montyformat` (catalog A-1). That is
   fine for internal use; it needs a decision before any distribution.
3. QA: time the T2 clang build with the official protocol. Exe `C:\opus_5h\oss_scout\build\t2\m2use_lsx\forge_m2use_lsx.exe`
   (sha256 f982d177...), build script `opus_oss_scout/tools/t2_build.ps1 -Variant m2use -Tag lsx -LibStdCxx`.
4. Coder + owner: a library-independent move sort (stable or own) would make MSVC / libc++ builds node-identical; it
   needs a new lock.
5. NNUE: GPU window for bullet K32H3^ (plan in `trials/t4_bullet_halfka/TUNING.md`).
6. AMD uProf install (hardware counters) - owner decision.
7. Data provenance policy for Stockfish / Lc0-derived data sets (catalog B7, B10, B11).
8. WPR traces are system-wide; this job ran one 6 s trace (20:07:04-20:07:10) while gates were playing.
