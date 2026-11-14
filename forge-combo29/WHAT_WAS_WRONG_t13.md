# What was wrong, what the sanitizer found, and what changed

Branch `grok47/t13-thread-sanitizer`, engine tree `forge-combo29`, base `lock/combo29-20261110` (`16833ecc`).
The command log and the verbatim ThreadSanitizer text are in `REPORT_t13.md`. This file is the explanation.

## What was wrong

`Board::Board()` in `src/board.cpp` calls `attacks::init()` before it loads the start position. Every later legal-move, attack, and pin calculation reads the tables that `init` fills. Those tables are process-wide: `KnightTable`, `KingTable`, `PawnTable`, the rook and bishop magic descriptors, and `LineTable` / `BetweenTable`.

On the locked tree, `init` looked like this:

```cpp
void init() {
    static bool initialized = false;
    if (initialized) return;
    initialized = true;

    for (int square = 0; square < 64; ++square) {
        // write KnightTable, KingTable, PawnTable, masks, ...
    }
    init_magics(true, RookAttackTable.data(), RookMagics);
    init_magics(false, BishopAttackTable.data(), BishopMagics);
    // LineTable and BetweenTable, which themselves call rook() and bishop()
}
```

Two separate things are wrong with that, and they stack.

The `bool` is an ordinary static, not an atomic and not a mutex. One thread reads it while another thread writes it. That is a data race on the flag itself. C++ does not define what the reader observes.

The second problem is the order, and it would still be wrong if the flag were atomic. The writer stores `initialized = true` and only then starts filling the tables. A second thread can see `true`, return from `init`, and start generating moves while the first thread is still inside the loop. The flag says "finished" at the moment the work starts.

What that second thread then reads:

- `KnightTable`, `KingTable`, and `PawnTable` are still zero, or only some squares have been stored. `legal_moves()` on the start position must return 20 moves. A half-filled knight or pawn table drops moves or invents them. The start-position perft of 4865609 depends on these tables, so a torn fill changes the move generator for the rest of the process, not just for the racing thread.
- `Magic::table` is a pointer, and it starts as `nullptr`. `init_magics` is what stores `m.table = table + offset` and then fills the attack array that pointer addresses. `bishop()` does this with no check:

```cpp
const Magic& m = BishopMagics[static_cast<std::size_t>(square)];
return m.table[m.index(occupancy)];
```

  `rook()` is the same. If the second thread reaches a sliding attack before `init_magics` has stored that pointer, it indexes through null. That is the `SEGV` ThreadSanitizer printed, in `attacks::bishop` at `include/forge/bitboard.hpp:188` on the unmodified file.

- `LineTable` and `BetweenTable` are filled by calling `rook()` and `bishop()`. Those calls are only valid after both magic tables exist. A thread that has already returned from `init` can be inside `between()` while the first thread is still on an earlier square of the same loops.
- `init_magics` (the non-PEXT build, which is the one this tree uses) keeps `occupancies`, `references`, and `epochs` as function-local `static` arrays and reuses them for every square. Those arrays are also shared and unprotected. ThreadSanitizer did not get to print that pair: the null bishop pointer aborted the process first. The same missing "wait until the fill is finished" is what leaves them exposed. After the fix only one thread ever enters `init_magics`, so those scratch arrays stay single-threaded.

Why ordinary bench and a normal UCI game hide this: the first `Board` is built on one thread, `init` runs to completion, and every later call sees the flag and returns. The race needs two threads inside the first construction at the same time. Search with 2 or 4 threads does not do that. `Searcher` builds its workers after the caller's `Board` already exists, so the tables are already published before a helper thread runs.

## What ThreadSanitizer found

Grouped the way the task asked. Line numbers below are the unmodified `bitboard.cpp` / `bitboard.hpp`, from the run that crashed.

### Group C, startup. This is the bug above.

`tests_t13/startup_race.cpp` constructs four `Board`s at once, each on its own thread, then each calls `legal_moves()` and checks for the 20 start moves. On the unmodified engine ThreadSanitizer reported:

| Read | Write | What the second thread did |
| --- | --- | --- |
| `src/bitboard.cpp:138` `initialized` | `src/bitboard.cpp:139` `initialized = true` | Saw the flag and skipped the fill. |
| `include/forge/bitboard.hpp:184` `pawn` | `src/bitboard.cpp:152` `PawnTable` | Read a pawn-attack entry the writer was still storing. |
| `include/forge/bitboard.hpp:181` `knight` | `src/bitboard.cpp:145` `KnightTable` | Same, for a knight entry. |
| `include/forge/bitboard.hpp:182` `king` | `src/bitboard.cpp:149` `KingTable` | Same, for a king entry. |
| `include/forge/bitboard.hpp:188` `bishop` | the fill still inside `init` | `Magic::table` was still null. `SEGV`. The process aborted. |

No further pairs were printed because the process died on that null pointer. The pawn, knight, and king races are enough to show the reader was already using the tables while the writer was still in the per-square loop, which is before `init_magics`.

### Group A, the shared hash table. No race, and the torn-entry check was already there.

`tests_t13/race_driver.cpp` searches 20 positions to depth 10 with Hash 16, first with 2 threads and then with 4. Positions are openings, middlegames, endings, and two white-to-move mates. On the unmodified engine this driver printed no ThreadSanitizer report at all.

Every probe and every store takes `TranspositionTable::lock_stripe` for the whole cluster access (`probe_body` / `store_body` in `src/search.cpp`). The 2-thread and 4-thread runs use `TTAccess::Shared`. The main worker skips that lock only while it holds `ExclusiveLease`, and `Searcher::search` takes the lease only for `TTAccess::Exclusive` with exactly one worker. That path was not the one under test.

A hit is a copy of one 16-byte `TTEntry` made while the stripe lock is held. The copy is accepted only when `key32 == verification_key(key)` and `occupied()` is true. A store writes `key32` and the score, eval, move, depth, and bound in that same locked section. Another worker blocks on the same stripe until the writer unlocks, so it cannot observe a key from one position mixed with a score from another. `__builtin_prefetch` does not load an entry into the search, and this run did not report it.

I did not add a lock. I did not add a second checksum word. The locked copy plus `key32` is the torn-entry protection, and ThreadSanitizer staying silent across the TT traffic in this run is the check that the lock covers the entry fields.

### Group B, other shared search data. No race.

History tables, correction tables, the evaluation cache, the search stack, and the root-move effort arrays belong to one `Worker`. The shared stop flag, the ponder-hit time, and the per-worker node counters are `std::atomic`. Helpers are started after `new_search()` and joined before the next search. The same 2-thread and 4-thread run that covered the hash table reported none of these.

### Group C, options, output, and the UCI thread. No race, once it was actually run.

The first report said this from the `Searcher` drivers only. That was a hole: `src/uci.cpp` was not in the instrumented binary, so option handling, the `go` worker, and the `bestmove` print had not been under ThreadSanitizer. I built that binary and drove it:

- `uci`, `isready`, `setoption` for Hash 16, Threads 2, OwnBook false, Ponder true, then `ucinewgame`
- `position startpos` and `go depth 6`
- the mate-in-1 position and `go depth 6` (`bestmove a1a8`, `score mate 1`)
- `setoption name Threads value 4`, `go infinite`, `isready` while info lines were still printing, then `stop`
- `go depth 4 ponder`, then `ponderhit`

Stderr was empty. Exit status 0. So the UCI worker, the option writes (they run on the main thread, and `setoption` calls `stop_search` before it changes thread count or hash size), and the info / `bestmove` prints (they take `uci_output_mutex`) did not race in this session.

### One thing that was wrong in the test, not in the engine

`race_driver` used `is_mate_score(info.score)`. That function is true for a win and for a loss:

```cpp
return score >= MateInMaxPly || score <= -MateInMaxPly;
```

`MateInMaxPly` is `32000 - 128`, so 31872. Both fixtures are white to move and white is winning. A score of -31999 would mean white is getting mated, and the old check would still have printed `mate_ok`. The check is now `info.score >= MateInMaxPly`. Re-runs still returned 31999 on the mate in 1 (`a1a8`) and 31997 on the mate in 2, under ThreadSanitizer and under address/undefined, with 2 threads and with 4. Exit status 0 both times.

## What changed

Engine code, and only the startup publication:

- `src/bitboard.cpp`. `#include <mutex>`. The `static bool` is gone. The same fill, the same `init_magics` calls, and the same line/between loop now sit inside `std::call_once`. One thread runs the lambda. Every other caller blocks in `call_once` and does not return until the lambda has returned, which is after the magic pointers and the line tables have been stored. The fill body is the same statements as before.
- `include/forge/bitboard.hpp`. Comment only. It used to say initialisation was idempotent. It now says a concurrent caller waits until the fill has finished.

Nothing in `search.cpp`, `uci.cpp`, or the hash entry layout changed. No lock was added to the transposition table.

After that change, the same `startup_race` binary under ThreadSanitizer exits 0 with an empty stderr and prints `PASS startup` (four constructors, `bad 0`, and a legal move from the search that is stopped from a second thread). The same binary under `-fsanitize=address,undefined` also exits 0. `race_driver` under both sanitizers exits 0 with `PASS failures 0`.

Rule 7 on `./build/forge`, before the edit and again after it:

- `bench 11` = 312866
- `bench 13` = 862329
- `go perft 5` from the start position = 4865609

Those counts stay put because a single-threaded bench never overlaps `init`, and the bytes written into the tables are the same bytes as before. `call_once` only changes who is allowed to be inside the fill.

Files added, none of them on the search hot path: `tests_t13/race_driver.cpp`, `tests_t13/startup_race.cpp`, `REPORT_t13.md`, and this file.
