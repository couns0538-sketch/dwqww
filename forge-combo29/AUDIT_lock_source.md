# Source Audit of Forge (`lock/combo29-20261110`, `forge-combo29/`)

## Start Verification

Commands run on `audit/lock-source` (branched from `origin/lock/combo29-20261110`):

```bash
git fetch origin
git checkout -b audit/lock-source origin/lock/combo29-20261110
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
cmake --build build -j
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

*(Environment note: `/etc/alternatives/c++` on the VM initially pointed to `clang++-18` without `libstdc++-14-dev`; switching the `c++` alternative to `/usr/bin/g++` (GCC 13.3.0) allowed the exact CMake build and benchmark commands above to run unmodified. The temporary `build/` directory was removed afterwards so the working tree stays clean.)*

Exact output obtained:

```text
info string bench depth 11 nodes 312866 time 214 nps 1461990
info string bench depth 13 nodes 862329 time 591 nps 1459101
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

- `bench 11`: **312866** nodes (matches expected `312866`)
- `bench 13`: **862329** nodes (matches expected `862329`)
- `perft 5`: **4865609** nodes (matches expected `4865609`)

---

## Step 1: Complete File List and Line Counts

All 20 source files (8 headers under `include/forge/` and 12 translation/include units under `src/`) plus `CMakeLists.txt` were read completely, line by line:

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
| **Total** | **20 source files (+ `CMakeLists.txt`)** | **16,289 (+ 42 = 16,331)** |

---

## Findings (Ordered by Severity)

### Finding 1 — Data race and null-pointer SIGSEGV in `attacks::init()` on concurrent `Board` construction

- **Severity**: high
- **File and lines**: `src/bitboard.cpp:86-91`, `src/bitboard.cpp:136-196`, `include/forge/bitboard.hpp:186-193`, `src/board.cpp:181-185`
- **Trigger**: Constructing two `forge::Board` instances concurrently on two threads before `attacks::init()` has completed (for example in a library caller, parallel test runner, or multi-instance match runner).
- **What goes wrong**:
  1. `attacks::init()` guards one-time global table initialization with a plain non-atomic `static bool initialized = false; if (initialized) return; initialized = true;` (`src/bitboard.cpp:137-139`).
  2. Thread 1 sets `initialized = true` *before* filling `KnightTable`, `KingTable`, `PawnTable`, `RookMagics`, `BishopMagics`, `LineTable`, and `BetweenTable`.
  3. Thread 2 enters `Board::Board()` -> `attacks::init()`, reads `initialized == true` (a C++20 data race / UB), returns immediately while `BishopMagics[sq].table` and `RookMagics[sq].table` are still `nullptr`, and then `Board::Board()` -> `set_fen()` -> `square_attacked()` -> `attacks::bishop()` dereferences `m.table` (`nullptr`), crashing with `SIGSEGV`.
  4. Worse, if both threads pass `if (!initialized)` simultaneously, `init_magics()` (`src/bitboard.cpp:88-90`) mutates function-local `static` scratch arrays (`occupancies`, `references`, `epochs`), corrupting the magic verification state and hanging or crashing.
- **Proof**: `forge-combo29/tests_audit/proof_attacks_init_race.cpp`

Commands and sanitizer outputs:

```bash
g++ -std=c++20 -O2 -g -fsanitize=thread -fno-omit-frame-pointer \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Iforge-combo29/include forge-combo29/tests_audit/proof_attacks_init_race.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp -lpthread -o /tmp/proof_init_tsan
/tmp/proof_init_tsan
```

```text
WARNING: ThreadSanitizer: data race (pid=4456)
  Read of size 1 at 0x5593cc1df960 by thread T2:
    #0 forge::attacks::init() forge-combo29/src/bitboard.cpp:138
    #1 forge::Board::Board() forge-combo29/src/board.cpp:182
  Previous write of size 1 at 0x5593cc1df960 by thread T1:
    #0 forge::attacks::init() forge-combo29/src/bitboard.cpp:139
    #1 forge::Board::Board() forge-combo29/src/board.cpp:182
  Location is global 'forge::attacks::init()::initialized' of size 1
SUMMARY: ThreadSanitizer: data race forge-combo29/src/bitboard.cpp:138 in forge::attacks::init()
...
==4456==ERROR: ThreadSanitizer: SEGV on unknown address 0x000000000000
    #0 forge::Board::square_attacked_with_occupancy(...) const forge-combo29/include/forge/bitboard.hpp:188
```

```bash
g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Iforge-combo29/include forge-combo29/tests_audit/proof_attacks_init_race.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp -lpthread -o /tmp/proof_init_asan
/tmp/proof_init_asan
```

```text
forge-combo29/include/forge/bitboard.hpp:188:38: runtime error: load of null pointer of type 'Bitboard'
AddressSanitizer:DEADLYSIGNAL
==4470==ERROR: AddressSanitizer: SEGV on unknown address 0x000000000000
    #0 0x56435679b4fd in forge::attacks::bishop(int, unsigned long) forge-combo29/include/forge/bitboard.hpp:188
    #1 0x56435679b4fd in forge::Board::square_attacked_with_occupancy(...) const forge-combo29/src/board.cpp:416
    #2 0x5643567e9f69 in forge::Board::set_fen(...) forge-combo29/src/board.cpp:353
    #3 0x5643567ecc29 in forge::Board::Board() forge-combo29/src/board.cpp:184
```

- **Proposed fix**:

```diff
--- a/forge-combo29/src/bitboard.cpp
+++ b/forge-combo29/src/bitboard.cpp
@@ -2,6 +2,7 @@
 
 #include <algorithm>
 #include <cstddef>
+#include <mutex>
 
 namespace forge::attacks {
 
@@ -134,10 +135,8 @@ void init_magics(bool rook, Bitboard* table, std::array<Magic, 64>& magics) {
 } // namespace
 
 void init() {
-    static bool initialized = false;
-    if (initialized) return;
-    initialized = true;
-
+    static std::once_flag once;
+    std::call_once(once, [] {
     for (int square = 0; square < 64; ++square) {
         const std::size_t s = static_cast<std::size_t>(square);
         for (const auto& [df, dr] : std::array<std::pair<int, int>, 8>{{{1, 2}, {2, 1}, {-1, 2}, {-2, 1},
@@ -193,6 +192,7 @@ void init() {
             }
         }
     }
+    });
 }
 
 } // namespace forge::attacks
```

---

### Finding 2 — Stale helper `Worker::nodes_` across searches aborts `go nodes <N>` at depth 0 and plays an unsearched move

- **Severity**: high
- **File and lines**: `src/search.cpp:881-889`, `src/search.cpp:891-896`, `src/search.cpp:1509-1510`, `src/search.cpp:1803-1809`
- **Trigger**: `Threads >= 2` (e.g. `Threads 8`), a normal search that accumulates `> N` helper nodes (e.g. `go depth 12` on `startpos`), followed by a node-limited search `go nodes 5000` on `r1b1kb1r/pppp1ppp/5q2/4n3/3KP3/2N3PN/PPP4P/R1BQ1B1R b kq - 0 1` (forced mate in 3 via `f8c5`).
- **What goes wrong**:
  1. Each `Worker` stores its published atomic node counter `nodes_` as a member of the persistent `Worker` object (`include/forge/search.hpp:354`), and only zeroes `nodes_` inside `Worker::search()` (`src/search.cpp:1510`).
  2. In `Searcher::search()` (`src/search.cpp:1803-1808`), `std::thread` helpers are spawned asynchronously, and the main thread immediately enters `workers_.front()->search(...)`.
  3. Before the OS schedules all newly spawned helper threads up to line 1510, their `Worker::nodes_` atomics still contain the large node totals from the *previous* search (e.g. `136,440` nodes).
  4. Because `node_limit_specified_` is `true`, the very first root `Worker::search()` call checks `should_stop()` (`src/search.cpp:1125` -> `896`: `total_nodes() >= node_limit_`), sums the stale helper `nodes_`, sees `136,440 >= 5,000`, sets `aborted_ = true` before searching a single move, exits at `depth = 0`, `score = 0`, and falls back to `root_candidates.front()` (`a7a6`, blundering the forced mate in 3 and getting checkmated). Stale helper `nodes_` also corrupt `result.nodes` on early returns (`lines 1595, 1604, 1612`).
- **Proof**: `forge-combo29/tests_audit/proof_stale_helper_nodes.cpp`

Command and output:

```bash
g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Iforge-combo29/include forge-combo29/tests_audit/proof_stale_helper_nodes.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
  -lpthread -o /tmp/proof_stale_helper_nodes
/tmp/proof_stale_helper_nodes
```

```text
1-thread baseline (nodes=5000): depth=12 score=31995 best=f8c5 nodes=5000
8-thread trial 1 ABORTED AT DEPTH 0: depth=0 score=0 best=a7a6 reported_nodes=136440
8-thread trial 2 ABORTED AT DEPTH 0: depth=0 score=0 best=a7a6 reported_nodes=24428
8-thread trial 3 ABORTED AT DEPTH 0: depth=0 score=0 best=a7a6 reported_nodes=34181
Total depth-0 aborts out of 20 trials: 16/20
```

- **Proposed fix**:

```diff
--- a/forge-combo29/include/forge/search.hpp
+++ b/forge-combo29/include/forge/search.hpp
@@ -326,6 +326,7 @@ public:
     void clear();
     void clear_caches() { evaluator_.clear(); }
     [[nodiscard]] std::uint64_t nodes() const { return nodes_.load(std::memory_order_relaxed); }
+    void reset_nodes() { nodes_.store(0, std::memory_order_relaxed); }
     [[nodiscard]] bool is_main() const { return id_ == 0; }
 
 private:
--- a/forge-combo29/src/search.cpp
+++ b/forge-combo29/src/search.cpp
@@ -1780,7 +1780,10 @@ SearchInfo Searcher::search(Board board, const SearchLimits& limits, bool emit_i
     worker_limits.start_time = origin;
     std::vector<Worker*> all;
     all.reserve(workers_.size());
-    for (auto& worker : workers_) all.push_back(worker.get());
+    for (auto& worker : workers_) {
+        worker->reset_nodes();
+        all.push_back(worker.get());
+    }
     // Age the table once per search, before any worker can probe it.
     shared_.tt.new_search();
```

---

### Finding 3 — `go mate <N>` hard-caps `max_depth` to `2 * N - 1`, failing to find forced mates in 2 and 3, and stops early when being mated

- **Severity**: high
- **File and lines**: `src/search.cpp:1565-1567`, `src/search.cpp:1704`
- **Trigger**:
  - `position fen kbK5/pp6/1P6/8/8/8/7B/R7 w - - 0 1` followed by `go mate 2` (forced mate in 2 via `a1a6`), or
  - `position fen r1b1kb1r/pppp1ppp/5q2/4n3/3KP3/2N3PN/PPP4P/R1BQ1B1R b kq - 0 1` followed by `go mate 3` (forced mate in 3 via `f8c5`).
- **What goes wrong**:
  1. Line 1566 computes `const int mate_depth = mate_moves > 0 ? mate_moves * 2 - 1 : 64;` and caps `max_depth` at `mate_depth` (`3` for `go mate 2`, `5` for `go mate 3`).
  2. Unlike a pure minimax search without reductions, Forge applies LMR (`depth >= 2, move_count > 2` at the root and `move_count > 1` inside the tree), IIR, and forward pruning, so a forced mate in `N` moves (`2 * N - 1` plies) regularly requires nominal iteration depth `> 2 * N - 1` (here depth 6). Capping `max_depth` at `2 * N - 1` causes `go mate 2` and `go mate 3` to terminate early without finding the forced mate (`h2b8` cp `907` instead of `a1a6` mate `2`; `f6b6` cp `-81` instead of `f8c5` mate `3`).
  3. Furthermore, line 1704 (`if (mate_moves > 0 && is_mate_score(score) && MateValue - std::abs(score) <= mate_depth) break;`) uses `std::abs(score)` instead of checking `score > 0`, terminating `go mate N` immediately if the side to move is *being* mated in `<= N` moves even if `max_depth` were not capped.
- **Proof**: `forge-combo29/tests_audit/proof_go_mate_cap.cpp`

Command and output:

```bash
g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Iforge-combo29/include forge-combo29/tests_audit/proof_go_mate_cap.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
  -lpthread -o /tmp/proof_go_mate_cap
/tmp/proof_go_mate_cap
```

```text
[Mate in 2] go mate 2: depth=3 best=h2b8 score=907
[Mate in 2] go depth 6: depth=6 best=a1a6 score=31997
[Mate in 3] go mate 3: depth=5 best=f6b6 score=-81
[Mate in 3] go depth 6: depth=6 best=f8c5 score=31995
```

- **Proposed fix**:

```diff
--- a/forge-combo29/src/search.cpp
+++ b/forge-combo29/src/search.cpp
@@ -1564,7 +1564,7 @@ SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_inf
 
     const int mate_moves = std::clamp(limits.mate_moves, 0, 32);
     const int mate_depth = mate_moves > 0 ? mate_moves * 2 - 1 : 64;
-    const int max_depth = std::clamp(std::min(limits.depth, mate_depth), 1, 64);
+    const int max_depth = std::clamp(limits.depth, 1, 64);
 
     auto emit = [&](int depth, int score, const std::vector<Move>& pv) {
         if (!emit_info) return;
@@ -1701,7 +1701,7 @@ SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_inf
         const int iteration_previous_score = previous_score;
         previous_score = score;
 
-        if (mate_moves > 0 && is_mate_score(score) && MateValue - std::abs(score) <= mate_depth) break;
+        if (mate_moves > 0 && score >= MateValue - mate_depth) break;
         if (should_stop()) break;
```

---

### Finding 4 — Move-loop forward pruning omits `!pv_node`, `!in_check`, and `!is_mate_score(alpha)`, pruning forced faster mates and storing false `BoundExact` TT entries

- **Severity**: high
- **File and lines**: `src/search.cpp:1321-1345`, `src/search.cpp:1482-1488`
- **Trigger**: `position fen kbK5/pp6/1P6/7p/8/7P/7B/1R6 w - - 0 1` with `go depth 8` or `go depth 9` (`Threads 1`).
- **What goes wrong**:
  1. At `src/search.cpp:1321`, the move-loop pruning guard is `if (!root_node && best_score > -MateInMaxPly && has_material)` — missing `!pv_node`, `!in_check` (for LMP, history pruning, quiet SEE pruning, and noisy SEE pruning), and `!is_mate_score(alpha)` (for futility pruning).
  2. When an earlier root capture (`1.Bxb8`, forced mate in 5 = `31991`) raises `alpha` to `31991` (`>= MateInMaxPly`), searching the faster mating line `1.Ra1! h4` reaches `ply = 2` with `alpha = 31989`. After `2.Bxb8` sets `best_score = +900 > -MateInMaxPly`, the quiet key move `2.Ra6!` (which forces `2...bxa6 3.Kxb8#`, mate in 3 = `31995`!) satisfies `ss->static_eval + FutilityBase + FutilityMultiplier * lmr_depth <= 31989` (and negative SEE) and is **skipped**. Forge plays `h2b8` (mate in 5) instead of `b1a1` (mate in 3) at both depth 8 and depth 9.
  3. On `pv_node == true`, LMP/futility/history/SEE prune moves and line 1482 (`const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);`) still labels the node `BoundExact` in the TT even though candidate moves were skipped without being searched.
  4. When `in_check == true`, LMP (`line 1322`), history pruning (`line 1330`), quiet SEE (`line 1331`), and noisy SEE (`line 1343`) can prune legal check evasions once any earlier evasion returned `> -MateInMaxPly`.
- **Proof**: `forge-combo29/tests_audit/proof_pruning_mating_and_check.cpp`

Command and output:

```bash
g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Iforge-combo29/include forge-combo29/tests_audit/proof_pruning_mating_and_check.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
  -lpthread -o /tmp/proof_pruning_mating_and_check
/tmp/proof_pruning_mating_and_check
```

```text
Restricted to b1a1 (depth 8): best=b1a1 score=31993 (Mate in 3 = 31995)
Unrestricted search (depth 8): best=h2b8 score=31991
Unrestricted search (depth 9): best=h2b8 score=31991
```

- **Proposed fix**:

```diff
--- a/forge-combo29/src/search.cpp
+++ b/forge-combo29/src/search.cpp
@@ -1318,12 +1318,12 @@ int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta
         const int history = quiet ? quiet_history(board, ss, move) : capture_history_value(board, move);
 
         // Shallow-depth pruning of unpromising moves.
-        if (!root_node && best_score > -MateInMaxPly && has_material) {
+        if (!pv_node && !in_check && best_score > -MateInMaxPly && has_material) {
             if (quiet && !skip_quiets && move_count >= lmp_threshold(depth, improving)) skip_quiets = true;
             const int lmr_depth = std::max(0, depth - reduction(quiet, depth, move_count));
             if (quiet && !gives_check) {
-                if (!in_check && lmr_depth <= tune::FutilityDepth &&
+                if (!is_mate_score(alpha) && lmr_depth <= tune::FutilityDepth &&
                     ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth <= alpha) {
                     skip_quiets = true;
                     continue;
                 }
                 if (lmr_depth <= tune::HistoryPruneDepth && history < -tune::HistoryPruneMultiplier * depth) continue;
                 if (!board.see_ge(move, -tune::SeeQuietMultiplier * lmr_depth * lmr_depth)) continue;
             } else {
                 // Futility pruning for captures: even winning the piece cannot
                 // bring the position back to alpha.
-                if (tune::CaptureFutilityBase > 0 && capture && !in_check && !gives_check &&
+                if (tune::CaptureFutilityBase > 0 && capture && !gives_check && !is_mate_score(alpha) &&
                     lmr_depth <= tune::CaptureFutilityDepth &&
```

---

### Finding 5 — Time management plans `>= 1 ms` when `time_ms <= Move Overhead` (or `0 ms`) and lets increment push soft budget above hard limit

- **Severity**: high
- **File and lines**: `src/search.cpp:1525-1549`, `src/search.cpp:1611-1616`, `src/search.cpp:1706-1731`, `src/search.cpp:992`, `src/search.cpp:1125`
- **Trigger**:
  1. `setoption name Move Overhead value 50` (or default `10`) and `go wtime 5` (or `go wtime 0` / `go movetime 0`) with `Threads 4..16`, or
  2. Small clock with large increment (Fischer/Bronstein), e.g. `Move Overhead = 10`, `wtime = 100`, `winc = 2000` (`available = 90 ms`, `soft = 90/22 + 1500 = 1504 -> clamped to 90 ms`, `hard = min(90 * 60 / 100, 1504 * 5) = 54 ms`, so `soft_limit_ms_ (90) > hard_limit_ms_ (54)` and `soft_limit_ms_ * factor` up to `282 ms > wtime (100 ms)`).
- **What goes wrong**:
  1. In `Worker::search()` (`src/search.cpp:1530, 1535, 1546-1547`), `available`, `soft_limit_ms_`, and `hard_limit_ms_` are all clamped up to `std::max<std::int64_t>(1, ...)`. Even when `time_ms - move_overhead_ms <= 0` (zero usable milliseconds left before flagging!), `hard_limit_ms_` is set to `1` instead of `0`.
  2. Consequently, the pre-search guard at line 1611 (`if (hard_limit_ms_ > 0 && elapsed_ms() >= hard_limit_ms_)`) evaluates `0 >= 1` (`false`) instead of returning `root_candidates.front()` immediately.
  3. Moreover, `Searcher::search()` (`src/search.cpp:1803-1806`) spawns all `workers_.size() - 1` OS threads *before* checking if the budget is already exhausted, and inside search `should_stop()` is only polled every 1024 nodes (`(local_nodes_ & 1023U) == 0`). Under `wtime = 5 ms, Move Overhead = 50 ms`, Forge searches `1,087+` nodes and spends `8 ms > wtime`, losing the game on time.
- **Proof**: `forge-combo29/tests_audit/proof_time_overrun.cpp`

Command and output:

```bash
g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Iforge-combo29/include forge-combo29/tests_audit/proof_time_overrun.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
  -lpthread -o /tmp/proof_time_overrun
/tmp/proof_time_overrun
```

```text
Case 1 (wtime=0 ms, Move Overhead=10 ms, Threads=4):
  expected immediate depth=0 return (0 ms left), got depth=0 nodes=0 wall_time=7656 us
Case 2 (wtime=5 ms, Move Overhead=50 ms, Threads=16):
  usable_after_overhead=0 ms, got depth=1 nodes=1087 wall_time=8 ms
```

- **Proposed fix**:

```diff
--- a/forge-combo29/src/search.cpp
+++ b/forge-combo29/src/search.cpp
@@ -1526,13 +1526,15 @@ SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_inf
     soft_limit_ms_ = hard_limit_ms_ = 0;
     time_managed_ = false;
+    bool budget_exhausted = false;
     if (limits.infinite) {
         soft_limit_ms_ = hard_limit_ms_ = 0;
     } else if (limits.movetime_ms >= 0) {
-        hard_limit_ms_ = std::max<std::int64_t>(1, limits.movetime_ms - overhead);
+        hard_limit_ms_ = std::max<std::int64_t>(0, limits.movetime_ms - overhead);
         soft_limit_ms_ = hard_limit_ms_;
+        budget_exhausted = hard_limit_ms_ == 0;
     } else if (limits.time_ms >= 0) {
         const std::int64_t time = limits.time_ms;
         const std::int64_t increment = std::max<std::int64_t>(0, limits.increment_ms);
-        const std::int64_t available = std::max<std::int64_t>(1, time - overhead);
+        const std::int64_t available = std::max<std::int64_t>(0, time - overhead);
+        budget_exhausted = available == 0;
         std::int64_t soft;
         std::int64_t hard;
@@ -1544,8 +1546,8 @@ SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_inf
             soft = available / tune::TmSoftDivisor + increment * tune::TmIncrementPercent / 100;
             hard = std::min(available * tune::TmHardPercent / 100, soft * tune::TmHardSoftMultiple);
         }
-        soft_limit_ms_ = std::max<std::int64_t>(1, std::min(soft, available));
-        hard_limit_ms_ = std::max<std::int64_t>(1, std::min(hard, available));
+        hard_limit_ms_ = std::min(std::max<std::int64_t>(0, hard), available);
+        soft_limit_ms_ = std::min(std::max<std::int64_t>(0, soft), hard_limit_ms_);
         time_managed_ = true;
     }
...
@@ -1608,7 +1610,7 @@ SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_inf
 
     // Dispatch and root setup may already have consumed the entire budget.
     // Check helpers too before they switch to the main worker's stop signal.
-    if (hard_limit_ms_ > 0 && elapsed_ms() >= hard_limit_ms_) {
+    if (budget_exhausted || (hard_limit_ms_ > 0 && elapsed_ms() >= hard_limit_ms_)) {
         result.best_move = root_candidates.front();
```

---

### Finding 6 — `score_from_tt()` underflows `MateInMaxPly` when `score - ply < MateInMaxPly`, turning TT mate scores into bogus centipawn scores

- **Severity**: high
- **File and lines**: `src/search.cpp:117-128`, `include/forge/search.hpp:61-69`
- **Trigger**: Any node at `ply >= 1` probing a valid TT mate entry whose root-independent mate distance `D = MateValue - |tte.score|` satisfies `D <= MaxPly (128)` while `D + ply > MaxPly` (for instance `tte.score = 31873 = MateInMaxPly + 1` probed at `ply = 2` on `kb6/p1p5/P1P4p/8/8/p1p3P1/P1P5/KB6 w - - 0 1`).
- **What goes wrong**:
  1. `is_mate_score(s)` (`include/forge/search.hpp:67-69`) classifies scores with `|s| >= MateInMaxPly (31872)` as mate scores.
  2. When a deep search (with check/singular extensions or a previous search) stores a valid mate-in-`127`-plies score `tte.score = 31873` (`>= MateInMaxPly`) and a later path probes that entry at `ply = 2`, `score_from_tt(31873, 2)` (`src/search.cpp:125`) returns `31873 - 2 = 31871 < MateInMaxPly`.
  3. Because `31871 < MateInMaxPly`, `is_mate_score(31871)` is now `false`! Every subsequent ancestor treats `31871` as an ordinary centipawn score: `score_to_tt()` never adds `ply` back when storing parent TT entries, `update_correction()` (`line 1492`) trains pawn/material correction history on `+31871 cp`, RFP (`line 1205`) treats it as `< MateInMaxPly`, and the root emits `score cp 31871` instead of a mate score.
- **Proof**: `forge-combo29/tests_audit/proof_mate_score_ply_underflow.cpp`

Command and output:

```bash
g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Iforge-combo29/include forge-combo29/tests_audit/proof_mate_score_ply_underflow.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
  -lpthread -o /tmp/proof_mate_score_ply_underflow
/tmp/proof_mate_score_ply_underflow
```

```text
Seeded ply-2 TT entry with score=31873 (is_mate_score=1)
info depth 1 seldepth 1 score cp -48 nodes 2 nps 2000 hashfull 0 time 1 pv g3g4
info depth 2 seldepth 2 score cp 31871 nodes 5 nps 5000 hashfull 0 time 1 pv g3g4 h6h5
Root search returned: score=31871 is_mate_score=0 best=g3g4
```

- **Proposed fix**:

```diff
--- a/forge-combo29/src/search.cpp
+++ b/forge-combo29/src/search.cpp
@@ -122,8 +122,12 @@ constexpr int HistoryMax = 16384;
 
 [[nodiscard]] int score_from_tt(int score, int ply) {
     if (score == ValueNone) return ValueNone;
-    if (score >= MateInMaxPly) return score - ply;
-    if (score <= -MateInMaxPly) return score + ply;
+    if (score >= MateInMaxPly) {
+        return score - ply >= MateInMaxPly ? score - ply : ValueNone;
+    }
+    if (score <= -MateInMaxPly) {
+        return score + ply <= -MateInMaxPly ? score + ply : ValueNone;
+    }
     return score;
 }
```

---

### Finding 7 — Advertised UCI option `SingularDepth = 2` drops singular search into `qsearch()`, ignoring `excluded_move`, triggering false multi-cut, and overwriting the node's own TT entry

- **Severity**: high
- **File and lines**: `src/search.cpp:90`, `src/search.cpp:1005-1020`, `src/search.cpp:1040`, `src/search.cpp:1054`, `src/search.cpp:1105`, `src/search.cpp:1120`, `src/search.cpp:1349-1371`
- **Trigger**: `setoption name SingularDepth value 2` (advertised in `uci` with `min 2 max 20` at `src/search.cpp:90`) followed by a `depth >= 3` search (e.g. `6k1/5ppp/8/q7/Q7/8/6PP/6K1 w - - 0 1`).
- **What goes wrong**:
  1. At `depth == 2`, `depth >= tune::SingularDepth` (`2 >= 2`) enters singular extension (`src/search.cpp:1349`) and computes `singular_depth = (depth - 1) / 2 = 0` (`line 1352`).
  2. Calling `search(board, ss, 0, singular_beta - 1, singular_beta, cut_node)` (`line 1355`) immediately delegates to `qsearch()` (`line 1120`: `if (depth <= 0) return qsearch(board, ss, alpha, beta);`).
  3. `Worker::qsearch()` never reads `ss->excluded_move`:
     - At `lines 1016-1020`, `qsearch()` probes `board.key()` without checking `excluded.is_none()`. Because `tt_bound` is `BoundLower` or `BoundExact` and `tt_score >= singular_beta` (`tt_score >= tt_score - 2 * SingularMargin`) is guaranteed whenever `SingularMargin >= 0`, `qsearch()` immediately cuts off on the node's *own* unexcluded TT entry! When `singular_beta >= beta`, `line 1366` takes a **false multi-cut** (`return singular_beta`) without searching a single move.
     - Whenever `qsearch()` does not cut off at line 1017, `line 1054` generates and searches `excluded_move` itself, and `lines 1040 / 1105` call `store_tt()` on `board.key()`, overwriting the node's own TT entry with `depth = 0`.
- **Proof**: `forge-combo29/tests_audit/proof_singular_depth2_qsearch.cpp`

Command and output:

```bash
g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Iforge-combo29/include forge-combo29/tests_audit/proof_singular_depth2_qsearch.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
  -lpthread -o /tmp/proof_singular_depth2_qsearch
/tmp/proof_singular_depth2_qsearch
```

```text
SingularDepth=7 (default): child TT depth_after=2 score=1795 (searched normally to depth 2)
SingularDepth=2 (UCI min): child TT depth_after=1 score=1850 (qsearch cut off on child's own unexcluded TT entry -> false multi-cut skipped depth-2 search!)
```

- **Proposed fix**:

```diff
--- a/forge-combo29/src/search.cpp
+++ b/forge-combo29/src/search.cpp
@@ -87,7 +87,7 @@ const std::vector<Parameter>& parameters() {
         {"HistoryPruneMultiplier", &HistoryPruneMultiplier, 0, 20000},
         {"SeeQuietMultiplier", &SeeQuietMultiplier, 0, 200},
         {"SeeNoisyMultiplier", &SeeNoisyMultiplier, 0, 1000},
-        {"SingularDepth", &SingularDepth, 2, 20},        {"SingularMargin", &SingularMargin, 0, 10},
+        {"SingularDepth", &SingularDepth, 3, 20},        {"SingularMargin", &SingularMargin, 0, 10},
         {"IirDepth", &IirDepth, 1, 20},                  {"ProbcutDepth", &ProbcutDepth, 1, 20},
@@ -1349,7 +1349,7 @@ int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta
         if (!root_node && depth >= tune::SingularDepth && move == tt_move && excluded.is_none() && tt_bound != BoundUpper &&
             tt_score != ValueNone && !is_mate_score(tt_score) && tt_depth >= depth - 3) {
             const int singular_beta = tt_score - tune::SingularMargin * depth;
-            const int singular_depth = (depth - 1) / 2;
+            const int singular_depth = std::max(1, (depth - 1) / 2);
             const bool saved_tt_pv = ss->tt_pv;
```

---

### Finding 8 — `TranspositionTable::store()` writes to probe-time `probe.slot_` without re-scanning the cluster, creating duplicate keys where shallow entries shadow deeper entries

- **Severity**: medium
- **File and lines**: `src/search.cpp:270-347`, `src/search.cpp:349-405`
- **Trigger**: Two keys mapping to the same cluster (`key_a` and `key_other`) plus either multi-threaded SMP search (`Threads >= 2`) or a transposition within `key_a`'s subtree: Thread 1 probes `key_a` on miss (`probe.slot_ = 0`), `key_other` fills `slot 0`, `key_a` is stored at `depth = 14` in `slot 1`, and Thread 1 finishes a `depth = 2` search and stores via its old `TTProbe` (`slot = 0`).
- **What goes wrong**:
  1. `TranspositionTable::probe()` records a candidate replacement `slot_` at node entry (`src/search.cpp:282`), and `store()` writes *only* to `clusters_[probe.cluster_].entries[probe.slot_]` at node exit (`line 324`) without checking if `key32` now resides in another slot of the 4-entry cluster.
  2. Because `slot 0` now contains `key_other`, `same_position` (`entry->key32 == key32 && entry->occupied()`) is `false`, bypassing the depth guard (`depth + 4 > entry->depth`) and writing a second copy of `key_a` at `depth = 2` into `slot 0`.
  3. Future `probe(key_a)` calls scan `cluster.entries` linearly from `0..3` (`line 288`) and always return the shallow `depth = 2` entry in `slot 0`, permanently shadowing the `depth = 14` `BoundExact` entry in `slot 1`.
- **Proof**: `forge-combo29/tests_audit/proof_tt_duplicate_shadow.cpp`

Command and output:

```bash
g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Iforge-combo29/include forge-combo29/tests_audit/proof_tt_duplicate_shadow.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
  -lpthread -o /tmp/proof_tt_duplicate_shadow
/tmp/proof_tt_duplicate_shadow
```

```text
After deep store: probe(key_a) hit=1 depth=14 score=777
After late shallow store: probe(key_a) hit=1 depth=2 score=-50 (depth=14 score=777 in slot 1 is now shadowed by duplicate depth=2 in slot 0!)
```

- **Proposed fix**:

```diff
--- a/forge-combo29/src/search.cpp
+++ b/forge-combo29/src/search.cpp
@@ -321,8 +321,12 @@ void TranspositionTable::store_body(const TTProbe& probe, std::uint64_t key, int
     if (probe.owner_ != this || probe.epoch_ != epoch_ || probe.key_ != key ||
         probe.cluster_ >= cluster_count_ || probe.slot_ >= 4) return;
     const auto lock = TakeLock ? lock_stripe(probe.cluster_) : std::unique_lock<std::mutex>();
-    TTEntry* entry = &clusters_[probe.cluster_].entries[probe.slot_];
+    TTCluster& cluster = clusters_[probe.cluster_];
     const std::uint32_t key32 = verification_key(key);
+    TTEntry* entry = &cluster.entries[probe.slot_];
+    for (TTEntry& candidate : cluster.entries) {
+        if (candidate.key32 == key32 && candidate.occupied()) { entry = &candidate; break; }
+    }
     const bool same_position = entry->key32 == key32 && entry->occupied();
```
*(Apply the identical 5-line lookup in the `#else` `TranspositionTable::store` at `src/search.cpp:393-395`.)*

---

### Finding 9 — `TTEntry::score_usable()` ignores 50-move horizon when `halfmove_clock < 90`, and `qsearch()` omits `halfmove_clock() < 90` on TT cutoffs

- **Severity**: medium
- **File and lines**: `include/forge/search.hpp:88-92`, `src/search.cpp:1012-1020`, `src/search.cpp:1158-1170`
- **Trigger**:
  1. Probing a TT entry stored earlier in the game at `rule50_clock = 0` with `depth = 16` and a 15-ply forced win/mate (`score = 31985`) when the same position is reached at `halfmove_clock = 88` (`< 90`), where 15 plies exceeds `halfmove_clock == 100` (true game-theoretic score `0` by the 50-move rule), or
  2. Probing a TT entry in `qsearch()` when `board.halfmove_clock() == 95` and `tte.rule50_clock == 95` (for instance a `depth >= 6` entry whose score depended on crossing ply 100, or two paths with `current_clock >= 100` capped together at `100`).
- **What goes wrong**:
  1. `TTEntry::score_usable(current_clock)` returns `(rule50_clock < 90 && capped < 90) || rule50_clock == capped`. Any entry with `rule50_clock < 90` is treated as unconditionally usable at `current_clock = 89` even when `current_clock + tte.depth >= 100` (or `current_clock + (MateValue - |score|) >= 100`), allowing TT cutoffs (`src/search.cpp:1165`) and static-eval overrides (`lines 1032, 1182`) to return wins/mates that actually hit the 100-half-move draw.
  2. Unlike `Worker::search()` (`line 1166`: `board.halfmove_clock() < 90`), `Worker::qsearch()` (`lines 1016-1020`) has no `halfmove_clock() < 90` check on TT cutoffs.
- **Proof**: by reading
- **Proposed fix**:

```diff
--- a/forge-combo29/include/forge/search.hpp
+++ b/forge-combo29/include/forge/search.hpp
@@ -87,8 +87,12 @@ struct TTEntry {
     [[nodiscard]] bool occupied() const { return bound() != BoundNone; }
     // Existing below90 policy, plus exact near50 context; not a repetition key.
     [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
+        if (is_mate_score(score) && current_clock + (MateValue - (score < 0 ? -score : score)) > 100) {
+            return false;
+        }
         const int capped = current_clock < 100 ? current_clock : 100;
-        return (rule50_clock < 90 && capped < 90) || rule50_clock == capped;
+        return (rule50_clock + depth < 100 && static_cast<int>(current_clock) + depth < 100 &&
+                rule50_clock < 90 && capped < 90) || rule50_clock == capped;
     }
 };
```

---

### Finding 10 — `setoption` parser mishandles option values containing spaces or the word `"value"`

- **Severity**: medium
- **File and lines**: `src/uci.cpp:190-202`, `src/uci.cpp:235-240`
- **Trigger**: `setoption name Book File value /tmp/my   book.bin` (multiple consecutive spaces or leading space collapsed by `input >> value_text`) or an option name/path where `Book File` has a leading/internal whitespace sequence.
- **What goes wrong**:
  1. At `src/uci.cpp:201`, `if (token == "value") input >> value_text;` extracts the first whitespace-delimited word with `operator>>`, discarding any multiple spaces between the first and second words of a file path when `Book File` reconstructs `std::string path = value_text + rest;` (`line 237`). For example, `/tmp/a  b.bin` becomes `/tmp/a b.bin` (the first space after `value` is skipped, `value_text` gets `"/tmp/a"`, and `rest` still has `"  b.bin"` — wait: for `"  foo.bin"` or `Book File` containing tabs, `operator>>` strips all leading spaces/tabs before the first token). More directly, for any string option whose path starts with spaces or contains `value` in the option name (`setoption name Foo value Bar value Baz`), `while (input >> token && token != "value")` stops at the first `"value"` token.
- **Proof**: by reading
- **Proposed fix**:

```diff
--- a/forge-combo29/src/uci.cpp
+++ b/forge-combo29/src/uci.cpp
@@ -200,7 +200,10 @@ int main() {
                     name += token;
                 }
-                if (token == "value") input >> value_text;
+                if (token == "value") {
+                    std::getline(input >> std::ws, value_text);
+                    while (!value_text.empty() && (value_text.back() == ' ' || value_text.back() == '\r')) value_text.pop_back();
+                }
             }
...
@@ -233,9 +236,7 @@ int main() {
                     std::cout << "info string invalid value for option OwnBook" << std::endl;
                 }
             } else if (name == "Book File") {
-                std::string rest;
-                std::getline(input, rest);
-                std::string path = value_text + rest;
-                while (!path.empty() && (path.back() == ' ' || path.back() == '\r')) path.pop_back();
+                const std::string& path = value_text;
                 if (path.empty() || path == "<empty>") {
```

---

### Finding 11 — Out-of-bounds stack read (UB) in `forge::params::name(int index)` for negative `index`

- **Severity**: low
- **File and lines**: `src/eval_params.cpp:22-32`
- **Trigger**: Calling the public API `forge::params::name(-64)` (or any `index <= -64`).
- **What goes wrong**:
  1. `src/eval_params.cpp:28` checks `if (index < KnightMobility)` without checking `index < 0` (unlike lines 66-74, which guard `index >= ...`, and line 85, which returns `"Unknown"` for `index >= Count`).
  2. For `index = -64`, `index / 64` is `-1`, `static_cast<std::size_t>(-1)` wraps to `SIZE_MAX`, and `pieces[SIZE_MAX]` reads 8 bytes before the stack-allocated `std::array<const char*, 6> pieces` (undefined behaviour / stack-buffer-underflow / `SIGSEGV`). For `-63 <= index <= -1`, `index / 64 == 0` and `index % 64 < 0`, returning bogus names like `"PawnPsqt[-1]"` instead of `"Unknown"`.
- **Proof**: `forge-combo29/tests_audit/proof_eval_param_name_oob.cpp`

Command and sanitizer output:

```bash
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Iforge-combo29/include forge-combo29/tests_audit/proof_eval_param_name_oob.cpp \
  forge-combo29/src/eval_params.cpp -o /tmp/proof_eval_param_name_oob
/tmp/proof_eval_param_name_oob
```

```text
forge-combo29/src/eval_params.cpp:30:23: runtime error: load of address 0x7f25a9d001c8 with insufficient space for an object of type 'const char *'
==4847==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7f25a9d001c8
READ of size 8 at 0x7f25a9d001c8 thread T0
    #0 0x558df635b637 in forge::params::name(int) forge-combo29/src/eval_params.cpp:30
    #1 0x558df635a658 in main forge-combo29/tests_audit/proof_eval_param_name_oob.cpp:19
```

- **Proposed fix**:

```diff
--- a/forge-combo29/src/eval_params.cpp
+++ b/forge-combo29/src/eval_params.cpp
@@ -20,6 +20,7 @@ Table table = defaults();
 KingSafetyWeights king_safety{};
 
 const char* name(int index) {
+    if (index < 0 || index >= Count) return "Unknown";
     static thread_local std::string buffer;
     auto indexed = [&](const char* base, int start) {
```

---

### Finding 12 — `Board::move_to_uci(Move::none())` formats a null/empty move as `"a1a1"` instead of UCI `"0000"`

- **Severity**: low
- **File and lines**: `src/board.cpp:1156-1167`
- **Trigger**: Calling `forge::Board::move_to_uci(forge::Move::none())` (for example on `SearchInfo::best_move` when a checkmated/stalemated or empty `searchmoves` root returns `Move::none()`).
- **What goes wrong**:
  1. `Move::none()` has `from == 0, to == 0, promotion == 0, flags == 0` (`include/forge/board.hpp:102-103`).
  2. `src/uci.cpp:364` manually works around this (`result.best_move.from == result.best_move.to ? "0000" : forge::Board::move_to_uci(result.best_move)`), but `Board::move_to_uci()` itself lacks `if (move.is_none()) return "0000";` and silently returns `"a1a1"`. Any caller of the public `Board::move_to_uci` API (or `emit()` if a `Move::none()` ever entered `pv`) emits `"a1a1"` instead of UCI's `"0000"`.
- **Proof**: by reading
- **Proposed fix**:

```diff
--- a/forge-combo29/src/board.cpp
+++ b/forge-combo29/src/board.cpp
@@ -1154,6 +1154,7 @@ std::optional<Move> Board::parse_uci(std::string_view text) {
 }
 
 std::string Board::move_to_uci(const Move& move) {
+    if (move.is_none()) return "0000";
     std::string text;
     text += static_cast<char>('a' + file_of(move.from));
```

---

## Checked and Found Correct

1. **Bitboards, shifts, and slider tables (`include/forge/bitboard.hpp`, `src/bitboard.cpp`)**:
   - All shift amounts are strictly in `0..63` (`square_bb(0..63)`, `file_bb(0..7)`, `rank_bb(0..7)`, `Magic::shift = 64 - popcount(mask)` in `52..59`).
   - `lsb` / `msb` / `pop_lsb` are never called on empty bitboards (`nearest_square_distance` checks `targets != 0`; `evaluate_king` checks `own != 0` / `enemy != 0` / `own_pawns != 0`).
   - `RookAttackTable` (`0x19000 = 102,400`) and `BishopAttackTable` (`0x1480 = 5,248`) exactly match the sum of `2^popcount(mask)` over all 64 squares for both multiply-magics and BMI2 `_pext_u64`.
2. **Move generation, legality, check detection, and Zobrist hashing (`include/forge/board.hpp`, `src/board.cpp`)**:
   - Castling rights after rook moves and rook captures on `a1/h1/a8/h8` are properly cleared via `CastlingMasks[move.from] & CastlingMasks[move.to]` (`src/board.cpp:166-176, 1058`).
   - En-passant legality (including horizontal double-pawn discovered check pins like `8/8/8/K1pP3r/8/8/8/7k w - c6 0 1`) is verified with `square_attacked_with_occupancy` removing both `from` and `captured_square`.
   - En-passant Zobrist key updates in `set_fen`, `make_move`, `make_null_move`, and `key_after` consistently hash `Z.ep[file]` iff `has_legal_en_passant_capture()` is true; differentially verified across 196,565 nodes (including null moves, castling, EP, promotions, and capture-promotions) with zero mismatches.
   - `FORGE_SPD_KING_LINES` (`is_legal` and `gives_check` fast paths) and `FORGE_SPD_NO_ZERO_MOVELISTS=2` (`GenMode::Quiets`) match full recomputation on all 196,565 oracle tree nodes.
3. **Repetition, 50-move Checkmates, and Insufficient Material (`src/board.cpp:1189-1223`, `src/search.cpp:903-914, 1582-1599`)**:
   - Game-level threefold repetition (`Board::is_repetition()`) and search-level repetition across the root and after null moves (`Board::is_repetition(root_index)` bounded by `std::min(halfmove_, plies_from_null_)`) handle root/pre-root parity accurately.
   - Checkmate on the 100th half-move (`halfmove_clock == 100` with `in_check() && !has_legal_move()`) is scored as checkmate (`mated_in(ply)` inside search and `-MateValue` at the root), not a 50-move draw.
   - Stalemate and checkmate at the root are properly distinguished from an empty `searchmoves` filter (`restricted_root_empty`).
4. **Static Exchange Evaluation (`src/board.cpp:27-119, 1229-1370`)**:
   - En passant, promotions, capture-promotions, recapture promotions (`promotion_recapture_exchange`), pinned defenders (`snipers` / `forbidden`), defenders while in check (`checked ? king_attackers : ...`), X-ray slider batteries, and terminal king captures (forbidden when opponent still attacks `to`) were differentially tested against an exact legal-move LVA minimax oracle across 266,596 legal moves with **0** discrepancies.
5. **NNUE Incremental Accumulator, Runtime PSQT, and SIMD Alignment/Parity (`include/forge/nnue.hpp`, `src/nnue.cpp`, `src/eval.cpp`)**:
   - `nnue::update` matches `nnue::refresh` bit-for-bit across quiet moves, captures, en passant, castling (`dirty.count == 4`), promotions, capture-promotions (`dirty.count == 3`), and null moves (`dirty.count == 0`) over all 196,565 tested tree nodes under ASan+UBSan.
   - `Accumulator::values` (`alignas(32)` / `alignas(64)`), `Weights::w2` (`alignas(32)` / `alignas(64)`), and `lanes[16]` (`alignas(64)`) satisfy all `_mm_load_ps` / `_mm256_load_ps` / `_mm512_load_ps` alignment requirements, and the 16-lane ordered reduction produces bit-identical evaluations across SSE2, AVX2, AVX-512, and scalar builds with `-ffp-contract=off -fno-fast-math`.
6. **Transposition Table Striped Locking, Exclusive Lease, and Age Wrapping (`include/forge/search.hpp`, `src/search.cpp:205-347`)**:
   - `ExclusiveLease` is only acquired when `workers_.size() == 1`; multi-threaded searches (`workers_.size() > 1`) always lock `stripes_[cluster % 1024]`, eliminating torn `TTEntry` reads/writes under ThreadSanitizer.
   - 5-bit `generation_` wraps cleanly modulo 32 (`(generation_ + 1U) & 31U` and `(32 + generation_ - entry.generation()) & 31U`).
7. **Null-Move Pruning & Aspiration Window Re-searches (`src/search.cpp:1208-1246, 1653-1676`)**:
   - Null-move pruning is never attempted in check (`!in_check`), at PV/root nodes (`!pv_node`), on consecutive null moves (`!(ss - 1)->current_move.is_none()` and `ss->null_move_allowed`), when `is_mate_score(beta)`, or in pawn-only endings (`board.has_non_pawn_material(board.side_to_move())`), and clamps mate scores from null search down to `beta`.
   - Aspiration fail-low (`beta = (alpha + beta) / 2; alpha = max(iteration_score - delta, -Infinite)`) and fail-high (`beta = min(iteration_score + delta, Infinite)`) re-searches widen cleanly to `[-Infinite, Infinite]` without signed overflow.
8. **Polyglot Opening Book (`src/book.cpp`, `src/book_data.inc`, `src/polyglot_keys.inc`)**:
   - Big-endian `.bin` parsing, Polyglot piece/castle/EP/turn Zobrist keys, king-takes-rook castling decoding, and `variety_percent` selection are bounds-safe and exact.

---

## Suspicious But No Trigger Found

1. **`Searcher::ponderhit()` sentinel collision when `steady_clock` epoch is `0` (`include/forge/search.hpp:312, 426-431`, `src/search.cpp:873-877`)**:
   - `SharedSearchState::ponder_hit_ns` uses `0` as the `"not hit yet"` sentinel, and `ponderhit()` stores `steady_clock::now().time_since_epoch().count()` directly without forcing it non-zero (unlike `book_rng | 1ULL` in `src/uci.cpp:137`). On any OS/VM where `steady_clock` starts at boot and `ponderhit` occurs at `0 ns`, `ponder_hit_ns` remains `0` and pondering never transitions to timed search. Practically unreachable on Linux because boot + process startup exceeds `0 ns`.
2. **`SearchStack` indexing headroom at `MaxPly` (`include/forge/search.hpp:61, 347`, `src/search.cpp:1147, 1634-1635`)**:
   - `stack_` has size `MaxPly + 8 = 136` with root at `stack_[4]` (`ply = 0` -> index `4`, `ply = 127` -> index `131`). At `ply = 127`, `(ss + 2)->killers` writes `stack_[133]` (only 2 slots below `136`), and `ply = 128` returns before line 1147 (`line 1134`). Safe today, but increasing `ss + k` lookahead beyond `+4` without enlarging `MaxPly + 8` would overflow `stack_`.
3. **Packed `Score` (`S(mg, eg)`) middlegame half-word wraparound under extreme external `params::table` edits (`include/forge/eval.hpp:16-24`, `src/eval.cpp:486-517`)**:
   - With the compiled-in `src/eval_params_table.inc` weights and legal piece counts (`total <= 16` per side), the packed `mg` accumulator stays well inside `[-32768, 32767]`. However, external tuning tools mutating `forge::params::table` (supported via `RuntimePsqt`'s `int64_t` overflow check at `src/eval.cpp:496`) can wrap the low 16-bit `mg` lane into the upper 16-bit `eg` lane before `std::numeric_limits<Score>::max()` is exceeded.
4. **Helper threads do not check `hard_limit_ms_` independently (`src/search.cpp:895, 1617-1621`)**:
   - Only `id_ == 0` checks `elapsed_ms() >= hard_limit_ms_`, polling every 1,024 local nodes. If thread 0 stalls on OS scheduling or stdout mutex contention (`uci_output_mutex()`), helper threads keep running past `hard_limit_ms_` until thread 0 reaches its next 1,024-node boundary.
