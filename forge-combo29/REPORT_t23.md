# Report t23: `go mate N` and stale scores near the 50-move rule

- **Repository**: `github.com/couns0538-sketch/dwqww`
- **Base branch**: `integrate/combo29-fixes` (`bf5574ee654a773f0ef3d06878707056b90cdad7`)
- **Task branch**: `carbon/t23-mate-and-fifty`

---

## 1. Summary of Findings

### Fault A: `go mate N` misses forced mates within `2*N - 1` plies

In `Worker::search` (`forge-combo29/src/search.cpp`), `go mate N` caps iterative deepening at `mate_depth = 2 * N - 1` plies (`limits.mate_moves > 0`), which is the exact number of plies in an `N`-move forced checkmate (`N` attacker moves and `N - 1` defender replies). Inside `Worker::search` and `Worker::qsearch`, however, normal forward pruning, reductions, and unadjusted TT cutoffs remained active when `mate_moves > 0`:

1. **Late Move Reductions (`src/search.cpp`, old line 1412)** and **Internal Iterative Reductions (`src/search.cpp`, old line 1290)** reduced quiet and late moves below the remaining mate horizon `2 * N - 1`, so the mating line hit `qsearch` early, stood pat on a material score instead of generating quiet mating moves, and never reached the checkmate leaf.
2. **Forward pruning (`src/search.cpp`, old lines 1201–1286 and 1326–1350)** — razoring, reverse futility pruning, null-move pruning, ProbCut, late-move pruning, futility pruning, history pruning, SEE pruning — plus singular negative extensions (`src/search.cpp`, old lines 1372–1375) and `qsearch` capture futility/SEE pruning (`src/search.cpp`, old lines 1062–1070) discarded quiet setups and sacrifices (e.g., quiet queen/rook moves while down material, or queen sacrifices with negative SEE like smothered/back-rank mates).
3. **Mate-bound TT cutoffs (`src/search.cpp`, old lines 1021 and 1170)** and lack of mate-distance pruning in `qsearch`: TT bounds stored under mate-distance-pruned windows could cut off a wider mate search, and `Worker::search`'s early-exit check (`MateValue - std::abs(score) <= mate_depth`, old line 1714) did not require `score > 0` (so being mated in `<= N` would also stop early).

On the 40-position judge-verified suite (`tests_t23/mate_solver_test.cpp`: 30 forced mates in 1, 2, or 3 across rook, queen, two-bishop, and 10 constructed middlegame positions, plus 10 non-mate positions), the unchanged base **missed 15 out of 30 forced mates** (`missed_mates=15`, `false_mates=0`), including `8/8/8/8/2R5/k7/8/1K6 w - - 0 1` with `go mate 2` (`score cp 483`, move `c4g4`).

### Fault B: Stale scores near the 50-move rule (warm vs. empty hash table)

#### Interaction of the hash table and half-move clock in the unchanged base

1. **Zobrist key (`forge-combo29/src/board.cpp:1372–1382`, `Board::compute_key`)**: `halfmove_` is **not** part of the Zobrist key `key_`. The same board placement/castling/ep/side at clock 0 and clock 98 hashes to the exact same `TTEntry`.
2. **TT entry storage & `score_usable` (`forge-combo29/include/forge/search.hpp:82, 91–94`, `src/search.cpp:331, 400`)**: Each `TTEntry` stores `rule50_clock = min(halfmove_clock, 100)`. `TTEntry::score_usable(current_clock)` returns `(rule50_clock < 90 && capped < 90) || rule50_clock == capped`.
3. **Main search vs. `qsearch` TT cutoffs (`forge-combo29/src/search.cpp`, old lines 1162–1175 and 1015–1025)**:
   - In `Worker::search` (old line 1171), TT cutoffs are refused when `board.halfmove_clock() >= 90` (`board.halfmove_clock() < 90`), **but**:
     - `tt_move = tt_hit ? tte.move : Move::none()` (old lines 1015 and 1161) and `ss->tt_pv` (old lines 1020 and 1167) unconditionally reuse `tte.move` and `tte.pv()` from low-clock TT entries (`tte.rule50_clock < 90`) even when `board.halfmove_clock() >= 90`!
     - In `Worker::qsearch` (old lines 1021–1025), there is **no** `board.halfmove_clock() < 90` guard on TT cutoffs at all. If a position was searched at clock 95 (say root clock 95 -> ply 2 clock 97, where `qsearch` stood pat at `+521` and stored `rule50_clock = 97`), a subsequent search from root clock 97 reaches that exact node at `rule50_clock == 97`, `score_usable(97)` returns `true`, and `qsearch` takes a direct TT cutoff!
   - **Draw score storage (`src/search.cpp:909–918, 1003, 1138`)**: When `halfmove_clock() >= 100` (and not checkmate), `is_draw` returns `0` immediately *before* probing or storing in the TT, so terminal 50-move draws at `clock == 100` are not stored directly; ancestor nodes (`clock < 100`) store `0` with their own `halfmove_clock`.
4. **How low-clock TT entries corrupt clock 96–99 searches (`src/search.cpp`, old lines 1161, 1201, 1326, 1412)**:
   - When searching at high clock (e.g., clock 98 on `8/7p/5k2/4nN2/8/8/1KQ5/8 w - - 98 50`, or clock 97 on `8/7p/6k1/5n2/8/8/1KQ5/8 w - - 97 50`, or clock 96 on `8/7p/6k1/8/8/1BN5/1K6/8 w - - 96 50`) after warming the table at clock `0`:
     - At the defender's node at `clock == 99` (1 ply from the 50-move draw, so **every legal quiet non-pawn move immediately draws (`0`) at the next ply**), the warm TT supplies a low-clock `tt_move` that is a **pawn push or capture** (e.g., `h7h5` or `f6f5`).
     - Playing that `tt_move` resets `halfmove_clock` to `0`! In the resulting `clock == 0` subtree, all low-clock TT entries (`rule50_clock < 90`) become `score_usable(0) == true` and eligible for immediate TT cutoffs (`halfmove_clock() < 90`), returning `+576` for White (`-576` for Black) and setting `best_score = -576 > -MateInMaxPly`.
     - Immediately afterward, in `Worker::search` (old lines 1326–1337 and 1412–1428), shallow-depth pruning (`lmp_threshold`, futility pruning `static_eval + FutilityBase + FutilityMultiplier * lmr_depth <= alpha`) and LMR fire because `best_score > -MateInMaxPly` is now true (and/or LMR reduces quiet moves into `qsearch` before reaching `clock == 100`). Every quiet drawing move by the defender is skipped (`skip_quiets = true`) or reduced short of ply 100!
     - As a result, at clock 98 (`8/7p/5k2/4nN2/8/8/1KQ5/8 w - - 98 50`, depth 4), the warm search returns **`+576`** (and TT-only with cleared worker histories returns **`+590`**), whereas the empty-table search returns **`0`**. Across our 20-case test suite (`tests_t23/fifty_move_tt_test.cpp`, clocks 96–99), 11 cases failed on the unchanged base (and 78 combinations failed in our broader matrix scan).

---

## 2. The Change (in Three Sentences)

1. For `go mate N` (`mate_moves_ > 0`), `Worker` disables non-exact forward pruning, reductions (IIR/LMR), singular/check extensions, and mate-window TT cutoffs, applies mate-distance pruning in `qsearch`, and stops iterative deepening only on a positive mate score `>= mate_in(2 * N - 1)`, leaving all `mate_moves == 0` searches (`go depth`, `go nodes`, clock searches) untouched.
2. For positions near the 50-move rule, `qsearch` refuses TT cutoffs when `halfmove_clock() >= 90` (matching `Worker::search`), and both `search` and `qsearch` ignore `tte.move` and `tte.pv()` from TT entries whose `rule50_clock` does not match `board.halfmove_clock()` when `board.halfmove_clock() >= 90`.
3. In `Worker::search`, when `board.halfmove_clock() + depth >= 100` (or `board.halfmove_clock() + new_depth >= 100` for LMR), forward pruning and LMR are skipped so quiet moves that reach the 100-half-move draw horizon cannot be pruned or reduced short of `is_draw` — chosen over folding the clock into the Zobrist key because `bench` positions have low clocks (`0`), keeping all reference node counts bit-identical without fragmenting normal hash-table utilization.

---

## 3. Files Changed and Added

Changed engine files (27 insertions, 14 deletions = 41 changed lines total, well under the 300-line limit):
- `forge-combo29/include/forge/search.hpp`
- `forge-combo29/src/search.cpp`

Added test and report files:
- `forge-combo29/tests_t23/mate_solver_test.cpp`
- `forge-combo29/tests_t23/fifty_move_tt_test.cpp`
- `forge-combo29/REPORT_t23.md`

---

## 4. Commands Run and Full Outputs

### 4.1 Initial Start & Baseline Reference Numbers (Unchanged Base)

Note: `/usr/bin/c++` on this Ubuntu VM pointed to `clang++-18` without `libstdc++-14-dev` installed, while `g++` (GCC 13.3.0 with `libstdc++-13-dev`) is installed and working; `CXX=g++` was therefore passed to CMake. Both the portable build (`-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`) and the native lock build (`x86-64-v4`, since this CPU has AVX-512 and BMI2) produce the exact same reference node counts.

Command:
```bash
CXX=g++ cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
cmake --build build -j
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

Output:
```text
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE
-- Configuring done (0.4s)
-- Generating done (0.0s)
-- Build files have been written to: /agent/repos/dwqww/build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
info string bench depth 11 nodes 312866 time 169 nps 1851278
info string bench depth 13 nodes 862329 time 447 nps 1929147
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

---

### 4.2 Fault A Reproduction on Unchanged Base (Step 2: 15 of 30 Mates Missed)

Command:
```bash
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include forge-combo29/tests_t23/mate_solver_test.cpp /tmp/build-forge/CMakeFiles/forge.dir/src/bitboard.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/board.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/book.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/eval.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/eval_params.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/nnue.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/search.cpp.o -pthread -o /tmp/mate_solver_test && /tmp/mate_solver_test
```

Output (on unchanged base):
```text
OK   [R1_krk_m1] N=1 judge_min=1 move=a7a8 (mates_in=1) uci_mate=1 depth=1 nodes=23
MISS [R2_krk_m2] N=2 judge_min=2 move=c4g4 (mates_in=0) score=483 uci_mate=none depth=3 nodes=141
OK   [R3_krk_b_m2] N=2 judge_min=2 move=g1f2 (mates_in=2) uci_mate=2 depth=3 nodes=87
OK   [R4_krk_m2] N=2 judge_min=2 move=c6c7 (mates_in=2) uci_mate=2 depth=3 nodes=135
MISS [R5_krk_m3] N=3 judge_min=3 move=c3e3 (mates_in=0) score=498 uci_mate=none depth=5 nodes=560
MISS [R6_krk_b_m3] N=3 judge_min=3 move=f6h6 (mates_in=0) score=452 uci_mate=none depth=5 nodes=828
MISS [R7_krkp_m3] N=3 judge_min=3 move=b4a4 (mates_in=3) score=396 uci_mate=none depth=5 nodes=367
OK   [Q1_kqk_m1] N=1 judge_min=1 move=g5h4 (mates_in=1) uci_mate=1 depth=1 nodes=33
MISS [Q2_kqk_m2] N=2 judge_min=2 move=e5h2 (mates_in=0) score=941 uci_mate=none depth=3 nodes=198
MISS [Q3_kqk_m2] N=2 judge_min=2 move=d7c8 (mates_in=0) score=973 uci_mate=none depth=3 nodes=184
OK   [Q4_kqk_b_m2] N=2 judge_min=2 move=g5h6 (mates_in=2) uci_mate=2 depth=3 nodes=151
MISS [Q5_kqk_m3] N=3 judge_min=3 move=g4g2 (mates_in=0) score=950 uci_mate=none depth=5 nodes=914
MISS [Q6_kqk_m3] N=3 judge_min=3 move=b3d5 (mates_in=0) score=920 uci_mate=none depth=5 nodes=967
MISS [Q7_kqk_b_m3] N=3 judge_min=3 move=b4e1 (mates_in=0) score=1118 uci_mate=none depth=5 nodes=639
OK   [B1_kbbk_m1] N=1 judge_min=1 move=g4f3 (mates_in=1) uci_mate=1 depth=1 nodes=27
OK   [B2_kbbk_m2] N=2 judge_min=2 move=g5f4 (mates_in=2) uci_mate=2 depth=3 nodes=115
OK   [B3_kbbk_m2] N=2 judge_min=2 move=h4g3 (mates_in=2) uci_mate=2 depth=3 nodes=105
OK   [B4_kbbk_b_m2] N=2 judge_min=2 move=a5b6 (mates_in=2) uci_mate=2 depth=3 nodes=108
OK   [B5_kbbk_m3] N=3 judge_min=3 move=h4e7 (mates_in=3) uci_mate=3 depth=4 nodes=188
MISS [B6_kbbk_m3] N=3 judge_min=3 move=e6d5 (mates_in=0) score=474 uci_mate=none depth=5 nodes=639
OK   [MG1_m1] N=1 judge_min=1 move=f3f7 (mates_in=1) uci_mate=1 depth=1 nodes=47
OK   [MG2_quiet_m2] N=2 judge_min=2 move=d1d4 (mates_in=2) uci_mate=2 depth=3 nodes=195
MISS [MG3_smoth_m2] N=2 judge_min=2 move=e5c6 (mates_in=0) score=1777 uci_mate=none depth=3 nodes=167
OK   [MG4_opera_m2] N=2 judge_min=2 move=b3b8 (mates_in=2) uci_mate=2 depth=1 nodes=66
MISS [MG5_quiet_m2] N=2 judge_min=2 move=f1e1 (mates_in=0) score=187 uci_mate=none depth=3 nodes=176
MISS [MG6_smoth_m3] N=3 judge_min=3 move=e6c4 (mates_in=0) score=1484 uci_mate=none depth=5 nodes=898
MISS [MG7_anast_m3] N=3 judge_min=3 move=e3h3 (mates_in=0) score=1838 uci_mate=none depth=5 nodes=944
OK   [MG8_sac_m3] N=3 judge_min=3 move=d5f7 (mates_in=3) uci_mate=3 depth=1 nodes=101
OK   [MG9_quiet_m3] N=3 judge_min=3 move=d2d6 (mates_in=3) uci_mate=3 depth=4 nodes=392
MISS [MG10_blk_m3] N=3 judge_min=3 move=e6h6 (mates_in=0) score=1838 uci_mate=none depth=5 nodes=724
OK   [NM1_krk_not1] N=1 (no mate) move=c4c5 score=470 depth=1 nodes=24
OK   [NM2_krk_not2] N=2 (no mate) move=e6e5 score=550 depth=3 nodes=123
OK   [NM3_krk_not3] N=3 (no mate) move=e1d2 score=424 depth=5 nodes=1315
OK   [NM4_kqk_not3] N=3 (no mate) move=a1a2 score=947 depth=5 nodes=2962
OK   [NM5_kbbk_not3] N=3 (no mate) move=d3f1 score=377 depth=5 nodes=835
OK   [NM6_start_not2] N=2 (no mate) move=e2e4 score=18 depth=3 nodes=215
OK   [NM7_kiwi_not3] N=3 (no mate) move=e2a6 score=-170 depth=5 nodes=1880
OK   [NM8_def_not2] N=2 (no mate) move=e5f7 score=1784 depth=3 nodes=180
OK   [NM9_stale_not3] N=3 (no mate) move=c3d3 score=-431 depth=5 nodes=523
OK   [NM10_mid_not3] N=3 (no mate) move=d4c5 score=171 depth=5 nodes=1484
SUMMARY: total=40 mate_positions=30 non_mate_positions=10 missed_mates=15 false_mates=0 illegal=0
```

---

### 4.3 Fault B Reproduction on Unchanged Base (Step 5: 11 of 20 Suite Cases Mismatched)

Command:
```bash
git show origin/integrate/combo29-fixes:forge-combo29/include/forge/search.hpp > /tmp/base_inc/forge/search.hpp
git show origin/integrate/combo29-fixes:forge-combo29/src/search.cpp > /tmp/base_search.cpp
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -I /tmp/base_inc -I forge-combo29/include forge-combo29/tests_t23/fifty_move_tt_test.cpp /tmp/base_search.cpp /tmp/build-forge/CMakeFiles/forge.dir/src/bitboard.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/board.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/book.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/eval.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/eval_params.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/nnue.cpp.o -pthread -o /tmp/fifty_move_tt_base && /tmp/fifty_move_tt_base
```

Output (on unchanged base):
```text
FAIL [C96_KQvK_d3] low=90@d8(930) high=96@d3 | empty=0(d1c1) warm=1002(c2c8) tt_only=1065(c2c8)
OK   [C96_KQvK_d4] low=0@d8(992) high=96@d4 | empty=0(d1c1) warm=0(c2c8) tt_only=0(d1c1)
FAIL [C96_KBNvKp_d4] low=0@d8(247) high=96@d4 | empty=0(b3c2) warm=198(b3c2) tt_only=246(b2a3)
FAIL [C96_KBNvKp_d6] low=0@d8(247) high=96@d6 | empty=0(b3c2) warm=221(b3c2) tt_only=252(c3d5)
FAIL [C96_KBBvKp_d5] low=0@d8(450) high=96@d5 | empty=0(d3c4) warm=367(d3c4) tt_only=367(d3c4)
FAIL [C96_KRBvKp_d4] low=0@d8(651) high=96@d4 | empty=639(b3b4) warm=575(b3b5) tt_only=651(b3b4)
OK   [C96_KRNvKp_d4] low=0@d8(698) high=96@d4 | empty=0(b3b7) warm=0(b2a3) tt_only=0(b3b7)
FAIL [C97_KQvKNp_d3] low=0@d8(610) high=97@d3 | empty=0(c2h2) warm=567(c2h2) tt_only=565(c2h2)
FAIL [C97_KQvKNp_95] low=95@d8(0) high=97@d3 | empty=0(c2h2) warm=0(c2h2) tt_only=521(c2h2)
FAIL [C97_KQvKNp2_d3] low=0@d8(650) high=97@d3 | empty=560(c3f3) warm=0(c3f3) tt_only=0(c3f3)
FAIL [C97_KBBvKp_d5] low=90@d8(431) high=97@d5 | empty=0(d3c4) warm=335(d3c4) tt_only=368(d3c4)
FAIL [C97_KBNvKp_90d5] low=90@d8(250) high=97@d5 | empty=0(b3c2) warm=0(b2a2) tt_only=206(b3c2)
OK   [C97_KRNvP_96d3] low=96@d8(0) high=97@d3 | empty=0(b1c3) warm=0(b1c3) tt_only=0(b1c3)
FAIL [C98_KQNvKNp_d4] low=0@d10(1169) high=98@d4 | empty=0(f5g7) warm=576(c2c7) tt_only=590(c2c7)
OK   [C98_KQvKNp_d4] low=0@d8(610) high=98@d4 | empty=0(c2c8) warm=0(c2c8) tt_only=0(c2c8)
OK   [C98_KRvK_d4] low=0@d8(443) high=98@d4 | empty=0(c2g2) warm=0(c2g2) tt_only=0(c2g2)
OK   [C98_KBNvKp_d4] low=0@d8(247) high=98@d4 | empty=0(c3e4) warm=0(c3e4) tt_only=0(c3e4)
OK   [C99_KRvK_d4] low=0@d8(443) high=99@d4 | empty=0(c2d2) warm=0(c2e2) tt_only=0(c2e2)
OK   [C99_KQvKNp_d4] low=0@d8(610) high=99@d4 | empty=0(c2g2) warm=0(c2g2) tt_only=0(c2g2)
OK   [C99_KQNvKNp_d4] low=0@d8(1184) high=99@d4 | empty=0(c2c6) warm=0(f5d4) tt_only=0(f5d4)
SUMMARY: cases=20 failures=11
```

---

### 4.4 Reference Numbers of Rule 7 After Both Fixes (Portable `x86-64-v3` and Default `x86-64-v4`, plus Full 10-Pin Check)

Command (portable `x86-64-v3` Release build):
```bash
CXX=g++ cmake -S forge-combo29 -B /tmp/build-portable -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
cmake --build /tmp/build-portable -j
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/build-portable/forge
```

Output:
```text
info string bench depth 11 nodes 312866 time 167 nps 1873449
info string bench depth 13 nodes 862329 time 445 nps 1937817
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

Command (default `x86-64-v4` Release build + `scripts/check_pins.sh`):
```bash
CXX=g++ cmake -S forge-combo29 -B /tmp/build-forge -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/build-forge -j
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/build-forge/forge
forge-combo29/scripts/check_pins.sh /tmp/build-forge/forge
```

Output:
```text
info string bench depth 11 nodes 312866 time 159 nps 1967710
info string bench depth 13 nodes 862329 time 424 nps 2033794
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
net-on : 312866 862329 3024920 12389307 34048354
net-off: 375354 907205 2448617 13573040 24506465
perft5 : 4865609
PINS MATCH combo29
```

---

### 4.5 Release Test Runs After Both Fixes (Step 4 & Step 8)

Command:
```bash
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -I forge-combo29/include forge-combo29/tests_t23/mate_solver_test.cpp /tmp/build-forge/CMakeFiles/forge.dir/src/bitboard.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/board.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/book.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/eval.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/eval_params.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/nnue.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/search.cpp.o -pthread -o /tmp/mate_solver_release
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -I forge-combo29/include forge-combo29/tests_t23/fifty_move_tt_test.cpp /tmp/build-forge/CMakeFiles/forge.dir/src/bitboard.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/board.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/book.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/eval.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/eval_params.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/nnue.cpp.o /tmp/build-forge/CMakeFiles/forge.dir/src/search.cpp.o -pthread -o /tmp/fifty_move_tt_release
/tmp/mate_solver_release
/tmp/fifty_move_tt_release
```

Output:
```text
OK   [R1_krk_m1] N=1 judge_min=1 move=a7a8 (mates_in=1) uci_mate=1 depth=1 nodes=23
OK   [R2_krk_m2] N=2 judge_min=2 move=b1c2 (mates_in=2) uci_mate=2 depth=3 nodes=371
OK   [R3_krk_b_m2] N=2 judge_min=2 move=g1f2 (mates_in=2) uci_mate=2 depth=3 nodes=99
OK   [R4_krk_m2] N=2 judge_min=2 move=c6c7 (mates_in=2) uci_mate=2 depth=3 nodes=223
OK   [R5_krk_m3] N=3 judge_min=3 move=c5b6 (mates_in=3) uci_mate=3 depth=5 nodes=9009
OK   [R6_krk_b_m3] N=3 judge_min=3 move=f4g3 (mates_in=3) uci_mate=3 depth=5 nodes=5844
OK   [R7_krkp_m3] N=3 judge_min=3 move=b4a4 (mates_in=3) uci_mate=3 depth=5 nodes=4373
OK   [Q1_kqk_m1] N=1 judge_min=1 move=g5h4 (mates_in=1) uci_mate=1 depth=1 nodes=30
OK   [Q2_kqk_m2] N=2 judge_min=2 move=e5e2 (mates_in=2) uci_mate=2 depth=3 nodes=250
OK   [Q3_kqk_m2] N=2 judge_min=2 move=b5c6 (mates_in=2) uci_mate=2 depth=3 nodes=447
OK   [Q4_kqk_b_m2] N=2 judge_min=2 move=g5h6 (mates_in=2) uci_mate=2 depth=3 nodes=431
OK   [Q5_kqk_m3] N=3 judge_min=3 move=d6e6 (mates_in=3) uci_mate=3 depth=5 nodes=13872
OK   [Q6_kqk_m3] N=3 judge_min=3 move=e6d7 (mates_in=3) uci_mate=3 depth=5 nodes=8628
OK   [Q7_kqk_b_m3] N=3 judge_min=3 move=e2d3 (mates_in=3) uci_mate=3 depth=5 nodes=11122
OK   [B1_kbbk_m1] N=1 judge_min=1 move=g4f3 (mates_in=1) uci_mate=1 depth=1 nodes=27
OK   [B2_kbbk_m2] N=2 judge_min=2 move=g5f4 (mates_in=2) uci_mate=2 depth=3 nodes=159
OK   [B3_kbbk_m2] N=2 judge_min=2 move=h4g3 (mates_in=2) uci_mate=2 depth=3 nodes=141
OK   [B4_kbbk_b_m2] N=2 judge_min=2 move=a5b6 (mates_in=2) uci_mate=2 depth=3 nodes=147
OK   [B5_kbbk_m3] N=3 judge_min=3 move=g4d7 (mates_in=3) uci_mate=3 depth=5 nodes=2326
OK   [B6_kbbk_m3] N=3 judge_min=3 move=c6b6 (mates_in=3) uci_mate=3 depth=5 nodes=7867
OK   [MG1_m1] N=1 judge_min=1 move=f3f7 (mates_in=1) uci_mate=1 depth=1 nodes=49
OK   [MG2_quiet_m2] N=2 judge_min=2 move=d1d4 (mates_in=2) uci_mate=2 depth=3 nodes=340
OK   [MG3_smoth_m2] N=2 judge_min=2 move=d5g8 (mates_in=2) uci_mate=2 depth=3 nodes=557
OK   [MG4_opera_m2] N=2 judge_min=2 move=b3b8 (mates_in=2) uci_mate=2 depth=1 nodes=64
OK   [MG5_quiet_m2] N=2 judge_min=2 move=d3a6 (mates_in=2) uci_mate=2 depth=3 nodes=958
OK   [MG6_smoth_m3] N=3 judge_min=3 move=f7h6 (mates_in=3) uci_mate=3 depth=5 nodes=16949
OK   [MG7_anast_m3] N=3 judge_min=3 move=d5e7 (mates_in=3) uci_mate=3 depth=5 nodes=36214
OK   [MG8_sac_m3] N=3 judge_min=3 move=d5f7 (mates_in=3) uci_mate=3 depth=1 nodes=184
OK   [MG9_quiet_m3] N=3 judge_min=3 move=d2d6 (mates_in=3) uci_mate=3 depth=5 nodes=8058
OK   [MG10_blk_m3] N=3 judge_min=3 move=d4e2 (mates_in=3) uci_mate=3 depth=5 nodes=35258
OK   [NM1_krk_not1] N=1 (no mate) move=c4c5 score=470 depth=1 nodes=24
OK   [NM2_krk_not2] N=2 (no mate) move=b4h4 score=550 depth=3 nodes=595
OK   [NM3_krk_not3] N=3 (no mate) move=a1a5 score=433 depth=5 nodes=7062
OK   [NM4_kqk_not3] N=3 (no mate) move=a1f6 score=1166 depth=5 nodes=13192
OK   [NM5_kbbk_not3] N=3 (no mate) move=e1e2 score=392 depth=5 nodes=12921
OK   [NM6_start_not2] N=2 (no mate) move=g1f3 score=7 depth=3 nodes=746
OK   [NM7_kiwi_not3] N=3 (no mate) move=e2a6 score=-104 depth=5 nodes=94087
OK   [NM8_def_not2] N=2 (no mate) move=e5f7 score=2188 depth=3 nodes=2443
OK   [NM9_stale_not3] N=3 (no mate) move=c3d3 score=-483 depth=5 nodes=1677
OK   [NM10_mid_not3] N=3 (no mate) move=d4c5 score=162 depth=5 nodes=62827
SUMMARY: total=40 mate_positions=30 non_mate_positions=10 missed_mates=0 false_mates=0 illegal=0
OK   [C96_KQvK_d3] low=90@d8(948) high=96@d3 | empty=0(d1c1) warm=0(d1c1) tt_only=0(d1c1)
OK   [C96_KQvK_d4] low=0@d8(992) high=96@d4 | empty=0(d1c1) warm=0(c2c8) tt_only=0(d1c1)
OK   [C96_KBNvKp_d4] low=0@d8(247) high=96@d4 | empty=0(b3c2) warm=0(b3c2) tt_only=0(b3c2)
OK   [C96_KBNvKp_d6] low=0@d8(247) high=96@d6 | empty=0(b3c2) warm=0(b3c2) tt_only=0(b3c2)
OK   [C96_KBBvKp_d5] low=0@d8(450) high=96@d5 | empty=0(b2c2) warm=0(d3c4) tt_only=0(d3e4)
OK   [C96_KRBvKp_d4] low=0@d8(651) high=96@d4 | empty=0(b3b6) warm=0(b3b6) tt_only=0(b3b6)
OK   [C96_KRNvKp_d4] low=0@d8(698) high=96@d4 | empty=0(b3b7) warm=0(b2a3) tt_only=0(b3b7)
OK   [C97_KQvKNp_d3] low=0@d8(610) high=97@d3 | empty=0(c2h2) warm=0(c2c8) tt_only=0(c2h2)
OK   [C97_KQvKNp_95] low=95@d8(0) high=97@d3 | empty=0(c2h2) warm=0(c2h2) tt_only=0(c2h2)
OK   [C97_KQvKNp2_d3] low=0@d8(650) high=97@d3 | empty=0(c3f3) warm=0(c3f3) tt_only=0(c3f3)
OK   [C97_KBBvKp_d5] low=90@d8(433) high=97@d5 | empty=0(d3c4) warm=0(d3c4) tt_only=0(d3c4)
OK   [C97_KBNvKp_90d5] low=90@d8(251) high=97@d5 | empty=0(b3c2) warm=0(b3c2) tt_only=0(b3c2)
OK   [C97_KRNvP_96d3] low=96@d8(0) high=97@d3 | empty=0(b1c3) warm=0(b1c3) tt_only=0(b1c3)
OK   [C98_KQNvKNp_d4] low=0@d10(1169) high=98@d4 | empty=0(c2c8) warm=0(c2c8) tt_only=0(c2c8)
OK   [C98_KQvKNp_d4] low=0@d8(610) high=98@d4 | empty=0(c2c8) warm=0(c2c8) tt_only=0(c2c8)
OK   [C98_KRvK_d4] low=0@d8(443) high=98@d4 | empty=0(c2g2) warm=0(c2g2) tt_only=0(c2g2)
OK   [C98_KBNvKp_d4] low=0@d8(247) high=98@d4 | empty=0(c3e4) warm=0(c3e4) tt_only=0(c3e4)
OK   [C99_KRvK_d4] low=0@d8(443) high=99@d4 | empty=0(c2d2) warm=0(c2d2) tt_only=0(c2d2)
OK   [C99_KQvKNp_d4] low=0@d8(610) high=99@d4 | empty=0(c2g2) warm=0(c2g2) tt_only=0(c2g2)
OK   [C99_KQNvKNp_d4] low=0@d8(1184) high=99@d4 | empty=0(c2c6) warm=0(c2c6) tt_only=0(c2c6)
SUMMARY: cases=20 failures=0
```

---

### 4.6 Sanitizer (`-fsanitize=address,undefined`) Build and Run of All Regression Tests (Step 8)

Command:
```bash
ASAN_FLAGS="-std=c++20 -O3 -g -ffp-contract=off -fno-fast-math -march=x86-64-v4 -fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=all -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -I forge-combo29/include -I forge-combo29/src"
mkdir -p /tmp/build-asan
for src in bitboard board book eval eval_params nnue search; do
  g++ $ASAN_FLAGS -c forge-combo29/src/${src}.cpp -o /tmp/build-asan/${src}.o
done
OBJS="/tmp/build-asan/bitboard.o /tmp/build-asan/board.o /tmp/build-asan/book.o /tmp/build-asan/eval.o /tmp/build-asan/eval_params.o /tmp/build-asan/nnue.o /tmp/build-asan/search.o"
g++ $ASAN_FLAGS forge-combo29/tests_t23/mate_solver_test.cpp $OBJS -pthread -o /tmp/build-asan/mate_solver_test
g++ $ASAN_FLAGS forge-combo29/tests_t23/fifty_move_tt_test.cpp $OBJS -pthread -o /tmp/build-asan/fifty_move_tt_test
g++ $ASAN_FLAGS forge-combo29/tests_t1/bad_capture_overflow.cpp $OBJS -pthread -o /tmp/build-asan/bad_capture_overflow
g++ $ASAN_FLAGS forge-combo29/tests_t3/clock_parse_test.cpp -pthread -o /tmp/build-asan/clock_parse_test
g++ $ASAN_FLAGS forge-combo29/tests_t6/fixed_nodes.cpp $OBJS -pthread -o /tmp/build-asan/fixed_nodes
g++ $ASAN_FLAGS forge-combo29/tests_t8/nnue_convert.cpp -pthread -o /tmp/build-asan/nnue_convert
g++ $ASAN_FLAGS forge-combo29/tests_t8/nnue_file_test.cpp $OBJS -pthread -o /tmp/build-asan/nnue_file_test

ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 /tmp/build-asan/mate_solver_test
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 /tmp/build-asan/fifty_move_tt_test
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 /tmp/build-asan/bad_capture_overflow
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 /tmp/build-asan/clock_parse_test
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 /tmp/build-asan/fixed_nodes
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 /tmp/build-asan/nnue_convert /tmp/build-asan/embedded.nnue
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 /tmp/build-asan/nnue_file_test /tmp/build-asan/embedded.nnue
```

Output (zero sanitizer diagnostics, exit code 0 on all 7 binaries):
```text
OK   [R1_krk_m1] N=1 judge_min=1 move=a7a8 (mates_in=1) uci_mate=1 depth=1 nodes=23
OK   [R2_krk_m2] N=2 judge_min=2 move=b1c2 (mates_in=2) uci_mate=2 depth=3 nodes=371
OK   [R3_krk_b_m2] N=2 judge_min=2 move=g1f2 (mates_in=2) uci_mate=2 depth=3 nodes=99
OK   [R4_krk_m2] N=2 judge_min=2 move=c6c7 (mates_in=2) uci_mate=2 depth=3 nodes=223
OK   [R5_krk_m3] N=3 judge_min=3 move=c5b6 (mates_in=3) uci_mate=3 depth=5 nodes=9009
OK   [R6_krk_b_m3] N=3 judge_min=3 move=f4g3 (mates_in=3) uci_mate=3 depth=5 nodes=5844
OK   [R7_krkp_m3] N=3 judge_min=3 move=b4a4 (mates_in=3) uci_mate=3 depth=5 nodes=4373
OK   [Q1_kqk_m1] N=1 judge_min=1 move=g5h4 (mates_in=1) uci_mate=1 depth=1 nodes=30
OK   [Q2_kqk_m2] N=2 judge_min=2 move=e5e2 (mates_in=2) uci_mate=2 depth=3 nodes=250
OK   [Q3_kqk_m2] N=2 judge_min=2 move=b5c6 (mates_in=2) uci_mate=2 depth=3 nodes=447
OK   [Q4_kqk_b_m2] N=2 judge_min=2 move=g5h6 (mates_in=2) uci_mate=2 depth=3 nodes=431
OK   [Q5_kqk_m3] N=3 judge_min=3 move=d6e6 (mates_in=3) uci_mate=3 depth=5 nodes=13872
OK   [Q6_kqk_m3] N=3 judge_min=3 move=e6d7 (mates_in=3) uci_mate=3 depth=5 nodes=8628
OK   [Q7_kqk_b_m3] N=3 judge_min=3 move=e2d3 (mates_in=3) uci_mate=3 depth=5 nodes=11122
OK   [B1_kbbk_m1] N=1 judge_min=1 move=g4f3 (mates_in=1) uci_mate=1 depth=1 nodes=27
OK   [B2_kbbk_m2] N=2 judge_min=2 move=g5f4 (mates_in=2) uci_mate=2 depth=3 nodes=159
OK   [B3_kbbk_m2] N=2 judge_min=2 move=h4g3 (mates_in=2) uci_mate=2 depth=3 nodes=141
OK   [B4_kbbk_b_m2] N=2 judge_min=2 move=a5b6 (mates_in=2) uci_mate=2 depth=3 nodes=147
OK   [B5_kbbk_m3] N=3 judge_min=3 move=g4d7 (mates_in=3) uci_mate=3 depth=5 nodes=2326
OK   [B6_kbbk_m3] N=3 judge_min=3 move=c6b6 (mates_in=3) uci_mate=3 depth=5 nodes=7867
OK   [MG1_m1] N=1 judge_min=1 move=f3f7 (mates_in=1) uci_mate=1 depth=1 nodes=49
OK   [MG2_quiet_m2] N=2 judge_min=2 move=d1d4 (mates_in=2) uci_mate=2 depth=3 nodes=340
OK   [MG3_smoth_m2] N=2 judge_min=2 move=d5g8 (mates_in=2) uci_mate=2 depth=3 nodes=557
OK   [MG4_opera_m2] N=2 judge_min=2 move=b3b8 (mates_in=2) uci_mate=2 depth=1 nodes=64
OK   [MG5_quiet_m2] N=2 judge_min=2 move=d3a6 (mates_in=2) uci_mate=2 depth=3 nodes=958
OK   [MG6_smoth_m3] N=3 judge_min=3 move=f7h6 (mates_in=3) uci_mate=3 depth=5 nodes=16949
OK   [MG7_anast_m3] N=3 judge_min=3 move=d5e7 (mates_in=3) uci_mate=3 depth=5 nodes=36214
OK   [MG8_sac_m3] N=3 judge_min=3 move=d5f7 (mates_in=3) uci_mate=3 depth=1 nodes=184
OK   [MG9_quiet_m3] N=3 judge_min=3 move=d2d6 (mates_in=3) uci_mate=3 depth=5 nodes=8058
OK   [MG10_blk_m3] N=3 judge_min=3 move=d4e2 (mates_in=3) uci_mate=3 depth=5 nodes=35258
OK   [NM1_krk_not1] N=1 (no mate) move=c4c5 score=470 depth=1 nodes=24
OK   [NM2_krk_not2] N=2 (no mate) move=b4h4 score=550 depth=3 nodes=595
OK   [NM3_krk_not3] N=3 (no mate) move=a1a5 score=433 depth=5 nodes=7062
OK   [NM4_kqk_not3] N=3 (no mate) move=a1f6 score=1166 depth=5 nodes=13192
OK   [NM5_kbbk_not3] N=3 (no mate) move=e1e2 score=392 depth=5 nodes=12921
OK   [NM6_start_not2] N=2 (no mate) move=g1f3 score=7 depth=3 nodes=746
OK   [NM7_kiwi_not3] N=3 (no mate) move=e2a6 score=-104 depth=5 nodes=94087
OK   [NM8_def_not2] N=2 (no mate) move=e5f7 score=2188 depth=3 nodes=2443
OK   [NM9_stale_not3] N=3 (no mate) move=c3d3 score=-483 depth=5 nodes=1677
OK   [NM10_mid_not3] N=3 (no mate) move=d4c5 score=162 depth=5 nodes=62827
SUMMARY: total=40 mate_positions=30 non_mate_positions=10 missed_mates=0 false_mates=0 illegal=0
OK   [C96_KQvK_d3] low=90@d8(948) high=96@d3 | empty=0(d1c1) warm=0(d1c1) tt_only=0(d1c1)
OK   [C96_KQvK_d4] low=0@d8(992) high=96@d4 | empty=0(d1c1) warm=0(c2c8) tt_only=0(d1c1)
OK   [C96_KBNvKp_d4] low=0@d8(247) high=96@d4 | empty=0(b3c2) warm=0(b3c2) tt_only=0(b3c2)
OK   [C96_KBNvKp_d6] low=0@d8(247) high=96@d6 | empty=0(b3c2) warm=0(b3c2) tt_only=0(b3c2)
OK   [C96_KBBvKp_d5] low=0@d8(450) high=96@d5 | empty=0(b2c2) warm=0(d3c4) tt_only=0(d3e4)
OK   [C96_KRBvKp_d4] low=0@d8(651) high=96@d4 | empty=0(b3b6) warm=0(b3b6) tt_only=0(b3b6)
OK   [C96_KRNvKp_d4] low=0@d8(698) high=96@d4 | empty=0(b3b7) warm=0(b2a3) tt_only=0(b3b7)
OK   [C97_KQvKNp_d3] low=0@d8(610) high=97@d3 | empty=0(c2h2) warm=0(c2c8) tt_only=0(c2h2)
OK   [C97_KQvKNp_95] low=95@d8(0) high=97@d3 | empty=0(c2h2) warm=0(c2h2) tt_only=0(c2h2)
OK   [C97_KQvKNp2_d3] low=0@d8(650) high=97@d3 | empty=0(c3f3) warm=0(c3f3) tt_only=0(c3f3)
OK   [C97_KBBvKp_d5] low=90@d8(433) high=97@d5 | empty=0(d3c4) warm=0(d3c4) tt_only=0(d3c4)
OK   [C97_KBNvKp_90d5] low=90@d8(251) high=97@d5 | empty=0(b3c2) warm=0(b3c2) tt_only=0(b3c2)
OK   [C97_KRNvP_96d3] low=96@d8(0) high=97@d3 | empty=0(b1c3) warm=0(b1c3) tt_only=0(b1c3)
OK   [C98_KQNvKNp_d4] low=0@d10(1169) high=98@d4 | empty=0(c2c8) warm=0(c2c8) tt_only=0(c2c8)
OK   [C98_KQvKNp_d4] low=0@d8(610) high=98@d4 | empty=0(c2c8) warm=0(c2c8) tt_only=0(c2c8)
OK   [C98_KRvK_d4] low=0@d8(443) high=98@d4 | empty=0(c2g2) warm=0(c2g2) tt_only=0(c2g2)
OK   [C98_KBNvKp_d4] low=0@d8(247) high=98@d4 | empty=0(c3e4) warm=0(c3e4) tt_only=0(c3e4)
OK   [C99_KRvK_d4] low=0@d8(443) high=99@d4 | empty=0(c2d2) warm=0(c2d2) tt_only=0(c2d2)
OK   [C99_KQvKNp_d4] low=0@d8(610) high=99@d4 | empty=0(c2g2) warm=0(c2g2) tt_only=0(c2g2)
OK   [C99_KQNvKNp_d4] low=0@d8(1184) high=99@d4 | empty=0(c2c6) warm=0(c2c6) tt_only=0(c2c6)
SUMMARY: cases=20 failures=0
in_check 0
losing_captures 68
bestmove d3b1
nodes 176
clock_parse_test passed
fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
depth 1 score 1 move d2d4 nodes 26
depth 2 score 49 move d2d4 nodes 54
depth 3 score 18 move e2e4 nodes 215
span depth 2 nodes 54 -> depth 3 nodes 215
nodes 55 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 75 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 95 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 115 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 135 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 155 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 175 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 195 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
fen 8/8/8/8/4k3/8/3R4/4K3 w - - 0 1
depth 1 score 409 move e1f2 nodes 32
depth 2 score 432 move e1f2 nodes 58
depth 3 score 419 move e1e2 nodes 160
span depth 2 nodes 58 -> depth 3 nodes 160
nodes 59 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 71 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 83 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 95 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 107 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 119 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 131 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 143 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 155 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
PASS fixed-node score and move agree
wrote /tmp/build-asan/embedded.nnue hidden 256
ok load converted net
ok startpos eval matches built-in net
ok kiwipete eval matches built-in net
ok converted file is non-empty
ok load shifted bias
ok shifted bias changes an evaluation
ok empty path restores built-in net
ok restored eval matches built-in net
ok bad magic keeps the current net
ok eval unchanged after bad magic
ok wrong version keeps the current net
ok wrong hidden size keeps the current net
ok truncated file keeps the current net
ok oversized file keeps the current net
ok missing file keeps the current net
ok eval unchanged after rejected files
PASS
```

---

## 5. What Could Not Be Verified

1. **Clang ThinLTO+PGO Windows lock build**: This Linux cloud VM builds with GCC 13.3.0 (`g++`); the Windows Clang ThinLTO+PGO toolchain in `windows_build/` could not be executed here (`clang++` on this VM lacked `libstdc++-14-dev` headers/libs, though GCC 13.3.0 builds both portable `x86-64-v3` and `x86-64-v4` cleanly and matches all 10 published `combo29` bench pins + `perft 5`).
2. **Brute-force mate verification for `N >= 4`**: The brute-force legal-move minimax judge in `tests_t23/mate_solver_test.cpp` verifies `N` up to 3 (`1 <= N <= 3`), as specified; `go mate N` for larger `N` (`N >= 4`) relies on the same unpruned/unreduced search path up to `2*N - 1` plies, which can become exponentially slow in high-branching middlegame positions without a time or node limit.
3. **50-move horizon interactions when `halfmove_clock < 90` at the node**: By design, TT cutoffs remain enabled below `halfmove_clock == 90` and pruning/LMR remain enabled when `halfmove_clock + depth < 100` so low-clock searches and all `bench` node signatures stay bit-identical; searches starting well below clock 90 that reach clock 100 only along deep lines (>10 plies) were not exhaustively tablebase-verified.
