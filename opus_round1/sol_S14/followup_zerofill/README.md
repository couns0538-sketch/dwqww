# S14 follow-up: no zero-fill of the move buffers (`FORGE_NOZERO_MOVE_BUFFERS`, default off)

## The switch
- **Off (default):** the AL1 lock code. The PC box-recipe build of this branch differs from the lock exe only in the
  6 PE timestamp/checksum bytes.
- **On:** `-DFORGE_NOZERO_MOVE_BUFFERS=1` (box recipe: an extra `build_pc.sh` argument) or the CMake option
  `-DFORGE_NOZERO_MOVE_BUFFERS=ON`. The move buffers are then left uninitialised:
  - `MoveList::data_` (`include/forge/board.hpp`);
  - `MovePicker::moves_` and `MovePicker::bad_captures_` (`src/search.cpp`).

  Each buffer is an `UninitArray<T, N>`: `std::byte` storage that implicitly creates the `T[N]` array (C++20), read
  through `std::launder`. `Move` is unchanged.
- **What changes with the switch on:** every `MoveList` skips its 1 KiB zero-fill, and so does every picker (3,328 B).
  That covers the picker in qsearch, ProbCut and the main search, plus `Board::has_legal_move`, `perft`,
  `legal_moves` and the root move lists.
- **Contract:** only `[0, size_)`, `[0, count_)` and `[0, bad_count_)` are ever read. With the switch on,
  `MoveList::resize` may only shrink (it asserts this). The only caller, `legal_moves`, only shrinks.
- **Not changed:** the main search's `quiets_tried{}` / `captures_tried{}` (768 B of zmm stores per node).

## Tools (this folder)
| file | what it does |
|---|---|
| `picker_order_oracle.cpp` | Includes `src/search.cpp` and builds pickers in 7 configurations on every root of `tools/openings/forge-10000.epd`, their legal children, and 12 built-in positions. The storage is pre-filled with a pattern (`zero a5 01 ff random`) or is fresh heap memory (`heap`). It records each full pick sequence, with the SEE flag. It also checks pseudo-legality, termination and completeness (each generated move exactly once). Adapted from Sol's S14 oracle. |
| `run_picker_oracle.sh <src> <out> [epd] [children]` | Builds the oracle with the switch off and on, runs every pattern, and requires all runs to print the reference digests. Environment: `CXX`, `ARCH_FLAGS`, `EXTRA_FLAGS`, `LINK_FLAGS`, `PATTERNS`, `RUNNER`, `LIFETIME_FLAG`. |
| `mutation_check.py <src> <scratch> --ref-digest X` | Planted bugs M1 (picker reads past `count_`), M2 (`MoveList::end` past `size_`) and M3 (bad captures past `bad_count_`). Each must make the oracle fail; an unmutated control must reproduce the reference. |
| `codegen_compare_s14.sh <exe_A> <exe_B> [diff_dir]` | O3's codegen compare, plus the MoveList functions, plus per-function counts of memset calls and zmm/ymm stores. |
| `callgrind_callers.py <callgrind.out> --exe forge` | Attributes memset to individual call sites, with addr2line inline chains and groups. Needs `--dump-instr=yes --compress-strings=no --compress-pos=no`. |
| `test_callgrind_callers.py` | Unit tests for the parser (synthetic profiles). |
| `ci_s14fu.sh <check\|asan\|tsan\|profile\|nps>` | The Linux CI driver, used by `.github/workflows/opus-sol-s14fu.yml`. |
| `nps_ab.py` | The paired ABBA NPS tool (unchanged copy from S29/O3/offguard). |

## Reproduce on the PC (Git Bash, nice 19, one thread)
```
T=D:/grok-pc-data/dwqww/.claude/worktrees/b/tools
nice -n 19 bash $T/build_pc.sh "$PWD" /f/opus_scratch/build/S14fu/forge_s14fu_on.exe -DFORGE_NOZERO_MOVE_BUFFERS=1
nice -n 19 $PY -I -B $LA/2_build/uci_check.py /f/opus_scratch/build/S14fu/forge_s14fu_on.exe --full
CXX=/c/msys64/ucrt64/bin/g++.exe ARCH_FLAGS=-march=znver5 LINK_FLAGS=-static \
  nice -n 19 bash opus_round1/sol_S14/followup_zerofill/run_picker_oracle.sh "$PWD" /f/opus_scratch/sol_S14fu/oracle "" 100000
TMPDIR=/f/opus_scratch/sol_S14fu/tmp bash opus_round1/sol_S14/followup_zerofill/codegen_compare_s14.sh lock.exe on.exe
```
On Linux CI: `bash opus_round1/sol_S14/followup_zerofill/ci_s14fu.sh <mode> ci_out`.
