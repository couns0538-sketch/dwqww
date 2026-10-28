# R3-5 regression test set: how to run

Six new CTest entries (registered in the last block of CMakeLists.txt; CI runs every CTest in release, ASan+UBSan
and TSan through opus_round1/ci/run_ci.sh, so no CI file had to change):

| CTest name | Program | What it checks |
|---|---|---|
| `forge_perft_cpw` | `forge_perft_suite <tsv> --group cpw` | start position, Kiwipete, CPW positions 3-6, position 4 mirrored |
| `forge_perft_edge` | `forge_perft_suite <tsv> --group edge` | 13 en passant / castling / promotion / pin / check / stalemate cases |
| `forge_draw_rules_tests` | tests/draw_rules_tests.cpp | twofold in search, threefold by history, issue #7 with IntendedThreefold off/on, 50-move rule |
| `forge_tt_mate_tb_tests` | tests/tt_mate_tb_tests.cpp | mate distances through the TT (always); tablebase scores and moves (only with tables) |
| `uci_options_regression` | tools/uci_options_regression.py | every advertised UCI option: valid / invalid / clamped values, strings with spaces, unknown names |
| `smp_uci_regression` | tools/smp_uci_regression.py | Threads 2 and 3: go infinite + stop, go ponder + ponderhit / stop, go nodes, no double bestmove, no hang |

The 20 perft positions and their published counts are in tests/data/perft_suite.tsv (sources in IDEA_SOURCE.md).

## Running

```
# full build + every test (PC): see AGENT_COMMON.md / forge-engine-verify
JOBS=1 nice -n 19 bash /d/grok-pc-data/dwqww/.claude/worktrees/b/tools/cmake_build.sh "$PWD" <build_dir>
cd <build_dir> && ctest --output-on-failure --timeout 600 -R "perft|draw_rules|tt_mate_tb|uci_options|smp_uci"

# with the Syzygy tables (tablebase checks of forge_tt_mate_tb_tests and uci_options_regression)
cmake_build.sh "$PWD" <build_dir> -DFORGE_SYZYGY_PATH=D:/grok-pc-data/dwqww/.claude/worktrees/syzygy345
#   or: FORGE_SYZYGY_PATH=<dir> ctest -R "tt_mate_tb|uci_options"

# programs directly
forge_perft_suite tests/data/perft_suite.tsv [--group cpw|edge|all] [--max-depth D] [--max-nodes N]
forge_draw_rules_tests
forge_tt_mate_tb_tests tests/syzygy_reference.tsv [tablebase_dir]
python3 tools/uci_options_regression.py <forge> [--syzygy DIR] [--workdir DIR] [--log FILE]
python3 tools/smp_uci_regression.py <forge> [--seed N] [--rounds N] [--threads 2,3] [--timeout S] [--log FILE]
```

## Perft depth per build (CMakeLists.txt)

A position runs at its deepest published depth within the caps; positions published only deeper (the small
Sedlak positions at depth 6 or 7, at most 3.9M nodes) run at that depth in every build.

| Build | Caps | Effect |
|---|---|---|
| plain (release, the PC) | `--max-depth 6` | startpos d6, kiwipete d5, CPW3 d6, CPW4/4m/5/6 d5, castling d6, promotions d6, the rest d5-d7 |
| ASan+UBSan (FORGE_ENABLE_SANITIZERS) | `--max-depth 5` | every position at depth >= 5 |
| TSan (`-fsanitize=thread` in CMAKE_CXX_FLAGS) | `--max-depth 5 --max-nodes 20000000` | kiwipete, CPW 5 and 6 at depth 4 (perft is single-threaded: TSan cannot find anything there, and runs ~40x slower) |

Override with `-DFORGE_PERFT_SUITE_ARGS="--max-depth;7"`.

## Tools in this folder

- `tools/perft_crosscheck.py <tsv>`: recomputes every reference count with python-chess (single-threaded; the full
  run takes about 40 minutes on the PC). Log: `logs/perft_crosscheck.log`.
- `tools/mutation_check.py <worktree> <scratch>`: the planted bugs (one-line mutants) and the test each must fail;
  copies `src` and `include` per mutant into a fresh scratch folder, never deletes anything. Log:
  `logs/mutation_check.log`.

## Overlap with older tests (kept on purpose, narrower there)

- tests/tests.cpp: perft of the CPW positions at depth 3-4 only; one repetition and one rule-50 root check.
- tests/intended_threefold_tests.cpp (S-IT): the deep IntendedThreefold checks (TT placeholders, ProbCut, stand
  pat, correction history). R3-5 keeps only the issue #7 numbers in exact form, at the qsearch and the root.
- tests/rule50_tests.cpp: TT entries across the 50-move horizon. R3-5 adds the search-level rules (draw at 100,
  mate on the 100th half-move, resets by captures and pawn moves).
- tests/syzygy_tests.cpp (C1): probing correctness. R3-5 adds search-level scores and moves on a sample of the
  same reference file and the in-search tablebase score through a warm TT.
- tools/uci_regression.py / ponder_regression.py: single-thread UCI behaviour; opus_round1/O1/uci_stress.py: a
  random SMP stress that runs only in the TSan hook. R3-5 runs the SMP stop / ponder scenarios as a CTest in every
  build and the option parsing generically over the advertised options.
