# Reproduced on the lock, 2026-11-13

Source is `lock/combo29-20261110` at `16833ecc03b425586f91f4c8834dea8807bf4c22`, extracted with `git archive` to `/tmp` and built there. The lock branch was not checked out for the build and was not modified.

Compiler: g++ 13.3.0. Host has AVX-512F and BMI2. Configure: `-DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=x86-64-v4`. Lock and correctness binaries also used `-fsanitize=address,undefined -fno-omit-frame-pointer -g`. The time-audit binary was a release build without sanitizers. No repository script was executed. Probes were a short UCI session from Python.

## Clock past 32 bits

`forge-combo29/src/uci.cpp:74` initialises the parsed integer to 0. `uci.cpp:77-78` uses `std::from_chars` into that `int` and returns 0 on any failure. `uci.cpp:99` then stores `max(0, that)` as White's `wtime`. Zero is the flagged clock (`search.hpp` defaults `time_ms` to -1, meaning no clock).

A standalone g++ 13.3.0 program confirmed `std::from_chars` of `3000000000` and `2147483648` into an `int` that starts at 0: `errc::result_out_of_range`, the whole token consumed, value left 0. `3000000000abc` is also out of range but the token is not fully consumed. `+10` is rejected.

Lock ASan binary, `setoption name OwnBook value false`, `Threads 1`, `position startpos`, `go wtime 3000000000 btime 3000000000`:

- `readyok` then `bestmove a2a3` about 1 ms later
- no `info depth` line

Same binary, `go wtime 2000 btime 2000`, was still printing increasing depths (depth 9 at engine time 72 ms) when the probe stopped it. OwnBook is off in both, because a book hit would have answered the 2000 ms clock immediately too.

`cursor/forge-time-audit-770f` at `82b4a082b18c8fa6f633d29019f4fa7b524c916a`, release build, same `go wtime 3000000000`: still searching at depth 16 (267839 nodes, engine time 190 ms) when stopped at 350 ms wall. It did not play the immediate `a2a3`.

`movestogo 3000000000` is the same parser plus `max(1, read_int())` at `uci.cpp:95`, so the source turns it into `movestogo 1`. That spend was not timed in this run. `cursor/forge-concurrency-audit-8d98` has no `result_out_of_range` handler; the clock defect is still in that tree.

## 64-slot deferred captures

`search.cpp:469` is `bad_captures_[bad_count_++] = move` with no size test. The lock CMake sets `FORGE_SPD_NO_ZERO_MOVELISTS=2` and does not set `FORGE_SDK_BADCAP_PREFIX`, so the array is `std::array<Move, 64>` at `search.cpp:576`. Quiets and the main capture list do check their sizes. This buffer does not.

Lock ASan binary, `OwnBook false`, `UseNNUE false`, `go depth 3` on

`3r4/Pn1Q1p2/1Q1n1QpN/1p1Q1pRB/1Qbp1QpN/2bQ1pRB/3r1QpK/2k2q2 w - - 0 1`

AddressSanitizer SEGV, write in `forge::MovePicker::next(bool)` at `src/search.cpp:469`, called from `Worker::search` at `search.cpp:1305`. Exit by signal, no `bestmove`. The same FEN with UseNNUE left at default also aborted with an ASan SEGV and no bestmove; that stack was not symbolized separately.

Control on the same binary: `position startpos`, `go depth 2`, `UseNNUE false` completed `bestmove e2e3`.

`cursor/forge-correctness-20261113-e6b6` at `dff76c5808d0ceb7fc3940d1758991c3c33fb26d` sizes that array to `MoveList::Capacity` (256) at `search.cpp:581`. The write is still unchecked. ASan build of that tree, `UseNNUE false`, same FEN, `go depth 3`: `info depth 1 ... score mate 1 ... pv d3b1` and `bestmove d3b1`. No sanitizer report. This run did not prove the mate with a second generator. It shows the lock crashes in the picker and this tree returns a move.

A position with more than 256 deferred captures would still write past the larger array. This run did not look for one. Release builds define `NDEBUG`, so `MoveList::push_back`'s capacity assert is compiled out as well.
