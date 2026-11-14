# Audit of Forge Locked Source (`lock/combo29-20261110`, `forge-combo29/`)

*(Work in progress — initial checkpoint)*

## Start Verification Numbers

Commands executed:
```bash
git fetch origin
git checkout -b audit/lock-source origin/lock/combo29-20261110
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
cmake --build build -j
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```
*(Note: on this Linux container `/etc/alternatives/c++` initially pointed to `/usr/bin/clang++` without matching `libstdc++-14-dev`; switching `/etc/alternatives/c++` to `/usr/bin/g++` (GCC 13.3.0) allowed the exact CMake commands above to run unmodified.)*

Observed output:
- `bench 11`: `info string bench depth 11 nodes 312866` (expected `312866`)
- `bench 13`: `info string bench depth 13 nodes 862329` (expected `862329`)
- `perft 5`: `nodes 4865609` (expected `4865609`)

## Step 1: Complete Source File Inventory (All 20 Source Files + `CMakeLists.txt` Read in Full)

| # | File | Lines |
|---:|---|---:|
| 1 | `include/forge/bitboard.hpp` | 218 |
| 2 | `include/forge/board.hpp` | 314 |
| 3 | `include/forge/book.hpp` | 58 |
| 4 | `include/forge/eval.hpp` | 68 |
| 5 | `include/forge/eval_params.hpp` | 103 |
| 6 | `include/forge/nnue.hpp` | 78 |
| 7 | `include/forge/search.hpp` | 447 |
| 8 | `include/forge/uci_output.hpp` | 12 |
| 9 | `src/bitboard.cpp` | 198 |
| 10 | `src/board.cpp` | 1394 |
| 11 | `src/book.cpp` | 193 |
| 12 | `src/book_data.inc` | 990 |
| 13 | `src/eval.cpp` | 530 |
| 14 | `src/eval_params.cpp` | 88 |
| 15 | `src/eval_params_table.inc` | 640 |
| 16 | `src/nnue.cpp` | 272 |
| 17 | `src/nnue_weights.inc` | 8240 |
| 18 | `src/polyglot_keys.inc` | 198 |
| 19 | `src/search.cpp` | 1818 |
| 20 | `src/uci.cpp` | 430 |
| — | `CMakeLists.txt` | 42 |

*(Findings and proofs under `forge-combo29/tests_audit/` being added next.)*
