# R10: HalfKA (K32H3^) inference for nets from the nnue-pytorch trainer

Report: `docs/OPUS_R10_HALFKA.md`. Ideas and sources: `IDEA_SOURCE.md`. Engine code: `src/nnue_halfka.cpp`,
`include/forge/nnue_halfka.hpp`, the search / UCI wiring (`src/search.cpp`, `src/uci.cpp`), the CTest
`tests/halfka_tests.cpp`. PC rules for every run: BelowNormal, pinned off the CPUs of R9 (0-3) and self-play (12-15):
`python -I -B tools/run_pinned.py --mask 0x0FF0 -- <script.py> ...` (children inherit the mask).

## Use
`setoption name EvalFileHalfKA value F:/path/net.nnue` (Windows path); `<empty>` turns it off. Only K32H3^ nets from
nnue-pytorch b2614500 (`--features K32H3^`) load; anything else answers `info string ERROR EvalFileHalfKA: ...`.

## Tools (`tools/`)
| tool | what it does |
|---|---|
| `build_r10.py <src> <out.exe> [-D...]` | box-recipe engine build (`FORGE_EXTRA_SRCS="src/nnue_halfka.cpp"`), sha256, FMA and warning counts |
| `build_tool.py <repo> <tool.cpp> <out.exe> [flags]` | a test program against the engine core with the box flags (`-march=x86-64-v3` appended = AVX2-only build) |
| `halfka_tool.cpp` | `eval <net> <fens> <out>` (raw output per FEN, SIMD vs scalar), `walk <net> <seed> <games> <plies>` (incremental == refresh), `speed <net> <fens> <reps>` (ns per eval stage, HalfKA and the lock's eval) |
| `parity_nnue_pytorch.py` | the trainer's own reader + feature extractor + fake-quantized forward (R6 venv, CPU) -> reference raw outputs; `compare <ref> <forge>` |
| `make_init_net.py` | an untrained K32H3^ net of any L1 written by the trainer's own writer (load / speed tests only) |
| `halfka_uci_check.py <exe> <net> <scratch>` | load, ON bench stable, bad files rejected, off = lock bench |
| `verify_search.py <verify.exe> <net>` | a `-DFORGE_HALFKA_VERIFY` build through bench + 3-thread searches (every lazily built row checked) |
| `wac_tactics.py` | the lock's WAC harness (env `OPTS="EvalFileHalfKA=<net>"`) |
| `fast_games.py <exe> <net> <out>` | N fastchess games ON vs OFF, every termination checked |
| `nps_opts_ab.py`, `nps_ci.py` | same-exe option sets, or two builds with `exe=<path>` sets; paired 95% intervals |
| `mutants_halfka.py <repo> <fresh dir>` | planted bugs in `src/nnue_halfka.cpp` against the CTest |
| `run_ctest.sh <src> <build dir> <log>` | CMake all targets + CTest + the known-failure check |
| `exe_run.py`, `bash_run.py`, `run_pinned.py` | run a program / a bash script under the pinned BelowNormal parent |
| `patch_r10_search.py`, `patch_r10_uci.py` | the anchored patches that wired the path into the lock's search and UCI (applied) |

## Data
`nets/smoke_k32h3_l64.nnue` (CPU smoke net, used by the CTest), `nets/SHA256SUMS_nets.txt` (all three nets; the R6 and
L1 1024 nets stay in `F:\opus_scratch\r10\nets`), `parity/fens_12k.txt` (12,000 self-play positions, all piece-count
buckets). Logs of every step: `logs/`. Skills written in R10: `skills/` (copies of the project skills).
