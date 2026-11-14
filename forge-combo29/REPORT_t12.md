# Task t12: Two-Thread KRK Mate Miss — Root Cause and Fix

## 1. Summary of Findings (Candidates Checked in Order)

On the unchanged lock (`origin/lock/combo29-20261110`, `16833ecc03b425586f91f4c8834dea8807bf4c22`), `forge-combo29/tests_t12/krk_mate_test` constructs an exact retrograde KRK tablebase, deterministically selects 40 legal White-to-move KRK positions across forced mates in 5, 6, and 7 moves (9, 11, and 13 plies) where a fresh `Threads 1` search at depth 14 (`Hash 16`, default `UseNNUE true`) proves a mate score and plays a mating move, verifies `0 / 100` misses with `Threads 1`, and then runs each of the 40 positions 10 times with `Threads 2` at depth 14 (fresh hash and worker state per run).

On the unchanged lock, `Threads 2` missed the forced mate in **54 of 400** runs (`no_mate_score=54`, `non_mating_move=24`), while `Threads 1` missed in **0 of 100** runs.

All five candidates `(a)`–`(e)` were checked in order:

- **(a) Torn hash reads/writes (key and data from different positions): Not the cause.**
  `TranspositionTable::ExclusiveLease` is acquired only when `workers_.size() == 1` (`src/search.cpp:1787`). With `Threads >= 2`, `tt_owned_` is `false` on every worker, so every `probe` and `store` acquires `stripes_[index % 1024].mutex` (`lock_stripe`) and copies `TTEntry` by value while holding the mutex. AddressSanitizer and UndefinedBehaviorSanitizer report zero issues. Furthermore, running `Threads 1` with `clear_hash()` only (retaining move-ordering history from the previous position so move ordering shifts without any second thread) reproduces the exact same KRK depth-14 mate miss in `18 / 400` runs (`pos=2` `8/4K3/8/1R6/8/8/7k/8 w - - 0 1` missed `10 / 10`), proving that concurrent memory races are not required.
- **(b) Mate scores stored or read without ply correction: Not the cause.**
  Every TT store site (`src/search.cpp:1040, 1105, 1274, 1485`) passes `score_to_tt(score, ply)` (`score + ply` for `>= MateInMaxPly`, `score - ply` for `<= -MateInMaxPly`), and both TT probe sites (`src/search.cpp:1013, 1159`) decode with `score_from_tt(tte.score, ply)`. `StaticEval` and `corrected_eval` are clamped to `[-MateInMaxPly + 1, MateInMaxPly - 1]`. Logged mate entries on the mating PV round-trip to exact ply-adjusted distances at every ply.
- **(c) A bound stored for a node cut short by `stop` or by a helper's different depth: Not the cause.**
  In both `Worker::search` and `Worker::qsearch`, `aborted_` is checked immediately after every recursive call (`if (aborted_) return 0;`), returning before any `store_tt` / `tt.store` call. Helpers in `Searcher::search` run the exact same `worker_limits` iterative-deepening loop (`depth = 1..max_depth`) with no depth-skew offset, and `shared_.stop` is raised only after Worker 0 finishes depth 14 (`src/search.cpp:1809–1812`).
- **(d) Unsound bounds stored after forward pruning / reductions skipped the mating quiet move, combined with TT bound propagation across threads: Real cause.**
  In `Worker::search`, when facing a bare king (such as KRK), forced mates require quiet waiting/zugzwang king and rook moves that do not give check and do not change material, so quiescence search at leaf nodes cannot see the mate and returns static centipawn evaluations (~`+430..+520 cp`). Inside `Worker::search`:
  1. Shallow move-loop pruning (`src/search.cpp:1321–1345`: late-move pruning `skip_quiets`, futility pruning, history pruning, SEE pruning), pre-loop pruning (`src/search.cpp:1196–1245`: razoring, reverse futility pruning, null-move pruning), and late-move reductions (`src/search.cpp:1407–1422`) skip or heavily reduce late quiet non-checking moves whenever `best_score > -MateInMaxPly`.
  2. Despite skipping legal quiet moves (including the unique mating quiet move) or reducing them so their horizon falls short of the mate, `Worker::search` unconditionally stores `BoundUpper` (on fail-low) or `BoundExact` (on PV nodes) at the node's full nominal `depth` (`src/search.cpp:1482–1488`).
  3. One ply higher, the defending bare king sees all of its moves refuted by only `~+470..+506 cp` (instead of `-Mate`) and stores `BoundLower` (e.g. `score = -477..-506`, `depth = 10..11`) in the shared TT—certifying to any thread probing at `depth <= 11` that Black is *not* getting mated (`tt_score >= beta` for a window around `-488`).
  4. With `Threads 1` on a fresh searcher, deterministic move ordering happens to produce an aspiration/null-window fail-high along the mating root move, triggering a full-depth PV re-search that bypasses the reduced horizon and finds the mate. With `Threads 2`, the helper worker races into interior KRK nodes, writes pruning/reduction-backed centipawn `BoundUpper` / `BoundLower` / `BoundExact` entries into the shared TT, and causes Worker 0's null-window/LMR probes on the mating line to take immediate TT cutoffs (`!pv_node && tt_depth >= depth && tt_bound == BoundLower && tt_score >= beta`) instead of searching the mating subtree to full depth.
  *(Note: simply downgrading `BoundExact`/`BoundUpper` when move-loop pruning skipped moves was also tested directly; it left `46 / 400` misses because LMR and pre-loop pruning still certify centipawn bounds over reduced subtrees without skipping moves in the picker.)*
- **(e) Replacement rule dropping a deep mate entry for a shallow one: Not the cause.**
  Instrumenting every `TranspositionTable::store_body` call across all failing `Threads 2` runs recorded **zero** instances (`MATE_LOST = 0`) where an occupied entry holding `is_mate_score(before.score)` was overwritten by a non-mate score. In the failing runs, neither thread ever proved the mate in the first place because centipawn bounds blocked the mating line before mate discovery; furthermore, changing `store` to strict `depth >= entry->depth` replacement without `BoundExact` override still failed in `58 / 400` runs.

### Logged Entry Before-and-After Evidence

Instrumented trace on `3K4/5k2/6R1/8/8/8/8 w - - 0 1` (exact mate in 6 / 11 plies; `Threads 1` proves `mate 8` / `score = 31985` via `g6c6 f7g8 d8e7 g8g7 e7e8 g7g8 c6c7 g8h8 e8f7 h8h7 c7c5 ...` at depth 11..14):

1. **Interior node `PV#8` (after `1.Rc6 Kg8 2.Ke7 Kg7 3.Ke8 Kg8 4.Rc7 Kh8`, White to move, mate in 4 by `5.Kf7`):**
   At root depth 12, ply 6, `depth = 5`, null window `[506, 507]`, Worker 0 skips quiet moves (`prn=1`) and overwrites the slot with a centipawn `BoundUpper` at `depth = 5`, which Worker 1 then refreshes at root depth 14:
   ```
   STR PV#8 w=0 rd=12 ply=6 d=5 [506,507] pv=0 prn=1
     BEF(move=c7a7 score=498 depth=2 bound=Upper) -> AFT(move=c7a7 score=506 depth=5 bound=Upper)
   STR PV#8 w=1 rd=14 ply=8 d=5 [488,489] pv=0 prn=1
     BEF(move=c7a7 score=449 depth=3 bound=Upper) -> AFT(move=c7a7 score=463 depth=5 bound=Upper)
   ```
2. **Interior node `PV#4` (after `1.Rc6 Kg8 2.Ke7 Kg7`, White to move, mate in 6 by `3.Ke8`):**
   At root depth 14, ply 4, `depth = 6`, null window `[520, 521]`, Worker 1 skips quiet moves (`prn=1`) and overwrites the slot with a centipawn `BoundUpper` at `depth = 6` (instead of `score = 31989` `BoundExact` as in the `Threads 1` run):
   ```
   STR PV#4 w=1 rd=14 ply=4 d=6 [520,521] pv=0 prn=1
     BEF(move=a1a1 score=476 depth=2 bound=Upper) -> AFT(move=a1a1 score=488 depth=6 bound=Upper)
   ```
3. **Propagation to `PV#3` (`2...Kg7` parent) and `PV#1` (after `1.Rc6`, Black to move) and resulting Worker 0 cutoff:**
   Immediately after writing `PV#4`, Worker 1 backs that pruned fail-low up to `PV#3` as a centipawn `BoundLower` for Black (`-488 >= -520` at `depth = 7`), and later writes `BoundLower` (`score = -477`, `depth = 10`) on `PV#1` (`after 1.Rc6`):
   ```
   STR PV#3 w=1 rd=14 ply=3 d=7 [-521,-520] pv=0 prn=0
     BEF(move=g8g7 score=-476 depth=3 bound=Lower) -> AFT(move=g8g7 score=-488 depth=7 bound=Lower)
   STR PV#1 w=1 rd=14 ply=1 d=10 [-478,-477] pv=0 prn=0
     BEF(move=f7g7 score=-477 depth=13 bound=Exact) -> AFT(move=f7g7 score=-477 depth=10 bound=Lower)
   ```
   When Worker 0 searches `PV#1` at root depth 14 (`req_d = 3`, window `[-487, -486]`), it hits Worker 1's `BoundLower` entry (`-477 >= -486`, `tt_depth = 10 >= 3`), takes an immediate TT cutoff without searching `1.Rc6` to full depth, and finishes depth 14 reporting `cp 487` (`g6d6`) instead of `mate 8`:
   ```
   CUT PV#1 w=0 rd=14 ply=5 req_d=3 [-487,-486]
     ENT(move=f7g7 score=-477 depth=10 bound=Lower)
   STR PV#0 w=0 rd=14 ply=0 d=14 [470,506] pv=1 prn=0
     BEF(move=g6a6 score=477 depth=14 bound=Exact) -> AFT(move=g6d6 score=487 depth=14 bound=Exact)
   ```

### Before vs. After Miss Counts (`krk_mate_test`, 40 positions x 10 runs, `Threads 2`, `Hash 16`, depth 14)

- **Before (unchanged lock `16833ecc`):** `54 / 400` misses (`no_mate_score=54`, `non_mating_move=24`); `Threads 1` check: `0 / 100` misses.
- **After (with fix):**
  - Repeat 1: `0 / 400` misses (`no_mate_score=0`, `non_mating_move=0`); `Threads 1` check: `0 / 100` misses.
  - Repeat 2: `0 / 400` misses (`no_mate_score=0`, `non_mating_move=0`); `Threads 1` check: `0 / 100` misses.
  - Repeat 3: `0 / 400` misses (`no_mate_score=0`, `non_mating_move=0`); `Threads 1` check: `0 / 100` misses.

---

## 2. The Change

In `Worker::search` (`forge-combo29/src/search.cpp`), when multiple workers are active (`all_workers_->size() > 1`) and either side is down to a bare king (`occupied(color) == pieces(color, King)`), lossy forward pruning (razoring, reverse futility pruning, null-move pruning, and shallow move-loop pruning) and late-move reductions are skipped so bare-king subtrees do not certify centipawn bounds from skipped or depth-reduced mating quiet moves into the shared transposition table. All helper threads continue to read from and write to the shared transposition table normally, no history or correction tables are cleared per search, thread counts and locking are untouched, and single-thread search is bit-for-bit identical to the lock.

---

## 3. Files Changed and Added

- Modified engine source (19 insertions, 5 deletions; 24 changed lines total, well within the 300-line limit):
  - `forge-combo29/src/search.cpp`
- Added test files and report:
  - `forge-combo29/tests_t12/CMakeLists.txt`
  - `forge-combo29/tests_t12/krk_mate_test.cpp`
  - `forge-combo29/REPORT_t12.md`

---

## 4. Commands Run and Full Outputs

*(Environment note: On this Linux VM, `/usr/bin/c++` defaults to Clang 18 without matching Clang `-lstdc++` link paths, while `g++` 13.3.0 has full `libstdc++-13-dev` support; `CXX=g++ CC=gcc` was therefore passed to CMake. All build directories were placed outside the repository or cleaned before committing so only permitted text source files exist in git.)*

### 4.1 Baseline Start Check (Unchanged Lock `16833ecc`)

Command:
```bash
CXX=g++ CC=gcc cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build build -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
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
-- Configuring done (0.3s)
-- Generating done (0.0s)
-- Build files have been written to: /agent/repos/dwqww/build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
info string bench depth 11 nodes 312866 time 166 nps 1884734
info string bench depth 13 nodes 862329 time 504 nps 1710970
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

### 4.2 Step 2: Test on Unchanged Lock (`16833ecc`)

Command:
```bash
CXX=g++ CC=gcc cmake -S forge-combo29/tests_t12 -B /tmp/build_tests_t12 -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build /tmp/build_tests_t12 -j && /tmp/build_tests_t12/krk_mate_test; echo EXIT:$?
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
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/build_tests_t12
[ 11%] Building CXX object CMakeFiles/krk_mate_test.dir/krk_mate_test.cpp.o
[ 22%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/search.cpp.o
[ 33%] Linking CXX executable krk_mate_test
[100%] Built target krk_mate_test
config positions=40 runs_per_pos=10 threads=2 hash_mb=16 depth=14 use_nnue=true
threads_1_check: 0 / 100 misses
  MISS pos=2 run=0 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 506/b5g5 move_dtm=13
  MISS pos=2 run=1 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 457/b5g5 move_dtm=13
  MISS pos=2 run=2 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 499/b5g5 move_dtm=13
  MISS pos=2 run=3 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 412/b5g5 move_dtm=13
  MISS pos=2 run=4 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 444/b5g5 move_dtm=13
  MISS pos=2 run=5 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 477/e7d6 move_dtm=21
  MISS pos=2 run=6 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 443/b5g5 move_dtm=13
  MISS pos=2 run=7 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 450/b5g5 move_dtm=13
  MISS pos=2 run=8 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 458/b5g5 move_dtm=13
  MISS pos=2 run=9 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 453/b5f5 move_dtm=17
pos 2 (8/4K3/8/1R6/8/8/7k/8 w - - 0 1, dtm=13 plies): 10/10 misses
  MISS pos=5 run=1 fen="8/2K5/8/3R4/8/8/k7/8 w - - 0 1" exact_dtm=13 t1=mate 9/d5b5 got=cp 464/c7c6 move_dtm=17
  MISS pos=5 run=2 fen="8/2K5/8/3R4/8/8/k7/8 w - - 0 1" exact_dtm=13 t1=mate 9/d5b5 got=cp 578/d5b5 move_dtm=13
pos 5 (8/2K5/8/3R4/8/8/k7/8 w - - 0 1, dtm=13 plies): 7/10 misses
pos 6 (8/8/2K5/8/k7/8/1R6/8 w - - 0 1, dtm=13 plies): 4/10 misses
pos 7 (2R5/8/3K4/8/8/8/k7/8 w - - 0 1, dtm=13 plies): 7/10 misses
pos 8 (8/8/8/7K/8/8/7k/2R5 w - - 0 1, dtm=13 plies): 1/10 misses
pos 9 (1k6/8/8/8/3K4/8/6R1/8 w - - 0 1, dtm=13 plies): 1/10 misses
pos 11 (8/8/1R6/8/8/k7/3K4/8 w - - 0 1, dtm=11 plies): 2/10 misses
pos 12 (3K4/5k2/6R1/8/8/8/8/8 w - - 0 1, dtm=11 plies): 3/10 misses
pos 15 (k7/8/8/8/4K3/8/8/7R w - - 0 1, dtm=11 plies): 8/10 misses
pos 17 (8/8/1K6/5R2/8/8/k7/8 w - - 0 1, dtm=11 plies): 3/10 misses
pos 22 (4K3/8/1k6/3R4/8/8/8/8 w - - 0 1, dtm=9 plies): 7/10 misses
pos 28 (R7/8/8/8/8/8/8/3K1k2 w - - 0 1, dtm=9 plies): 1/10 misses
SUMMARY: misses=54 / 400 (no_mate_score=54, non_mating_move=24)
EXIT:1
```

### 4.3 Step 5: Three Repeats of `krk_mate_test` After the Fix

Command:
```bash
rm -rf /tmp/build_tests_t12 && CXX=g++ CC=gcc cmake -S forge-combo29/tests_t12 -B /tmp/build_tests_t12 -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build /tmp/build_tests_t12 -j && echo "=== RUN 1 ===" && /tmp/build_tests_t12/krk_mate_test && echo "=== RUN 2 ===" && /tmp/build_tests_t12/krk_mate_test && echo "=== RUN 3 ===" && /tmp/build_tests_t12/krk_mate_test
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
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/build_tests_t12
[ 11%] Building CXX object CMakeFiles/krk_mate_test.dir/krk_mate_test.cpp.o
[ 22%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/bitboard.cpp.o
[ 33%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/board.cpp.o
[ 44%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/book.cpp.o
[ 55%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/eval.cpp.o
[ 66%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/eval_params.cpp.o
[ 77%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/nnue.cpp.o
[ 88%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/search.cpp.o
[100%] Linking CXX executable krk_mate_test
[100%] Built target krk_mate_test
=== RUN 1 ===
config positions=40 runs_per_pos=10 threads=2 hash_mb=16 depth=14 use_nnue=true
threads_1_check: 0 / 100 misses
SUMMARY: misses=0 / 400 (no_mate_score=0, non_mating_move=0)
=== RUN 2 ===
config positions=40 runs_per_pos=10 threads=2 hash_mb=16 depth=14 use_nnue=true
threads_1_check: 0 / 100 misses
SUMMARY: misses=0 / 400 (no_mate_score=0, non_mating_move=0)
=== RUN 3 ===
config positions=40 runs_per_pos=10 threads=2 hash_mb=16 depth=14 use_nnue=true
threads_1_check: 0 / 100 misses
SUMMARY: misses=0 / 400 (no_mate_score=0, non_mating_move=0)
```

*(In addition, an extra stress run with `clear_hash()` only — retaining worker move-ordering history across runs on the 10 deepest `dtm=13` positions x 30 runs each — also passed with `0 / 300` misses, and the non-portable AVX-512/PEXT `-DFORGE_PORTABLE=OFF -DFORGE_MARCH=x86-64-v4` build also passed with `0 / 400` misses.)*

### 4.4 AddressSanitizer + UndefinedBehaviorSanitizer Run (`-fsanitize=address,undefined`)

Command:
```bash
rm -rf /tmp/build_tests_t12_asan && CXX=g++ CC=gcc cmake -S forge-combo29/tests_t12 -B /tmp/build_tests_t12_asan -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DFORGE_SANITIZE=ON && cmake --build /tmp/build_tests_t12_asan -j && /tmp/build_tests_t12_asan/krk_mate_test; echo EXIT:$?
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
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/build_tests_t12_asan
[ 11%] Building CXX object CMakeFiles/krk_mate_test.dir/krk_mate_test.cpp.o
[ 22%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/board.cpp.o
[ 33%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/book.cpp.o
[ 44%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/search.cpp.o
[ 55%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/eval.cpp.o
[ 66%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/bitboard.cpp.o
[ 77%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/eval_params.cpp.o
[ 88%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/nnue.cpp.o
[100%] Linking CXX executable krk_mate_test
[100%] Built target krk_mate_test
config positions=40 runs_per_pos=10 threads=2 hash_mb=16 depth=14 use_nnue=true
threads_1_check: 0 / 100 misses
SUMMARY: misses=0 / 400 (no_mate_score=0, non_mating_move=0)
EXIT:0
```

### 4.5 Step 6: Rule 7 Single-Thread Reference Numbers After the Fix (Plus Full `check_pins.sh`)

Command (portable `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3` build + full `check_pins.sh`):
```bash
rm -rf /tmp/forge-build && CXX=g++ CC=gcc cmake -S forge-combo29 -B /tmp/forge-build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build /tmp/forge-build -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/forge-build/forge && forge-combo29/scripts/check_pins.sh /tmp/forge-build/forge
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
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/forge-build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
info string bench depth 11 nodes 312866 time 164 nps 1907719
info string bench depth 13 nodes 862329 time 439 nps 1964302
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

Command (default AVX-512/PEXT `-march=x86-64-v4` build):
```bash
CXX=g++ CC=gcc cmake -S forge-combo29 -B /tmp/forge-v4 -DCMAKE_BUILD_TYPE=Release && cmake --build /tmp/forge-v4 -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/forge-v4/forge
```

Output:
```text
info string bench depth 11 nodes 312866 time 159 nps 1967710
info string bench depth 13 nodes 862329 time 423 nps 2038602
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

## 5. Not Verified

- **The exact external 40-position list behind the reported `57 / 400` number:** No external FEN file came with the task; `krk_mate_test.cpp` generates 40 deterministic legal KRK positions via an exact retrograde tablebase and reproduced a comparable `54 / 400` miss rate (`0 / 100` on `Threads 1`) on the unchanged lock, dropping to `0 / 400` across all three post-fix runs and under ASan+UBSan.
- **Single-thread bare-king searches on a stained/warm history state:** Because Rule 7 requires `Threads 1` reference node counts (`bench 11` = 312866, `bench 13` = 862329, and `bench 13` includes rook-endgame FEN #7 `6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1` whose deep subtrees reach bare-king nodes), `bare_king_mode` is active only when `all_workers_->size() > 1`. Extending it to `Threads 1` would alter `bench 13` (to 862604 nodes) and violate Rule 7.
- **Non-bare-king quiet mates (e.g., endgames where the losing side still has pawns or pieces):** `bare_king_mode` applies specifically when one side has only a king (`occupied(color) == pieces(color, King)`).
- **Clang and Windows ThinLTO/PGO builds, ThreadSanitizer, and playing strength / Elo / speed:** On this VM, `/usr/bin/clang++` lacks matching libstdc++ linker paths so GCC 13.3.0 was used; no Elo or speed claims are made.
