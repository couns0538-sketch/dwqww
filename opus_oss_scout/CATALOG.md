# CATALOG - open-source tools, libraries and data for Forge (survey 2026-11-06)

How the rows were made:
- **Licence**: the SPDX id that the GitHub API reports for the repo (`gh api repos/<r>`). For NOASSERTION or "none", the
  root LICENSE file was read with `tools/licence_at.py` (a copy of `opus_deepres/tools/licence_at.py`).
- **Last activity**: `pushed_at` of the default branch, read on 2026-11-06.
- **Expected gain**: one of three kinds, never estimated:
  - a crew-measured number with its source,
  - an upstream claim with its link,
  - "unmeasured".
- **Rule for use**: MIT / BSD / Apache / ISC / zlib / MPL / CC0 code or tools may be used. GPL / AGPL / LGPL and
  unlicensed repos are ideas-only (read to understand, never copy code into Forge).
- **Data sets** carry their data licence. Data from another engine (Stockfish evals, Lc0 games) is an owner decision
  about provenance, even when the licence allows it.

Status: **in use** = the crew already runs it; **new** = not used by the crew yet; **skip** = no fit on this PC, or
ideas-only. Effort: S < 2 h, M = a day, L = several days.

## A. NNUE training: trainers and the GPU stack

| # | Name | Repo / page | Licence | Last activity | What it gives Forge | Expected gain (evidence) | Fit on grok-pc | Effort | Status |
|---|---|---|---|---|---|---|---|---|---|
| A1 | bullet | https://github.com/jw1912/bullet | MIT ([LICENSE](https://github.com/jw1912/bullet/blob/main/LICENSE)); **but** `bullet_lib` links crates.io `sfbinpack` 0.6.4 (GPL-3.0) and `montyformat` 0.9.2 (AGPL-3.0), see note A-1 | 2026-11-05 (head 5d701776) | GPU NNUE trainer (CUDA, ROCm, Metal); loaders for Stockfish / Viridithas / Monty binpacks and bulletformat | v2 nets on this GPU: 2.8M pos/s on CPUs 4-5, 4.0M on CPUs 3-5 (30-h job, `D:\o30\FINAL_REPORT.md`); the HalfKA (K32H3^) shape is not measured | ROCm build proven (R14 P4, 30-h job: VS 18 vcvars + npt venv HIP SDK + gfx1100); GPU booked by npt to Nov 8 | M (HalfKA config + exporter) | in use (v2); HalfKA open -> trial T4 |
| A2 | bullet-utils | https://github.com/jw1912/bullet/tree/main/crates/utils | MIT; links `montyformat` (AGPL-3.0) | 2026-11-05 | convert text `FEN \| score \| result` to bulletformat, shuffle, interleave | unmeasured | builds with the same cargo toolchain | S | new |
| A3 | nnue-pytorch | https://github.com/official-stockfish/nnue-pytorch | GPL-3.0 | 2026-11-01 | the live npt trainer (R6 Triton port on ROCm). The crew fork `F:\opus_scratch\r6\nnue-pytorch-amd` = upstream b2614500 (#563 "K32H3 & Refactors", 2026-10-28) + 4 AMD commits. That already includes the October loader / memory / overhead work (e.g. afa956b9 "Reduce data loader host memory by ~14 GiB per rank", fbd2de1a, ab7f8b7b). Upstream after b2614500: only 4 small commits (LR / lambda logging, `--estimate-size`, a loader error message, `--histogram`) | R6: Triton FT 448-467k pos/s vs 210k plain (memory `opus-r6-amd-status`) | runs now (Idle, mask 0xF) | - | in use (run-only); nothing to port for speed |
| A4 | Grapheus | https://github.com/Luecx/Grapheus | no LICENSE file at 2119312 (all rights reserved) | 2025-03-08 | trainer; README is only a title | unmeasured | unknown backend | - | skip (unlicensed) |
| A5 | CudAD | https://github.com/Luecx/CudAD | GPL-3.0 | 2022-11-30 | CUDA trainer of Koivisto | unmeasured | CUDA Toolkit required -> no on the AMD card | - | skip |
| A6 | marlinflow | https://github.com/jnlt3/marlinflow | GPL-3.0 | 2025-04-14 | PyTorch + Rust loader trainer (Black Marlin; used by Viridithas, Svart in the past) | unmeasured | PyTorch ROCm would work; superseded by bullet | - | skip (ideas-only) |
| A7 | PyTorch | https://github.com/pytorch/pytorch | BSD-3-Clause style ([LICENSE](https://github.com/pytorch/pytorch/blob/main/LICENSE)) | 2026-11-06 | framework under npt | - | ROCm wheels in the npt venv | - | in use |
| A8 | TheRock (ROCm build system and wheels) | https://github.com/ROCm/TheRock | MIT | 2026-11-06 | ROCm SDK / PyTorch wheels for Windows on gfx110X; the `_rocm_sdk_devel` HIP SDK that bullet builds use | - | in the npt venv (`F:\nnue_pytorch\venv`), read-only for builds | - | in use |
| A9 | triton-windows | https://github.com/woct0rdho/triton-windows | MIT | archived (last push 2026-02-18) | Triton for NVIDIA GPUs on Windows | - | no (NVIDIA only; the AMD Triton comes with the ROCm wheels) | - | skip |

Note A-1 (licence finding): `crates/bullet_lib/Cargo.toml` at 5d701776 lists `sfbinpack = "0.6.4"`,
`viriformat = "2.0.1"` and `montyformat = "0.9.2"` as plain dependencies. crates.io gives their licences as:
- `sfbinpack`: GPL-3.0 (repo Disservin/binpack-rust).
- `viriformat`: MIT.
- `montyformat`: AGPL-3.0 (repo official-monty/Monty).

So every bullet trainer binary contains GPL-3.0 and AGPL-3.0 code. Using it as an internal tool is fine, and the nets
it writes are data. Never copy bullet or its crates into Forge, and do not distribute a built trainer without checking
the terms. The crew's 30-h job builds are affected in the same way.

## B. NNUE data tools and data sets

| # | Name | Repo / page | Licence | Last activity | What it gives Forge | Expected gain (evidence) | Fit on grok-pc | Effort | Status |
|---|---|---|---|---|---|---|---|---|---|
| B1 | binpack-rust (`sfbinpack` crate) | https://github.com/Disservin/binpack-rust | GPL-3.0 | 2026-07-09 | Rust reader/writer for Stockfish binpacks (bullet's loader dependency) | unmeasured | builds with cargo | - | ideas-only (run-only inside bullet) |
| B2 | pgn2binpack | https://github.com/Disservin/pgn2binpack | GPL-3.0 | 2026-08-29 | PGN -> binpack (could turn gate PGNs into training data) | unmeasured | Rust | - | ideas-only |
| B3 | chess-binpack-utils | https://github.com/Disservin/chess-binpack-utils | GPL-3.0 | 2026-09-18 | binpack utilities | unmeasured | Rust | - | ideas-only |
| B4 | viriformat | https://github.com/cosmobobak/viriformat (repo: no LICENSE file); crate `viriformat` 3.0.0 on crates.io = MIT | crate MIT / repo unlicensed | 2026-10-03 | compact game-record format with reference readers; bullet's `ViriBinpackLoader` | unmeasured | Rust | S | new (crate only, after reading its packaged licence) |
| B5 | Stockfish data tools (nnue-pytorch / Stockfish "tools") | https://github.com/official-stockfish/Stockfish | GPL-3.0 | 2026-11-06 | gensfen / rescore / filter / interleave | - | - | - | ideas-only |
| B6 | Lichess standard games | https://huggingface.co/datasets/Lichess/standard-chess-games | CC0-1.0 | card 2025-10-16 | 6.77 billion rated games (parquet): opening books, position sources, no labels | unmeasured | download by monthly parquet shard | S-M | new (data) |
| B7 | Lichess position evaluations | https://huggingface.co/datasets/Lichess/chess-position-evaluations | CC0-1.0 | card 2026-10-07 | 416 million positions with Stockfish evals at various depths | unmeasured | parquet shards | M | owner decision (Stockfish-derived labels) |
| B8 | Lichess puzzles | https://huggingface.co/datasets/Lichess/chess-puzzles | CC0-1.0 | card 2026-10-07 | 6.16 million rated, tagged puzzles: a large tactical screen for search changes (fixed-node solve rate) | unmeasured | parquet, small | S | new -> T6 candidate |
| B9 | Lichess openings | https://huggingface.co/datasets/Lichess/chess-openings | CC0-1.0 | card 2026-05-20 | 3,704 ECO-classified openings | - | small | S | new (data) |
| B10 | Stockfish master binpacks | https://huggingface.co/datasets/official-stockfish/master-binpacks | ODbL | card 2026-04-12 | the binpacks used for Stockfish nets (nnue-pytorch format, which Forge's npt line already reads) | unmeasured | large; no room now (disk) | M | owner decision (provenance, ODbL notice) |
| B11 | Leela T80 / T90 / T91 binpacks | https://huggingface.co/datasets/xushawn/t80-binpacks-raw-old, https://huggingface.co/datasets/xushawn/t90-binpacks-raw, https://huggingface.co/datasets/adamtwiss/t91-binpacks-filtered | ODbL | 2026-04 to 2026-08 | Lc0 self-play data converted to binpack (the T80 card says: with 3-4-5 TBs) | unmeasured | large | M | owner decision |
| B12 | chessdb.cn snapshots | https://huggingface.co/datasets/chessdb/snapshots | LGPL-3.0 | card 2026-07-05 | static dumps of chessdb.cn (openings, positions) | unmeasured | very large | - | owner decision |
| B13 | Lichess database site code | https://github.com/lichess-org/database | AGPL-3.0 (code); the data is CC0 (B6-B9 cards) | 2026-11-03 | how the monthly exports are built | - | - | - | ideas-only |

## C. Testing: match runners, books, statistics, tuning, PGN / EPD tools

| # | Name | Repo / page | Licence | Last activity | What it gives Forge | Expected gain (evidence) | Fit on grok-pc | Effort | Status |
|---|---|---|---|---|---|---|---|---|---|
| C1 | fastchess | https://github.com/Disservin/fastchess | MIT | master 2026-11-05; newest release v1.8.2-alpha 2026-07-26 | the gate runner | master has 16 commits since 1.8.2, all fixes / refactors (see note C-1): nothing changes a 10+0.1 gate | own copy of 1.8.2 runs in trial T1 | - | in use (stay on 1.8.2) |
| C2 | cutechess | https://github.com/cutechess/cutechess | GPL-3.0 | 2026-09-01 | GUI + cli runner | - | - | - | ideas-only |
| C3 | c-chess-cli | https://github.com/lucasart/c-chess-cli | GPL-3.0 | 2023-10-29 | small runner | - | - | - | ideas-only |
| C4 | OpenBench | https://github.com/AndyGrant/OpenBench | GPL-3.0 | 2026-11-04 | distributed SPRT + SPSA framework | - | single PC: little use | - | ideas-only |
| C5 | Stockfish books (UHO, 8moves, ...) | https://github.com/official-stockfish/books | CC0-1.0 | 2026-10-16 | opening suites; the gates use 8moves_v3 (sha 5835239F), UHO_Lichess_4852_v1.epd is already on the PC (sha 7A7F6470) | games per SPRT scale with 1/nElo^2: measured in **trial T1** | file on the PC | S | in use (8moves) / new (UHO) -> T1 |
| C6 | fishtest | https://github.com/official-stockfish/fishtest | no root LICENSE at 5a8a229 | 2026-10-26 | SPRT / pentanomial statistics, SPSA schedule, worker design | - | - | - | ideas-only |
| C7 | pentanomial | https://github.com/vdbergh/pentanomial | MIT | 2021-05-13 | a pentanomial SPRT reference implementation + simulator (Python) | - | Python | S | new (cross-check for the crew's own LLR tools) |
| C8 | weather-factory | https://github.com/jnlt3/weather-factory | MIT | 2024-12-23 | SPSA tuner driving fastchess / cutechess | unmeasured; the crew has own SPSA tuners (R9, 30-h job) | Python | S | skip (duplicate) |
| C9 | chess-tuning-tools | https://github.com/kiudee/chess-tuning-tools | Apache-2.0 ([LICENSE](https://github.com/kiudee/chess-tuning-tools/blob/master/LICENSE)) | 2025-10-27 | Bayesian optimisation (Gaussian process) of a few engine parameters with expensive match evaluations | unmeasured | Python + scikit-optimize | M | new (for few-parameter jobs: time management) |
| C10 | nevergrad | https://github.com/facebookresearch/nevergrad | MIT | 2026-11-02 | derivative-free optimisers (CMA-ES, SPSA variants, ...) | unmeasured | Python | M | new (low) |
| C11 | optuna | https://github.com/optuna/optuna | MIT | 2026-11-04 | TPE / CMA-ES with pruning, for offline tuning (net hyper-parameters, eval-scale fits) | unmeasured | Python | M | new (low-medium) |
| C12 | spsa (Kiiski) | https://github.com/zamar/spsa | GPL-3.0 | 2017-07-15 | the classic SPSA tuner for engines | - | - | - | ideas-only |
| C13 | texel-tuner | https://github.com/GediminasMasaitis/texel-tuner | GPL-3.0 | 2026-08-09 | Texel tuning of HCE terms (the lock adds HCE + net, so HCE terms matter) | - | - | - | ideas-only (an own permissive tuner would be needed) |
| C14 | WDL_model | https://github.com/official-stockfish/WDL_model | GPL-3.0 | 2026-09-27 | fit of win / draw / loss rates as a function of eval and material | - | - | - | ideas-only (eval-scale ideas for E3) |
| C15 | Ordo | https://github.com/michiguel/Ordo | GPL-3.0 | 2023-09-15 | rating lists from PGN | - | - | - | ideas-only |
| C16 | BayesElo | https://www.remi-coulom.fr/Bayesian-Elo/ (author page: "freeware") | GPL-3.0 per the source copy https://github.com/ddugovic/BayesianElo (archived, last push 2015-07-02) | 2015 | rating lists | - | - | - | ideas-only |
| C17 | chess-library | https://github.com/Disservin/chess-library | MIT | 2026-11-03 | header-only C++ move generation + fast PGN parser (fastchess uses it): a permissive base for own PGN / EPD / data tools | unmeasured | g++ 15.2 / clang 18 | S | new -> T6 candidate |
| C18 | python-chess | https://github.com/niklasf/python-chess | GPL-3.0 | 2026-08-22 | Python chess tooling (in the crew's read-only venv) | - | - | - | in use (run-only) |
| C19 | pgn-extract | https://www.cs.kent.ac.uk/people/staff/djb/pgn-extract/ | GPL (v3 per current packagers) | - | PGN filtering / conversion | - | - | - | ideas-only |

Note C-1 (fastchess since v1.8.2-alpha, read with `gh api repos/Disservin/fastchess/commits?since=2026-07-27`):
- #1066 "handle timeouts at time control boundaries": defers the next time-control period. It matters for moves/time
  controls, not for 10+0.1.
- #1065 duration parsing.
- #1063 ignore SIGPIPE from crashed engines (POSIX).
- #1075 SIGTERM like SIGINT.
- #1074 chess library update.
- The rest are refactors (CLI parsing, info-line tokens, fmt) and test updates.

## D. Engine speed: profilers, toolchains, build and micro-benchmark tools

| # | Name | Repo / page | Licence | Last activity | What it gives Forge | Expected gain (evidence) | Fit on grok-pc | Effort | Status |
|---|---|---|---|---|---|---|---|---|---|
| D1 | samply | https://github.com/mstange/samply | MIT OR Apache-2.0 (LICENSE-MIT + LICENSE-APACHE) | 2026-11-02; release 0.13.1 2025-02-01 | sampling profiler; on Windows it records with ETW and shows the Firefox Profiler; on- and off-CPU samples at 1 kHz (README) | enables targeted speed work (no direct gain) | the session is elevated (ETW needs admin) | S | new -> trial T3 |
| D2 | Tracy | https://github.com/wolfpld/tracy | BSD-3-Clause ([LICENSE](https://github.com/wolfpld/tracy/blob/master/LICENSE)) | 2026-11-05 | frame / zone profiler with timelines: Lazy SMP threads, time management, NNUE refresh | unmeasured | needs zones in the code behind an off-by-default build switch | M | new |
| D3 | Optick | https://github.com/bombomby/optick | MIT | 2024-05-25 | zone profiler (similar to Tracy) | unmeasured | Windows OK | M | skip (Tracy is more active) |
| D4 | Very Sleepy | https://github.com/VerySleepy/verysleepy | GPL-2.0 | 2023-10-16 | Windows sampling profiler, no admin needed | - | - | - | ideas-only |
| D5 | AMD uProf 5.3.521 | https://www.amd.com/en/developer/uprof.html | proprietary EULA; the Windows installer installs a driver | release 2026-06-17 | time-based, event-based and IBS sampling on Zen 5 under Windows 11: the only tool here with real hardware counters (cache misses, branch misses, IBS latency) | unmeasured | system install + driver: not allowed in this job | M | owner decision |
| D6 | Intel VTune | https://www.intel.com/content/www/us/en/developer/tools/oneapi/vtune-profiler.html | proprietary | 2026 docs | the user-mode hotspots mode is documented; hardware sampling relies on Intel PMU drivers | - | weak on AMD | M | skip |
| D7 | Windows Performance Recorder + Analyzer | https://learn.microsoft.com/windows-hardware/test/wpt/ | Microsoft licence | built into Windows 11 | ETW CPU sampling; `C:\Windows\System32\wpr.exe` exists (capture with no install); WPA needs the ADK | - | capture yes, viewer needs an install | S | new (fallback to D1) |
| D8 | LLVM 18.1.8 (installed) | https://github.com/llvm/llvm-project | Apache-2.0 WITH LLVM-exception | 2026-11-06 | clang-cl, lld-link ThinLTO, IR / CS-IR PGO (`clang_rt.profile-x86_64.lib`, `llvm-profdata`), `llvm-mca`, `llvm-symbolizer`, all in `C:\Program Files\LLVM\bin` | measured in **trial T2** | installed; needs VS 18 BuildTools vcvars64 | S | new -> T2 |
| D9 | llvm-mingw | https://github.com/mstorsjo/llvm-mingw | ISC (scripts; [LICENSE.txt](https://github.com/mstorsjo/llvm-mingw/blob/master/LICENSE.txt)) + bundled LLVM / mingw-w64 licences | 2026-11-04 | a portable clang for the MinGW ABI (the same CRT as the lock's g++) with current LLVM | unmeasured | zip, no install | S-M | new (after T2, if clang-cl looks promising) |
| D10 | BOLT | https://github.com/llvm/llvm-project/tree/main/bolt | Apache-2.0 WITH LLVM-exception | 2026-11-06 | post-link layout optimiser | README: "BOLT operates on X86-64 and AArch64 ELF binaries" | **no**: Forge ships Windows PE exes (only usable on Linux CI builds) | - | skip |
| D11 | Propeller | https://github.com/google/llvm-propeller | Apache-2.0 | 2026-11-03 | profile-guided relinking from perf LBR samples | - | Linux ELF + perf only | - | skip |
| D12 | google/benchmark | https://github.com/google/benchmark | Apache-2.0 | 2026-11-06 | micro-benchmark harness (NNUE update / movegen kernels) | unmeasured | builds with g++ / clang | S | new (low-medium) |
| D13 | nanobench | https://github.com/martinus/nanobench | MIT | 2026-09-07 | single-header micro-benchmarks with stable statistics | unmeasured | header only | S | new (low-medium) |
| D14 | sccache | https://github.com/mozilla/sccache | Apache-2.0 | 2026-11-06 | compiler cache (gcc, clang, MSVC) | small: LTO + PGO kit builds cache poorly | single exe | S | skip (low) |
| D15 | hyperfine | https://github.com/sharkdp/hyperfine | MIT OR Apache-2.0 | 2026-11-01 | CLI timing with statistics | none over the crew's ABBA tools | single exe | S | skip |
| D16 | mimalloc | https://github.com/microsoft/mimalloc | MIT | 2026-11-06 | fast allocator | none expected: the search does not allocate in hot paths | - | S | skip |
| D17 | SIMDe | https://github.com/simd-everywhere/simde | MIT | 2026-11-04 | portable intrinsics | none: Forge already has AVX2 / AVX-512 / VNNI kernels | - | - | skip |
| D18 | Highway | https://github.com/google/highway | Apache-2.0 OR BSD-3-Clause | 2026-11-06 | runtime-dispatched SIMD (one exe for many CPUs) | none for a per-CPU build | - | M | skip |
| D19 | Large pages (own switch H1 / H7) | crew branch `opus-speed-20261105` (HUNT, 2026-11-06) | own code | 2026-11-06 | TT / net in large pages | measured NO-WIN on a quiet PC: H1 -0.19 %; H7 +0.61 % [1.0006, 1.0227], below half the A/A width (QA WIN rule) | needs contiguous RAM (error 1450 while the trainer runs) | - | done by the crew (do not redo) |

## E. Endgame: tablebase probing and generation

| # | Name | Repo / page | Licence | Last activity | What it gives Forge | Expected gain (evidence) | Fit on grok-pc | Effort | Status |
|---|---|---|---|---|---|---|---|---|---|
| E1 | Fathom | https://github.com/jdart1/Fathom | MIT | 2025-12-24 | Syzygy WDL / DTZ probe library (C) | Forge already has an own reader (R13 P6, `include/forge/syzygy.hpp`, "no third-party probing code"); Fathom serves as an independent oracle + speed reference | g++ 15.2 | S | new -> trial T5 |
| E2 | Pyrrhic | https://github.com/AndyGrant/Pyrrhic | MIT ([LICENSE](https://github.com/AndyGrant/Pyrrhic/blob/master/LICENSE)) | 2026-05-28 | Fathom fork (used by Ethereal-style engines) | unmeasured | g++ | S | new (second oracle) |
| E3 | Syzygy generator | https://github.com/syzygy1/tb | GPL-2.0 | 2025-10-03 | table generator (README: >= 16 GB RAM for 6 pieces) | - | not needed: the tables can be downloaded | - | ideas-only |
| E4 | lila-tablebase | https://github.com/lichess-org/lila-tablebase | AGPL-3.0 | 2026-10-15 | the tablebase server behind tablebase.lichess.ovh (public API for spot checks) | - | API use only | - | ideas-only (code) |
| E5 | Syzygy table files | https://syzygy-tables.info/ | free download (mirrors: tablebase.lichess.ovh, tablebase.sesse.net) | - | 3-5 pieces 939.0 MiB (145 tables); 6 pieces 149.2 GiB (WDL 67.8 GiB); 7 pieces 16.7 TiB | 3-5 pieces are on the PC (`D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345`, 291 files, 938 MB) | 6-piece WDL needs ~68 GiB free on one drive: not now (C: 58, D: 47, F: 53 GB) | - | in use (3-5, R3 self-play) |

## F. Other

| # | Name | Repo / page | Licence | Last activity | What it gives Forge | Status |
|---|---|---|---|---|---|---|
| F1 | Lc0 | https://github.com/LeelaChessZero/lc0 | GPL-3.0 | 2026-11-03 | source of the T80-T91 data (B11) | ideas-only |
| F2 | lczero-training | https://github.com/LeelaChessZero/lczero-training | no root LICENSE at ee626a9 | 2026-11-02 | training-data formats | ideas-only |
| F3 | lc0-data-packing | https://github.com/xu-shawn/lc0-data-packing | no LICENSE | 2026-06-21 | Lc0 -> binpack converter (made B11) | ideas-only |
| F4 | Monty | https://github.com/official-monty/Monty | AGPL-3.0 | 2026-05-12 | source of the `montyformat` crate that bullet links (A-1) | ideas-only |

Rows: A 9, B 13, C 19, D 19, E 5, F 4 = **69 entries**.
