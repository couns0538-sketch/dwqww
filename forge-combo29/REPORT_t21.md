# Task t21: Round 2 Integration Report

Repository: `github.com/couns0538-sketch/dwqww`
Base branch: `origin/integrate/combo29-fixes` (`bf5574ee654a773f0ef3d06878707056b90cdad7`, containing lock `16833ecc` plus t1, t3, t6, t8)
Integration branch: `carbon/t21-integrate-round2`

---

## What I found

1. **Branch tip verification**: Seven of the eight remote branches matched the table hashes (`a847f237`, `3438c19e`, `9f48a760`, `c3468fc9`, `ed31021d`, `28ee8b54`, `d5e60c9d`). One differed: `git rev-parse origin/grok47/t18-uci-fuzz` printed `d1d10b3efa267de6e17f3bcb10b9564d714a4c05` (which gated `uci_loop` behind a macro in a follow-up commit), whereas the table specified `c90c9cb2` (`c90c9cb2...`). Per instruction 1, `c90c9cb2` from the table was merged.
2. **Compiler selection without system settings**: On this VM `/usr/bin/c++` pointed via `/etc/alternatives/c++` to `clang++` 18.1.3, which auto-selected `/usr/lib/gcc/x86_64-linux-gnu/14` where `libstdc++-14-dev` is not installed (`cannot find -lstdc++`). `g++` (GCC 13.3.0) has `libstdc++-13-dev`, `libasan8`, `libubsan1`, and `libtsan2` installed, so passing `CXX=g++` to `cmake` fixed compilation with zero system setting changes.
3. **MultiPV secondary-line stop defect in `t15` (Point 4)**: In `28ee8b54`, `alt_worker` owned an isolated `alt_shared` (`stop` always `false`) and received `narrowed` limits with `nodes`, `movetime_ms`, and `time_ms` cleared, so external `stop`, `go movetime` / game-clock hard limits, and `go nodes` budgets could not interrupt a secondary-line search once started (for example, on a mate-in-1 root with `MultiPV 4` and `go nodes 2500`, primary search reached depth 64 in <2000 nodes and line 2 would then search depth 64 unstopped).
4. **Wide-net weights coupling in `t19` (Point 5)**: In `d5e60c9d`, `src/nnue.cpp` hard-coded `#include "../tests_t19/nnue_weights_512.inc"` when `FORGE_NNUE_HIDDEN == 512`, coupling engine source to a test directory.
5. **Cross-branch option list interaction in `t16`**: `tests_t16/options.expected.txt` and `tests_t16/clamp.expected.txt` were recorded on the bare lock before `t8` added `option name NnueFile type string default <empty>` (already in base) and `t15` added `option name MultiPV type spin default 1 min 1 max 8`. Per rules 2 and 6, `tests_t16/*.expected.txt` were left untouched; filtering out only those two intentional `option name` lines yields an empty `diff -u` against both expected files.

---

## The change

All eight round-2 tasks (`t13`, `t17`, `t20`, `t18` at `c90c9cb2`, `t16`, selected paths of `t14`, `t15`, and tests/report of `t19`) are integrated in order onto `integrate/combo29-fixes`, resolving `src/uci.cpp`, `src/search.cpp`, and `include/forge/search.hpp` so every behaviour from `t1`, `t3`, `t6`, `t8`, and `t13`–`t20` is preserved. Secondary `MultiPV` worker searches now link to the main `Worker` and abort immediately when the main search's `stop` flag, time hard limit, or cumulative node budget triggers, without altering `MultiPV 1`. `CMakeLists.txt` and `src/nnue.cpp` replace `t19`'s test-folder `#include` with two CMake cache variables, `FORGE_NNUE_HIDDEN` (default `256`) and `FORGE_NNUE_WEIGHTS` (default `src/nnue_weights.inc`), preserving the default 256 search and 512-wide net parity (`bench 11` = 312866, `bench 13` = 862329, `perft 5` = 4865609).

---

## Files changed (against base `bf5574ee`)

Engine and build files:
- `forge-combo29/CMakeLists.txt` (modified: Point 5 cache variables only)
- `forge-combo29/include/forge/bitboard.hpp` (modified: `t13`)
- `forge-combo29/include/forge/board.hpp` (modified: `t17`)
- `forge-combo29/include/forge/eval.hpp` (modified: `t14`)
- `forge-combo29/include/forge/search.hpp` (modified: `t15` + `t21` Point 4)
- `forge-combo29/include/forge/uci.hpp` (added: `t18`)
- `forge-combo29/src/bitboard.cpp` (modified: `t13`)
- `forge-combo29/src/eval.cpp` (modified: `t14`)
- `forge-combo29/src/nnue.cpp` (modified: `t21` Point 5)
- `forge-combo29/src/search.cpp` (modified: `t15` + `t21` Point 4)
- `forge-combo29/src/uci.cpp` (modified: `t18`, `t16`, `t14`, `t15`)

Carried-over round-2 tests and reports:
- `forge-combo29/REPORT_t13.md`, `tests_t13/race_driver.cpp`, `tests_t13/startup_race.cpp`
- `forge-combo29/REPORT_t14.md`, `tests_t14/eval_cases.txt`, `tests_t14/test_eval.cpp`
- `forge-combo29/REPORT_t15.md`, `tests_t15/depth12_lock.txt`, `tests_t15/test_multipv.cpp`
- `forge-combo29/REPORT_t16.md`, `tests_t16/check_lines.cpp`, `tests_t16/clamp.expected.txt`, `tests_t16/clamp.in.txt`, `tests_t16/options.expected.txt`, `tests_t16/options.in.txt`, `tests_t16/ownbook.in.txt`, `tests_t16/ownbook.spec.txt`, `tests_t16/search.in.txt`, `tests_t16/search.spec.txt`, `tests_t16/start h2h4.book`
- `forge-combo29/REPORT_t17.md`, `tests_t17/rules_suite.cpp`
- `forge-combo29/REPORT_t18.md`, `tests_t18/uci_fuzz.cpp`
- `forge-combo29/REPORT_t19.md`, `tests_t19/eval_parity.cpp`, `tests_t19/nnue_weights_512.inc`, `tests_t19/wide_eval.cpp`, `tests_t19/wide_eval.hpp`, `tests_t19/widen_nnue.cpp`
- `forge-combo29/REPORT_t20.md`, `tests_t20/repeat_mate_test.cpp`

New `t21` files:
- `forge-combo29/tests_t21/multipv_stop_test.cpp`
- `forge-combo29/REPORT_t21.md`

---

## Per-file provenance and conflict resolutions

### 1. `forge-combo29/CMakeLists.txt`
- **Base (`bf5574ee`)**: unchanged lock CMake file (`2bb0af3c`). `t14`'s `CMakeLists.txt` and `README.md` edits were excluded per Step 6.
- **`t21` Point 5**: added cache variables `FORGE_NNUE_HIDDEN` (default `256`) and `FORGE_NNUE_WEIGHTS` (default `"src/nnue_weights.inc"`), resolved relative paths against `${CMAKE_CURRENT_SOURCE_DIR}`, and passed `FORGE_NNUE_HIDDEN=${FORGE_NNUE_HIDDEN}` and `FORGE_NNUE_WEIGHTS="${FORGE_NNUE_WEIGHTS_FILE}"` to `target_compile_definitions(forge PRIVATE ...)`. No other lines changed.

### 2. `forge-combo29/include/forge/bitboard.hpp` and `forge-combo29/src/bitboard.cpp`
- **`grok47/t13-thread-sanitizer` (`a847f237`)**: wrapped `forge::attacks::init()` table initialization inside `std::call_once` (`#include <mutex>`, `static std::once_flag once;`) and updated the header comment. Clean merge, no conflicts.

### 3. `forge-combo29/include/forge/board.hpp`
- **`grok47/t17-rules-suite` (`3438c19e`)**: added `friend struct BoardStateProbe;` in `Board`. Clean merge, no conflicts.

### 4. `forge-combo29/include/forge/eval.hpp` and `forge-combo29/src/eval.cpp`
- **`grok47/t14-eval-command` (`ed31021d`)**: taken via `git checkout ed31021d -- ...`; adds `struct EvalComponents` and `Evaluator::static_eval_components(const Board&)`. Neither file had been modified since `16833ecc`, so there were no conflicts.

### 5. `forge-combo29/include/forge/uci.hpp`
- **`grok47/t18-uci-fuzz` (`c90c9cb2`)**: new header declaring `int forge::uci_loop(std::istream& in);`. Clean merge, no conflicts.

### 6. `forge-combo29/include/forge/search.hpp`
- **Base (`t3` + `t6`)**: 64-bit `movetime_ms`/`time_ms`/`increment_ms` fields in `SearchLimits` (`t3`) and `bool stopped_by_nodes_ = false;` in `Worker` (`t6`).
- **`grok47/t15-multipv` (`28ee8b54`)**: added `int multipv = 1;` to `SearchLimits`. Auto-merged cleanly with `t3` and `t6`.
- **`t21` Point 4**: added `Worker* parent_worker_ = nullptr;`, `std::uint64_t extra_nodes_ = 0;`, and `[[nodiscard]] bool should_stop_with(std::uint64_t pending_nodes);` to `Worker`.

### 7. `forge-combo29/src/search.cpp`
- **Base (`t1` + `t6`)**: `bad_captures_` sized to `MoveList::Capacity` (`t1`); `stopped_by_nodes_` set in `Worker::should_stop()`, reset in `Worker::search()`, and checked before taking a partial-iteration root PV move (`t6`).
- **`grok47/t15-multipv` (`28ee8b54`)**: `multipv` clamping and `emit` formatting in `Worker::search`, `alt_shared`/`alt_worker` secondary-line excluded-root loop, and `Searcher::search` single-thread fallback when `multipv > 1`. Auto-merged cleanly with `t1` and `t6`.
- **`t21` Point 4**: factored `Worker::should_stop_with(std::uint64_t pending_nodes)` so `alt_worker` (`parent_worker_ != nullptr`) delegates stop checks (external `stop`, cumulative node budget `total_nodes() + extra_nodes_ + pending_nodes >= node_limit_`, and clock `hard_limit_ms_` / ponderhit state) to the main `Worker`; propagated `node_limit_specified_` to `alt_worker` so exact node budgets check on every node; accumulated `extra_nodes_ += alt.nodes`; aborted without pushing an incomplete `alt` line when `alt_worker->aborted_ || alt.depth < depth`; and included `extra_nodes_` in final `result.nodes`.

### 8. `forge-combo29/src/nnue.cpp`
- **Base (`t8`)**: `quantize`, `make_builtin`, `live_weights`, and `nnue::load_file` for `FORGENET` files.
- **`t21` Point 5** (replacing `t19`'s `nnue.cpp` edit): `#if defined(FORGE_NNUE_WEIGHTS)` includes `FORGE_NNUE_WEIGHTS` directly, falling back to `#elif __has_include("nnue_weights.inc")` when compiled standalone without `FORGE_NNUE_WEIGHTS`.

### 9. `forge-combo29/src/uci.cpp`
Touched by `t3` and `t8` (in base) and by `t18`, `t16`, `t14`, and `t15`:
- **Includes (lines 1–8)**: base (`t3`) added `#include "forge/uci_clock.hpp"`; Step 4 (`t18`, `c90c9cb2`) added `#include "forge/uci.hpp"` at the same insertion point. **Conflict resolution (Step 4)**: kept both `#include "forge/uci.hpp"` and `#include "forge/uci_clock.hpp"`.
- **Clock parsing in `parse_limits` (lines 84–113)**: from base (`t3`, `read_clock()` via `forge::parse_clock_ms`). Untouched by later merges.
- **Entry point `forge::uci_loop(std::istream&)` and `#ifndef FORGE_UCI_NO_MAIN` `main()` (lines 133–167, 469–477)**: from Step 4 (`t18`, `c90c9cb2`), plus `int multipv = 1;` from Step 7 (`t15`, `28ee8b54`).
- **`uci` option list (lines 174–198)**: combines `option name MultiPV type spin default 1 min 1 max 8` from Step 7 (`t15`), `option name NnueFile type string default <empty>` from base (`t8`), and the updated `#ifdef FORGE_EXPOSE_TUNABLES` comment from Step 5 (`t16`).
- **`setoption` handler (lines 218–317)**:
  - **Conflict resolution (Step 5, `t16` `c3468fc9` vs base `t8`)**: `HEAD` had the lock's manual `Book Depth` / `Book Variety` parser followed by `t8`'s `else if (name == "NnueFile")` block, while `t16` replaced `Book Depth` / `Book Variety` with `apply_spin(0, 100, ...)`. Resolved by keeping `t16`'s `apply_spin(0, 100, ...)` for `Book Depth` / `Book Variety` immediately followed by `t8`'s full `NnueFile` handler, plus `t16`'s `note_invalid()`, `Clear Hash`, `UseNNUE`, `Hash`, `Threads`, `Move Overhead`, and final `unknown option` `else` branch.
  - **Conflict resolution (Step 7, `t15` `28ee8b54` vs `HEAD` `t16`+`t8`)**: `t15` (branched from the lock) had pre-`t16` `UseNNUE` / `Hash` / `Threads` / `Move Overhead` blocks and parsed `MultiPV` with manual `std::from_chars` + `std::clamp(value, 1, 8)`. Resolved by keeping `t16`'s `UseNNUE` and `apply_spin` handlers and routing `MultiPV` through `apply_spin(1, 8, [&](int clamped) { multipv = clamped; })` so non-integer tokens are rejected, out-of-range integers (`< 1` or `> 8`) emit `info string invalid value for option MultiPV` and clamp to `[1, 8]`, and valid values `1..8` set `multipv` silently.
- **`go` limits setup (line 353)**: `limits.multipv = multipv;` from Step 7 (`t15`).
- **`eval` command (lines 409–415)**: **Manual integration (Step 6, `t14` `ed31021d`)**: applied `t14`'s `else if (command == "eval")` block directly before `else if (command == "bench")` so all prior `src/uci.cpp` changes from `t3`, `t8`, `t18`, and `t16` stayed intact.

---

## Full text of `t21` own changes (Points 4 and 5)

### Point 4 (`include/forge/search.hpp` and `src/search.cpp`, 21 added lines)

```diff
--- a/forge-combo29/include/forge/search.hpp
+++ b/forge-combo29/include/forge/search.hpp
@@ -367,6 +367,8 @@ private:
     // Set only when the node budget itself trips should_stop. A clock stop or an
     // external stop leaves this false so those paths keep the partial root move.
     bool stopped_by_nodes_ = false;
+    Worker* parent_worker_ = nullptr;
+    std::uint64_t extra_nodes_ = 0;
 #if FORGE_SPD_TT_NOTLS
     // True only while Searcher::search runs this (main) worker on the thread that
     // holds the table's ExclusiveLease; lock_stripe would hand back a deferred lock.
@@ -394,6 +396,7 @@ private:
     int search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
     int qsearch(Board& board, SearchStack* ss, int alpha, int beta);
     [[nodiscard]] bool should_stop();
+    [[nodiscard]] bool should_stop_with(std::uint64_t pending_nodes);
     [[nodiscard]] std::int64_t elapsed_ms() const;
     [[nodiscard]] std::uint64_t total_nodes() const;
     [[nodiscard]] bool is_draw(const Board& board, int ply) const;
--- a/forge-combo29/src/search.cpp
+++ b/forge-combo29/src/search.cpp
@@ -890,12 +890,10 @@ std::uint64_t Worker::total_nodes() const {
     return total;
 }
 
-bool Worker::should_stop() {
-    // Publish this thread's node count for the others at the same cadence.
-    nodes_.store(local_nodes_, std::memory_order_relaxed);
+bool Worker::should_stop_with(std::uint64_t pending_nodes) {
     if (shared_.stop.load(std::memory_order_relaxed)) return true;
     if (!is_main()) return false;
-    if (node_limit_specified_ && total_nodes() >= node_limit_) {
+    if (node_limit_specified_ && total_nodes() + extra_nodes_ + pending_nodes >= node_limit_) {
         stopped_by_nodes_ = true;
         return true;
     }
@@ -906,6 +904,14 @@ bool Worker::should_stop() {
     return false;
 }
 
+bool Worker::should_stop() {
+    // Publish this thread's node count for the others at the same cadence.
+    nodes_.store(local_nodes_, std::memory_order_relaxed);
+    if (shared_.stop.load(std::memory_order_relaxed)) return true;
+    if (parent_worker_ != nullptr) return parent_worker_->should_stop_with(local_nodes_);
+    return should_stop_with(0);
+}
+
 bool Worker::is_draw(const Board& board, int ply) const {
     (void)ply;
     if (board.halfmove_clock() >= 100) {
@@ -1517,14 +1523,17 @@ SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_inf
     seldepth_ = 0;
     aborted_ = false;
     stopped_by_nodes_ = false;
+    extra_nodes_ = 0;
     pondering_ = limits.ponder;
     null_tries_ = 0;
     null_cutoffs_ = 0;
     root_moves_ = limits.search_moves;
     root_restricted_ = limits.search_moves_specified;
     root_history_index_ = board.history_size() - 1;
     node_limit_ = limits.nodes;
-    node_limit_specified_ = is_main() && (limits.nodes_specified || limits.nodes != 0);
+    node_limit_specified_ = parent_worker_ != nullptr
+        ? parent_worker_->node_limit_specified_
+        : (is_main() && (limits.nodes_specified || limits.nodes != 0));
 
     // Time allocation.
@@ -1683,6 +1692,7 @@ SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_inf
         alt_shared = std::make_unique<SharedSearchState>(hash_mb);
         alt_worker = std::make_unique<Worker>(*alt_shared, 0);
+        alt_worker->parent_worker_ = this;
         alt_list.push_back(alt_worker.get());
     }
     for (int depth = 1; depth <= max_depth; ++depth) {
@@ -1747,7 +1757,7 @@ SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_inf
             std::vector<Move> banned{result.pv.front()};
             const int line_count = std::min(multipv, static_cast<int>(root_candidates.size()));
             for (int index = 2; index <= line_count && !aborted_; ++index) {
-                if (shared_.stop.load(std::memory_order_relaxed)) {
+                if (should_stop()) {
                     aborted_ = true;
                     break;
                 }
@@ -1775,6 +1785,11 @@ SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_inf
                 alt_shared->tt.clear();
                 alt_worker->clear();
                 const SearchInfo alt = alt_worker->search(board, narrowed, false, alt_list);
+                extra_nodes_ += alt.nodes;
+                if (alt_worker->aborted_ || alt.depth < depth) {
+                    aborted_ = true;
+                    break;
+                }
                 if (alt.best_move.is_none()) break;
                 if (std::find(banned.begin(), banned.end(), alt.best_move) != banned.end()) break;
                 std::vector<Move> pv = alt.pv;
@@ -1847,7 +1862,7 @@ SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_inf
     }
 
     nodes_.store(local_nodes_, std::memory_order_relaxed);
-    result.nodes = total_nodes();
+    result.nodes = total_nodes() + extra_nodes_;
     result.seldepth = std::max(result.seldepth, seldepth_);
```

### Point 5 (`CMakeLists.txt` and `src/nnue.cpp`, 9 added lines)

```diff
--- a/forge-combo29/CMakeLists.txt
+++ b/forge-combo29/CMakeLists.txt
@@ -16,6 +16,9 @@ set(FORGE_MARCH "x86-64-v4" CACHE STRING "value for -march (lock exe uses znver5
 # FORGE_PORTABLE=ON drops the two ISA-bound speed switches (SLIDER_PEXT, NNUE_ZMM) so it
 # builds on CPUs without AVX-512/BMI2. Use -DFORGE_MARCH=x86-64-v3 or native with it.
 option(FORGE_PORTABLE "build without the PEXT/AVX-512 speed switches" OFF)
+set(FORGE_NNUE_HIDDEN 256 CACHE STRING "NNUE hidden units per side")
+set(FORGE_NNUE_WEIGHTS "src/nnue_weights.inc" CACHE STRING "path of the NNUE weights file")
+get_filename_component(FORGE_NNUE_WEIGHTS_FILE "${FORGE_NNUE_WEIGHTS}" ABSOLUTE BASE_DIR "${CMAKE_CURRENT_SOURCE_DIR}")
 
 file(GLOB FORGE_SOURCES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)
 add_executable(forge ${FORGE_SOURCES})
@@ -23,7 +26,8 @@ target_include_directories(forge PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
 
 target_compile_definitions(forge PRIVATE
   NDEBUG
-  FORGE_NNUE_HIDDEN=256
+  FORGE_NNUE_HIDDEN=${FORGE_NNUE_HIDDEN}
+  FORGE_NNUE_WEIGHTS="${FORGE_NNUE_WEIGHTS_FILE}"
   FORGE_EXPOSE_TUNABLES=1
   FORGE_SPD_TT_NOTLS=1
   FORGE_SPD_NO_ZERO_MOVELISTS=2
--- a/forge-combo29/src/nnue.cpp
+++ b/forge-combo29/src/nnue.cpp
@@ -30,7 +30,10 @@
 #include <immintrin.h>
 #endif
 
-#if __has_include("nnue_weights.inc")
+#if defined(FORGE_NNUE_WEIGHTS)
+#include FORGE_NNUE_WEIGHTS
+#define FORGE_HAS_NNUE 1
+#elif __has_include("nnue_weights.inc")
 #include "nnue_weights.inc"
 #define FORGE_HAS_NNUE 1
 #else
```

### Standalone build command for `tests_t14/test_eval.cpp` (Step 6)

Because `t14`'s `CMakeLists.txt` changes were intentionally omitted, `tests_t14/test_eval.cpp` is built directly against the engine sources (excluding `uci.cpp`, or using `-DFORGE_UCI_NO_MAIN`):

```bash
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 \
  -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -I forge-combo29/include -pthread \
  forge-combo29/tests_t14/test_eval.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/book.cpp forge-combo29/src/eval.cpp \
  forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp \
  forge-combo29/src/search.cpp \
  -o /tmp/t14_eval
/tmp/t14_eval forge-combo29/tests_t14/eval_cases.txt
```

---

## Commands and output

### 1. Start commands and baseline rule-7 check

First run (default `/usr/bin/c++` -> `clang++` selecting GCC 14 without `libstdc++-14-dev`):

```bash
git fetch origin && git checkout -b carbon/t21-integrate-round2 origin/integrate/combo29-fixes && cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
```

Output (exit 1):

```text
Switched to a new branch 'carbon/t21-integrate-round2'
branch 'carbon/t21-integrate-round2' set up to track 'origin/integrate/combo29-fixes'.
-- The CXX compiler identification is Clang 18.1.3
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - failed
-- Check for working CXX compiler: /usr/bin/c++
-- Check for working CXX compiler: /usr/bin/c++ - broken
CMake Error at /usr/share/cmake-3.28/Modules/CMakeTestCXXCompiler.cmake:60 (message):
  The C++ compiler "/usr/bin/c++" is not able to compile a simple test program.
  ...
  /usr/bin/ld: cannot find -lstdc++: No such file or directory
```

Re-run with `CXX=g++` (GCC 13.3.0):

```bash
rm -rf build && CXX=g++ cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build build -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

Output (exit 0):

```text
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info - done
-- Configuring done (0.4s)
-- Generating done (0.0s)
-- Build files have been written to: /agent/repos/dwqww/build
[100%] Built target forge
info string bench depth 11 nodes 312866 time 179 nps 1747854
info string bench depth 13 nodes 862329 time 472 nps 1826968
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

### 2. Branch tip verification

```bash
for b in \
  origin/integrate/combo29-fixes \
  origin/grok47/t13-thread-sanitizer \
  origin/grok47/t17-rules-suite \
  origin/grok47/t20-repeatable-search \
  origin/grok47/t18-uci-fuzz \
  origin/grok47/t16-option-handling \
  origin/grok47/t14-eval-command \
  origin/grok47/t15-multipv \
  origin/grok47/t19-wide-net-parity; do
  printf "%-36s %s\n" "$b" "$(git rev-parse "$b" 2>&1)"
done
```

Output:

```text
origin/integrate/combo29-fixes       bf5574ee654a773f0ef3d06878707056b90cdad7
origin/grok47/t13-thread-sanitizer   a847f23765d9404725449a9c8f3fe3c7c78685f2
origin/grok47/t17-rules-suite        3438c19e92b3f3919b1cd089b2e7e3162bbeee45
origin/grok47/t20-repeatable-search  9f48a760552c385e98a18f29b6733c36c067cbdf
origin/grok47/t18-uci-fuzz           d1d10b3efa267de6e17f3bcb10b9564d714a4c05
origin/grok47/t16-option-handling    c3468fc9262edbd8068d2b9ac5244379e055f756
origin/grok47/t14-eval-command       ed31021d6d3ea68e7dc626f21eb3d8379e23e653
origin/grok47/t15-multipv            28ee8b54e2dc44423aafe9f28eac62f4e684fe98
origin/grok47/t19-wide-net-parity    d5e60c9dcbabff4fe6a16a095f5ed0bb8d9bc92e
```

### 3. Per-step build, rule-7 numbers, and cumulative test checks (Steps 1–8 + Points 4 & 5)

After every step, `/tmp/t21-build/forge` was built in Release mode, checked for the three reference numbers of rule 7, and tested against every test suite accumulated up to that step:

| Step | Commit | Description | `bench 11` | `bench 13` | `perft 5` | Cumulative tests run |
|---|---|---|---|---|---|---|
| Base | `bf5574ee` | `origin/integrate/combo29-fixes` | 312866 | 862329 | 4865609 | baseline captured |
| 1 | `0c080a9c` | Merge `a847f237` (`t13-thread-sanitizer`) | 312866 | 862329 | 4865609 | t1, t3, t6, t8, t13: PASS |
| 2 | `fb7b09d4` | Merge `3438c19e` (`t17-rules-suite`) | 312866 | 862329 | 4865609 | + t17: PASS |
| 3 | `4d2d1db4` | Merge `9f48a760` (`t20-repeatable-search`) | 312866 | 862329 | 4865609 | + t20: PASS |
| 4 | `04614cac` | Merge `c90c9cb2` (`t18-uci-fuzz`) | 312866 | 862329 | 4865609 | + t18: PASS |
| 5 | `32c6f45b` | Merge `c3468fc9` (`t16-option-handling`) | 312866 | 862329 | 4865609 | + t16: PASS |
| 6 | `f1009dfe` | Selected paths of `ed31021d` (`t14-eval-command`) | 312866 | 862329 | 4865609 | + t14: PASS |
| 7 | `8fc0f50d` | Merge `28ee8b54` (`t15-multipv`) | 312866 | 862329 | 4865609 | + t15: PASS |
| Pt 4 | `75c0726d` | MultiPV secondary-line stop/time/node limits + `tests_t21` | 312866 | 862329 | 4865609 | t15 + t21: PASS |
| 8 | `c37caf22` | Selected paths of `d5e60c9d` (`t19-wide-net-parity`) | 312866 | 862329 | 4865609 | + t19 `widen_nnue`: PASS |
| Pt 5 | `0dd0e091` | CMake `FORGE_NNUE_HIDDEN` & `FORGE_NNUE_WEIGHTS` | 312866 | 862329 | 4865609 | 256 & 512 builds + `eval_parity`: PASS |

*(Note: during initial development of `tests_t21/multipv_stop_test.cpp` before committing `75c0726d`, a first draft of `PipeBuf` overrode both `underflow()` and `uflow()` with a 1-byte `setg` window, causing `std::getline` to re-read byte 0 and time out; replacing `PipeBuf::underflow()` with a chunk buffer using `std::streambuf`'s standard `uflow()` fixed the test harness immediately. Commit `a712e108` then raised the test's `bench 11`/`13` wait timeout from 10 s to 60 s so the same test binary also completes under 30x-slower `-fsanitize=thread`.)*

### 4. Final Release build and rule-7 numbers (default 256 net)

Command:

```bash
CXX=g++ cmake -S forge-combo29 -B /tmp/t21-final/build-rel -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && \
cmake --build /tmp/t21-final/build-rel -j && \
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/t21-final/build-rel/forge
```

Output (exit 0):

```text
info string bench depth 11 nodes 312866 time 167 nps 1873449
info string bench depth 13 nodes 862329 time 443 nps 1946566
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

### 5. Final 512-wide net CMake build and rule-7 numbers (Point 5)

Portable AVX2 build (`-DFORGE_NNUE_HIDDEN=512 -DFORGE_NNUE_WEIGHTS=/agent/repos/dwqww/forge-combo29/tests_t19/nnue_weights_512.inc`):

```bash
CXX=g++ cmake -S forge-combo29 -B /tmp/t21-final/build-512 -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DFORGE_NNUE_HIDDEN=512 -DFORGE_NNUE_WEIGHTS=/agent/repos/dwqww/forge-combo29/tests_t19/nnue_weights_512.inc && \
cmake --build /tmp/t21-final/build-512 -j && \
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/t21-final/build-512/forge
```

Output (exit 0):

```text
info string bench depth 11 nodes 312866 time 241 nps 1298199
info string bench depth 13 nodes 862329 time 514 nps 1677682
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

Non-portable AVX-512 ZMM build (`-DFORGE_MARCH=x86-64-v4 -DFORGE_NNUE_HIDDEN=512 -DFORGE_NNUE_WEIGHTS=tests_t19/nnue_weights_512.inc`) was also built in `/tmp/t21-build512zmm` and likewise printed `bench 11` = `312866`, `bench 13` = `862329`, `nodes 4865609`.

### 6. `MultiPV 1` output identity against base (`bf5574ee`)

On both base (`bf5574ee`, `/tmp/t21-base-ref.out`) and the finished branch (`/tmp/t21-final/final-ref.out`), an interactive bash `coproc` session set `Threads 1`, `Hash 16`, `OwnBook false`, `MultiPV 1` (on the finished branch), waited for `readyok`, ran `bench 11`, `bench 13`, and ran `go depth 12` (awaiting `bestmove` on each) across the five positions:
1. `position startpos`
2. `position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`
3. `position fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8`
4. `position fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1`
5. `position fen 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1`

Command:

```bash
sed -E 's/ time [0-9]+/ time T/g; s/ nps [0-9]+/ nps N/g' /tmp/t21-base-ref.out > /tmp/t21-final/base-norm.out && \
sed -E 's/ time [0-9]+/ time T/g; s/ nps [0-9]+/ nps N/g' /tmp/t21-final/final-ref.out > /tmp/t21-final/final-norm.out && \
diff -u /tmp/t21-final/base-norm.out /tmp/t21-final/final-norm.out && echo "MULTIPV1_BASE_PARITY_OK"
```

Output (exit 0, zero diff lines):

```text
MULTIPV1_BASE_PARITY_OK
```

Full 68-line transcript of `/tmp/t21-final/final-ref.out`:

```text
readyok
info string bench depth 11 nodes 312866 time 167 nps 1873449
info string bench depth 13 nodes 862329 time 445 nps 1937817
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 1930600 hashfull 7 time 5 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 1871714 hashfull 10 time 7 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 1997916 hashfull 15 time 12 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 1829677 hashfull 36 time 31 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
info depth 1 seldepth 18 score cp -76 nodes 1942 nps 1942000 hashfull 1 time 1 pv e2a6 b4c3
info depth 2 seldepth 18 score cp -76 nodes 2070 nps 2070000 hashfull 1 time 1 pv e2a6 b4c3 d2c3
info depth 3 seldepth 18 score cp -76 nodes 2178 nps 2178000 hashfull 1 time 1 pv e2a6 b4c3 d2c3 h3g2
info depth 4 seldepth 18 score cp -76 nodes 2568 nps 2568000 hashfull 1 time 1 pv e2a6 b4c3 d2c3 h3g2 f3g2
info depth 5 seldepth 20 score cp -137 nodes 5913 nps 1971000 hashfull 3 time 3 pv e2a6 b4c3 d2c3 e6d5 e1g1 d5e4
info depth 6 seldepth 22 score cp -104 nodes 7089 nps 1772250 hashfull 4 time 4 pv e2a6 b4c3 d2c3 e6d5 e1c1 f6e4
info depth 7 seldepth 22 score cp -252 nodes 21156 nps 1627384 hashfull 11 time 13 pv d5e6 e7e6 e2a6 e6e5 e1c1 b4c3 d2c3
info depth 8 seldepth 22 score cp -123 nodes 26416 nps 1651000 hashfull 13 time 16 pv e2a6 b4c3 d2c3 e6d5 e5g4 h3g2 f3g2 d5e4
info depth 9 seldepth 22 score cp -240 nodes 41370 nps 1723750 hashfull 19 time 24 pv d5e6 e7e6 e2a6 h3g2 f3g2 e6e5 e1c1 b4c3 d2c3 e5c5
info depth 10 seldepth 22 score cp -166 nodes 53230 nps 1663437 hashfull 28 time 32 pv e2a6 b4c3 d2c3 e6d5 e5g4 f6g4 c3g7 g4e5 g7e5 e7e5 e1g1 d5e4
info depth 11 seldepth 22 score cp -132 nodes 88799 nps 1644425 hashfull 50 time 54 pv e2a6 h3g2 f3g2 b4c3 d2c3 e6d5 e5g4 d5e4 e1c1 e8f8 h2h3 f6g4 c3g7 f8g7 h3g4
info depth 12 seldepth 26 score cp -155 nodes 182597 nps 1601728 hashfull 107 time 114 pv e2a6 b4c3 d2c3 e6d5 e5g4 h3g2 f3g2 e8f8 c3f6 g7f6 e1c1 d5e4 g2g3 c7c6 g4f6 e7f6 c1b1 a8e8
bestmove e2a6
info depth 1 seldepth 3 score cp -318 nodes 56 nps 0 hashfull 0 time 0 pv a2a3
info depth 2 seldepth 4 score cp -313 nodes 112 nps 0 hashfull 0 time 0 pv a2a3 h7h6
info depth 3 seldepth 5 score cp -328 nodes 219 nps 0 hashfull 0 time 0 pv a2a3 h7h6 f1e2 d5c4
info depth 4 seldepth 6 score cp -328 nodes 347 nps 0 hashfull 0 time 0 pv a2a3 h7h6 f1e2 d5c4 e2c4
info depth 5 seldepth 7 score cp -329 nodes 870 nps 0 hashfull 0 time 0 pv a2a3 d8b6 d1c2 h7h6 c4d5 e6d5
info depth 6 seldepth 8 score cp -329 nodes 1459 nps 0 hashfull 0 time 0 pv a2a3 d8b6 d1c2 h7h6 c4d5 e6d5
info depth 7 seldepth 15 score cp -352 nodes 5390 nps 1796666 hashfull 2 time 3 pv c4d5 e6d5 f1d3 c8g4 d3b1 h7h6 e1g1
info depth 8 seldepth 15 score cp -350 nodes 8564 nps 2141000 hashfull 4 time 4 pv f1d3 d5c4 d3c4 c8d7 e1g1 d8b6 f1e1 b6b2
info depth 9 seldepth 15 score cp -345 nodes 13539 nps 1934142 hashfull 7 time 7 pv f1d3 d5c4 d3c4 d8b6 d1b1 c8d7 e1g1 c6a5 c4e2 f8c8
info depth 10 seldepth 16 score cp -338 nodes 32958 nps 1831000 hashfull 18 time 18 pv a2a3 f6e4 c3e4 d5e4 f3d2 f7f5 f1e2 c8d7 e1g1
info depth 11 seldepth 18 score cp -331 nodes 45946 nps 1767153 hashfull 26 time 26 pv a2a3 f6e4 a1c1 d8a5 c4d5 e6d5 d1b3 c8e6 f1d3 e4c3 c1c3
info depth 12 seldepth 22 score cp -319 nodes 87708 nps 1754160 hashfull 47 time 50 pv a2a3 h7h6 b2b4 d5c4 f1c4 a7a6 c4a2 b7b5 e1g1 c8b7 d1b3 a8c8
bestmove a2a3
info depth 1 seldepth 2 score cp 83 nodes 20 nps 0 hashfull 0 time 0 pv a5a6
info depth 2 seldepth 4 score cp 167 nodes 83 nps 0 hashfull 0 time 0 pv b4c4 h5e5 c4c7
info depth 3 seldepth 6 score cp 167 nodes 127 nps 0 hashfull 0 time 0 pv b4c4 h5e5 c4c7 e5e2
info depth 4 seldepth 6 score cp 71 nodes 443 nps 0 hashfull 0 time 0 pv b4c4 h5h7 c4f4 h4g3 f4f3 g3g2
info depth 5 seldepth 8 score cp 306 nodes 791 nps 0 hashfull 0 time 0 pv b4f4 h4g3 f4f7 h5e5 f7c7
info depth 6 seldepth 10 score cp 306 nodes 921 nps 0 hashfull 0 time 0 pv b4f4 h4g3 f4f7 h5e5 f7c7 e5e2
info depth 7 seldepth 12 score cp 103 nodes 1746 nps 0 hashfull 0 time 0 pv b4f4 h4g3 f4f7 h5c5 f7g7 g3f4 g7e7 f4g3
info depth 8 seldepth 16 score cp 90 nodes 5143 nps 2571500 hashfull 1 time 2 pv b4c4 h5e5 c4c7 e5e2 b5b6 e2a2 a5b5 a2g2 c7c1
info depth 9 seldepth 20 score cp 155 nodes 16822 nps 2403142 hashfull 5 time 7 pv b4f4 h4g3 f4c4 h5c5 a5b4 c5c4 b4c4 g3g2 c4d5 g2g3
info depth 10 seldepth 20 score cp 101 nodes 23651 nps 2365100 hashfull 8 time 10 pv b4f4 h4g3 f4c4 h5h7 c4c3 g3f2 a5a6 f2e2 a6b7 h7h5 b7c6 h5h7
info depth 11 seldepth 25 score cp 126 nodes 30834 nps 2371846 hashfull 10 time 13 pv b4f4 h4g3 f4c4 h5h7 a5a6 g3g2 e2e4 g2f3 a6b7 h7h5 b7c7 h5b5 c7d6
info depth 12 seldepth 25 score cp 121 nodes 35955 nps 2397000 hashfull 12 time 15 pv b4f4 h4g3 f4c4 h5h7 a5a6 g3g2 a6b7 h7h5 b7c7 h5b5 c7d6 g2g3 c4a4 b5b8 d6d5 g3f2
bestmove b4f4
info depth 1 seldepth 1 score cp -899 nodes 12 nps 0 hashfull 0 time 0 pv g8h8
info depth 2 seldepth 3 score cp -910 nodes 53 nps 0 hashfull 0 time 0 pv g7g6 d1d7
info depth 3 seldepth 5 score cp -891 nodes 129 nps 0 hashfull 0 time 0 pv g7g6 d1d7 g8g7
info depth 4 seldepth 5 score cp -874 nodes 337 nps 0 hashfull 0 time 0 pv g7g6 g1f1 g8g7 f1e2
info depth 5 seldepth 8 score cp -909 nodes 765 nps 0 hashfull 0 time 0 pv g7g6 g1f1 g8h8 f1e2 h8g7
info depth 6 seldepth 9 score cp -906 nodes 1660 nps 0 hashfull 0 time 0 pv f7f5 g1f1 h7h5 f1e2 g8h7 d1d7
info depth 7 seldepth 11 score cp -917 nodes 3349 nps 3349000 hashfull 2 time 1 pv g7g5 g1f1 g8g7 d1d5 f7f6 f1e2 h7h5
info depth 8 seldepth 14 score cp -951 nodes 7242 nps 3621000 hashfull 3 time 2 pv g7g5 g1f1 g8g7 f1e2 h7h5 e2e3 g7g6 e3d4 g6f5
info depth 9 seldepth 19 score cp -984 nodes 18844 nps 3140666 hashfull 7 time 6 pv g7g5 g1f1 h7h5 f1e2 f7f6 e2e3 h5h4 d1d5 g8g7 e3d4
info depth 10 seldepth 21 score cp -984 nodes 31043 nps 3104300 hashfull 11 time 10 pv f7f5 g1f1 h7h5 d1d7 g8h7 f1e2 h7h6 e2d3 g7g6 d3d4
info depth 11 seldepth 21 score cp -986 nodes 45862 nps 3057466 hashfull 18 time 15 pv h7h5 g1f1 g8h7 f1e2 h7h6 e2e3 g7g6 e3e4 f7f6 e4d4 h6g5
info depth 12 seldepth 21 score cp -1001 nodes 69141 nps 3006130 hashfull 23 time 23 pv h7h5 g1f1 h5h4 f1e2 g7g5 d1d5 f7f6 e2e3 g8g7 e3e4 g7g6 d5a5 g6h6
bestmove h7h5
```

### 7. All merged tests and `tests_t21` in Release build

Common compile flags (`$CXXFLAGS`):
`-std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include -pthread`

Commands executed:

```bash
ENG_OBJS="/tmp/t21-final/build-rel/CMakeFiles/forge.dir/src/bitboard.cpp.o /tmp/t21-final/build-rel/CMakeFiles/forge.dir/src/board.cpp.o /tmp/t21-final/build-rel/CMakeFiles/forge.dir/src/book.cpp.o /tmp/t21-final/build-rel/CMakeFiles/forge.dir/src/eval.cpp.o /tmp/t21-final/build-rel/CMakeFiles/forge.dir/src/eval_params.cpp.o /tmp/t21-final/build-rel/CMakeFiles/forge.dir/src/nnue.cpp.o /tmp/t21-final/build-rel/CMakeFiles/forge.dir/src/search.cpp.o"
g++ $CXXFLAGS forge-combo29/tests_t1/bad_capture_overflow.cpp $ENG_OBJS -o /tmp/t21-final/rel-tests/t1 && /tmp/t21-final/rel-tests/t1
g++ $CXXFLAGS forge-combo29/tests_t3/clock_parse_test.cpp -o /tmp/t21-final/rel-tests/t3 && /tmp/t21-final/rel-tests/t3
g++ $CXXFLAGS forge-combo29/tests_t6/fixed_nodes.cpp $ENG_OBJS -o /tmp/t21-final/rel-tests/t6 && /tmp/t21-final/rel-tests/t6
g++ $CXXFLAGS -I forge-combo29/src forge-combo29/tests_t8/nnue_convert.cpp -o /tmp/t21-final/rel-tests/t8_convert && /tmp/t21-final/rel-tests/t8_convert /tmp/t21-final/rel-tests/lock.forgenet
g++ $CXXFLAGS forge-combo29/tests_t8/nnue_file_test.cpp $ENG_OBJS -o /tmp/t21-final/rel-tests/t8 && /tmp/t21-final/rel-tests/t8 /tmp/t21-final/rel-tests/lock.forgenet
g++ $CXXFLAGS forge-combo29/tests_t13/race_driver.cpp $ENG_OBJS -o /tmp/t21-final/rel-tests/t13_race && /tmp/t21-final/rel-tests/t13_race
g++ $CXXFLAGS forge-combo29/tests_t13/startup_race.cpp $ENG_OBJS -o /tmp/t21-final/rel-tests/t13_startup && /tmp/t21-final/rel-tests/t13_startup
g++ $CXXFLAGS forge-combo29/tests_t17/rules_suite.cpp $ENG_OBJS -o /tmp/t21-final/rel-tests/t17_rules && /tmp/t21-final/rel-tests/t17_rules
g++ $CXXFLAGS forge-combo29/tests_t20/repeat_mate_test.cpp $ENG_OBJS -o /tmp/t21-final/rel-tests/t20_repeat_mate && /tmp/t21-final/rel-tests/t20_repeat_mate
g++ $CXXFLAGS -DFORGE_UCI_NO_MAIN -c forge-combo29/src/uci.cpp -o /tmp/t21-final/rel-tests/uci_nomain.o
g++ $CXXFLAGS -DFORGE_UCI_NO_MAIN forge-combo29/tests_t18/uci_fuzz.cpp /tmp/t21-final/rel-tests/uci_nomain.o $ENG_OBJS -o /tmp/t21-final/rel-tests/t18_uci_fuzz && /tmp/t21-final/rel-tests/t18_uci_fuzz
g++ -std=c++20 -O2 -Wall -Wextra forge-combo29/tests_t16/check_lines.cpp -o /tmp/t21-final/rel-tests/t16_check
/tmp/t21-final/build-rel/forge < forge-combo29/tests_t16/options.in.txt > /tmp/t21-final/rel-tests/t16_options.out
rg -vxF -e 'option name NnueFile type string default <empty>' -e 'option name MultiPV type spin default 1 min 1 max 8' /tmp/t21-final/rel-tests/t16_options.out | diff -u forge-combo29/tests_t16/options.expected.txt -
/tmp/t21-final/build-rel/forge < forge-combo29/tests_t16/clamp.in.txt > /tmp/t21-final/rel-tests/t16_clamp.out
rg -vxF -e 'option name NnueFile type string default <empty>' -e 'option name MultiPV type spin default 1 min 1 max 8' /tmp/t21-final/rel-tests/t16_clamp.out | diff -u forge-combo29/tests_t16/clamp.expected.txt -
/tmp/t21-final/build-rel/forge < forge-combo29/tests_t16/ownbook.in.txt > /tmp/t21-final/rel-tests/t16_ownbook.out && /tmp/t21-final/rel-tests/t16_check /tmp/t21-final/rel-tests/t16_ownbook.out forge-combo29/tests_t16/ownbook.spec.txt
/tmp/t21-final/build-rel/forge < forge-combo29/tests_t16/search.in.txt > /tmp/t21-final/rel-tests/t16_search.out && /tmp/t21-final/rel-tests/t16_check /tmp/t21-final/rel-tests/t16_search.out forge-combo29/tests_t16/search.spec.txt
g++ $CXXFLAGS forge-combo29/tests_t14/test_eval.cpp $ENG_OBJS -o /tmp/t21-final/rel-tests/t14_eval && /tmp/t21-final/rel-tests/t14_eval forge-combo29/tests_t14/eval_cases.txt
g++ $CXXFLAGS forge-combo29/tests_t15/test_multipv.cpp $ENG_OBJS -o /tmp/t21-final/rel-tests/t15_multipv && /tmp/t21-final/rel-tests/t15_multipv
g++ -std=c++20 -O2 -Wall -Wextra forge-combo29/tests_t19/widen_nnue.cpp -o /tmp/t21-final/rel-tests/widen_nnue && /tmp/t21-final/rel-tests/widen_nnue forge-combo29/src/nnue_weights.inc /tmp/t21-final/rel-tests/nnue_512.inc && cmp forge-combo29/tests_t19/nnue_weights_512.inc /tmp/t21-final/rel-tests/nnue_512.inc
COMMON19="-std=c++20 -O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=0 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_TT_NOTLS=1 -I forge-combo29/include -I forge-combo29/tests_t19"
g++ $COMMON19 -DFORGE_NNUE_HIDDEN=256 -c forge-combo29/src/nnue.cpp -o /tmp/t21-final/rel-tests/nnue256.o
g++ $COMMON19 -DFORGE_NNUE_HIDDEN=512 -DFORGE_NNUE_WEIGHTS='"/agent/repos/dwqww/forge-combo29/tests_t19/nnue_weights_512.inc"' -Dnnue=nnue512 -c forge-combo29/src/nnue.cpp -o /tmp/t21-final/rel-tests/nnue512.o
g++ $COMMON19 -DFORGE_NNUE_HIDDEN=512 -Dnnue=nnue512 -c forge-combo29/tests_t19/wide_eval.cpp -o /tmp/t21-final/rel-tests/wide_eval.o
g++ $COMMON19 -DFORGE_NNUE_HIDDEN=256 -c forge-combo29/tests_t19/eval_parity.cpp -o /tmp/t21-final/rel-tests/eval_parity.o
g++ $COMMON19 -pthread /tmp/t21-final/build-rel/CMakeFiles/forge.dir/src/bitboard.cpp.o /tmp/t21-final/build-rel/CMakeFiles/forge.dir/src/board.cpp.o /tmp/t21-final/build-rel/CMakeFiles/forge.dir/src/eval.cpp.o /tmp/t21-final/build-rel/CMakeFiles/forge.dir/src/eval_params.cpp.o /tmp/t21-final/rel-tests/nnue256.o /tmp/t21-final/rel-tests/nnue512.o /tmp/t21-final/rel-tests/wide_eval.o /tmp/t21-final/rel-tests/eval_parity.o -o /tmp/t21-final/rel-tests/t19_eval_parity && /tmp/t21-final/rel-tests/t19_eval_parity
g++ $CXXFLAGS -DFORGE_UCI_NO_MAIN -Wall -Wextra forge-combo29/tests_t21/multipv_stop_test.cpp /tmp/t21-final/rel-tests/uci_nomain.o $ENG_OBJS -o /tmp/t21-final/rel-tests/t21_multipv_stop && /tmp/t21-final/rel-tests/t21_multipv_stop
```

Outputs (all exit 0):

```text
=== t1 ===
in_check 0
losing_captures 68
bestmove d3b1
nodes 176
=== t3 ===
clock_parse_test passed
=== t6 ===
PASS fixed-node score and move agree
=== t8 ===
wrote /tmp/t21-final/rel-tests/lock.forgenet hidden 256
PASS
=== t13 ===
PASS failures 0
stopped-search move d2d4 score 12 depth 8 legal
PASS startup
=== t17 ===
RESULT PASS fails=0
=== t20 ===
t20 result: PASS
=== t18 (full 200000 lines) ===
seed=361192554478 generated_lines=200000
part_a hand_written=193
part_a cases=193 ok time_ms=68
part_b 10000
...
part_b 190000
part_b seed=361192554478 lines=200000 ok time_ms=48859
SANITIZERS clean
=== t16 ===
T16_OPTIONS_OK
T16_CLAMP_OK
ok 54 lines
ok 7 lines
=== t14 ===
ok 30 positions, 10 mirrors, 3 in check, promotions white 2 black 1
=== t15 ===
PASS a depth 12 info matches the lock except time and nps
PASS a bestmoves match the lock
PASS b checked 10 positions at depth 8
PASS c two legal moves
PASS d mate in 1 line a1a8 mate 1
PASS nodes best d2d4
PASS movetime best d2d4
PASS threads 4 falls back to threads 1
explained 20
failures 0
RESULT passed
=== t19 ===
input forge-combo29/src/nnue_weights.inc
output /tmp/t21-final/rel-tests/nnue_512.inc
read w1=196608 b1=256 w2=512 b2=127
write w1=393216 b1=512 w2=1024 b2=127
padding_zeros w1=196608 b1=256 w2=512
lock_column_zeros w1=125
fingerprint w1=6227214367631889344 b1=10979643604819931428 w2=11500908642059936499
WIDEN_CMP_OK
seed 20261110
positions 100000
unique 98914
resets 310
make_failures 0
residual_256 1
residual_512 1
start_static_256 38
start_static_512 38
static_equal 100000
static_differ 0
static_max_abs_diff 0
worst_fen -
worst_static_256 0
worst_static_512 0
network_differ 0
network_max_abs_diff 0
worst_network_256 0
worst_network_512 0
hash_static_256 13290400224059203287
hash_static_512 13290400224059203287
=== t21 ===
infinite_stop_ms 1 move e2e4 PASS
movetime_200_ms 190 move e2e4 PASS
nodes_2500_ms 11 move a1a8 PASS
multipv1_bench PASS
```

### 8. All merged tests and `tests_t21` built with `-fsanitize=address,undefined`

Environment:
`ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=1`
`UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1:print_stacktrace=1`

Engine sanitizer build:

```bash
CXX=g++ cmake -S forge-combo29 -B /tmp/t21-final/build-san -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -g" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" && \
cmake --build /tmp/t21-final/build-san -j
```

Every test (`t1`, `t3`, `t6`, `t8`, `t13` `race_driver` + `startup_race`, `t17`, `t20`, `t16` all four transcripts, `t14`, `t15`, `t19` `widen_nnue` + `eval_parity` 100,000 positions, `t18` full 200,000-line `uci_fuzz`, and `t21` `multipv_stop_test`) was compiled and linked with `-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -g`:

```bash
g++ $SAN_FLAGS -DFORGE_UCI_NO_MAIN -Wall -Wextra forge-combo29/tests_t21/multipv_stop_test.cpp /tmp/t21-final/san/uci_nomain.o $SAN_OBJS -o /tmp/t21-final/san/t21_multipv_stop && \
/tmp/t21-final/san/t21_multipv_stop
```

Outputs (all exit 0, zero ASan/UBSan/LSan diagnostics):

```text
=== SAN t1 ===
in_check 0
losing_captures 68
bestmove d3b1
nodes 176
=== SAN t3 ===
clock_parse_test passed
=== SAN t6 ===
PASS fixed-node score and move agree
=== SAN t8 ===
PASS
=== SAN t13 ===
PASS failures 0
PASS startup
=== SAN t17 ===
RESULT PASS fails=0
=== SAN t20 ===
t20 result: PASS
=== SAN t16 ===
SAN_T16_OPTIONS_OK
SAN_T16_CLAMP_OK
ok 54 lines
ok 7 lines
=== SAN t14 ===
ok 30 positions, 10 mirrors, 3 in check, promotions white 2 black 1
=== SAN t15 ===
explained 20
failures 0
RESULT passed
=== SAN t19 ===
SAN_WIDEN_CMP_OK
positions 100000
static_equal 100000
static_differ 0
network_differ 0
hash_static_256 13290400224059203287
hash_static_512 13290400224059203287
=== SAN t18 (full 200000 lines) ===
seed=361192554478 generated_lines=200000
part_a hand_written=193
part_a cases=193 ok time_ms=136
part_b 10000
...
part_b 190000
part_b seed=361192554478 lines=200000 ok time_ms=178332
SANITIZERS clean
=== SAN t21 ===
infinite_stop_ms 2 move d2d4 PASS
movetime_200_ms 193 move d2d4 PASS
nodes_2500_ms 41 move a1a8 PASS
multipv1_bench PASS
```

### 9. ThreadSanitizer (`-fsanitize=thread`) on `t13` and `t21`

Command:

```bash
export TSAN_OPTIONS="halt_on_error=1:second_deadlock_stack=1" && \
CXX=g++ cmake -S forge-combo29 -B /tmp/t21-final/build-tsan -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 \
  -DCMAKE_CXX_FLAGS="-fsanitize=thread -fno-sanitize-recover=all -fno-omit-frame-pointer -g" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=thread" && \
cmake --build /tmp/t21-final/build-tsan -j && \
TSAN_OBJS="/tmp/t21-final/build-tsan/CMakeFiles/forge.dir/src/bitboard.cpp.o /tmp/t21-final/build-tsan/CMakeFiles/forge.dir/src/board.cpp.o /tmp/t21-final/build-tsan/CMakeFiles/forge.dir/src/book.cpp.o /tmp/t21-final/build-tsan/CMakeFiles/forge.dir/src/eval.cpp.o /tmp/t21-final/build-tsan/CMakeFiles/forge.dir/src/eval_params.cpp.o /tmp/t21-final/build-tsan/CMakeFiles/forge.dir/src/nnue.cpp.o /tmp/t21-final/build-tsan/CMakeFiles/forge.dir/src/search.cpp.o" && \
TSAN_FLAGS="-std=c++20 -O2 -g -fno-omit-frame-pointer -fsanitize=thread -fno-sanitize-recover=all -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include -pthread" && \
g++ $TSAN_FLAGS forge-combo29/tests_t13/race_driver.cpp $TSAN_OBJS -o /tmp/t21-final/tsan/t13_race && \
/tmp/t21-final/tsan/t13_race && \
g++ $TSAN_FLAGS forge-combo29/tests_t13/startup_race.cpp $TSAN_OBJS -o /tmp/t21-final/tsan/t13_startup && \
/tmp/t21-final/tsan/t13_startup && \
g++ $TSAN_FLAGS -DFORGE_UCI_NO_MAIN -c forge-combo29/src/uci.cpp -o /tmp/t21-final/tsan/uci_nomain.o && \
g++ $TSAN_FLAGS -DFORGE_UCI_NO_MAIN -Wall -Wextra forge-combo29/tests_t21/multipv_stop_test.cpp /tmp/t21-final/tsan/uci_nomain.o $TSAN_OBJS -o /tmp/t21-final/tsan/t21_multipv_stop && \
/tmp/t21-final/tsan/t21_multipv_stop
```

Output (all exit 0, empty stderr, zero ThreadSanitizer warnings):

```text
PASS failures 0
startup constructors 4 bad 0
stopped-search move c2c4 score 18 depth 8 legal
PASS startup
infinite_stop_ms 8 move d2d4 PASS
movetime_200_ms 196 move c2c4 PASS
nodes_2500_ms 289 move a1a8 PASS
multipv1_bench PASS
```

---

## What I could not verify

1. **Windows / Clang ThinLTO+PGO lock build**: Only Linux `g++` 13.3.0 builds (`x86-64-v3` portable and `x86-64-v4` AVX-512) were built and run on this VM; the Windows Clang PGO build recipe under `windows_build/` was not executed.
2. **Clang on this VM without `libstdc++-14-dev`**: Default `clang++` selected `/usr/lib/gcc/x86_64-linux-gnu/14`, which lacked `libstdc++.so` and `libclang-rt-18-dev`; per rule 4 (no system settings), system packages were not modified and GCC 13 (`CXX=g++`) was used instead.
3. **External UCI GUI front-ends and game-play strength**: All UCI tests drove `forge` via pipes or `forge::uci_loop(std::istream&)`; no GUI client or Elo/speed measurement was run.
