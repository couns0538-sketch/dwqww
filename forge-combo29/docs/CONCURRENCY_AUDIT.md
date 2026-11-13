# Forge concurrency audit

Audit of Chess Engine Forge 6.4.24 candidate as locked on `origin/lock/combo29-20261110` (`16833ecc03b425586f91f4c8834dea8807bf4c22`). That branch was not checked out and was not modified. Sources were imported from it onto `cursor/forge-concurrency-audit-8d98` (commit `e3a699a8`) and the fixes below are only on this branch.

The engine is lazy SMP: one `SharedSearchState` (transposition table plus atomics) and one `Worker` per thread. The UCI command thread is separate from the search worker. The default UCI search asks for `TTAccess::Exclusive`, and that lease is taken only when `workers_.size() == 1`. With `FORGE_SPD_TT_NOTLS=1` the exclusive owner uses `probe_owned` / `store_owned`. Every other access takes one of 1024 stripe mutexes. Probe and store drop the stripe lock between them.

Search values, reductions, and evaluation were not changed. One-thread bench node counts match the imported tree.

## How this was built

GCC 13.3.0 (`g++`). The machine has AVX-512F and BMI2, so the lock's ZMM kernel builds with `-DFORGE_MARCH=x86-64-v4`. `/usr/bin/c++` is Clang 18 and cannot link this tree (`-lstdc++` is missing).

```
cmake -S forge-combo29 -B /tmp/forge-build -DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=x86-64-v4
cmake --build /tmp/forge-build -j$(nproc)
```

`/tmp/forge-build/forge_concurrency_tests` runs the in-process cases. `tests/uci_concurrency.py` drives the `forge` binary.

## Reproduced before the fixes

The pre-fix binary had only test seams: `FORGE_INIT_PAUSE_MS` slept inside attack-table init after the old early `initialized` flag, and `after_main_` ran in the helper wind-down between the stop load and the stop restore. Search behavior was otherwise the imported code. Log: `docs/evidence/pre-fix-concurrency.txt`.

| Case | Observed | Exit |
| --- | --- | --- |
| Concurrent first `Board` construction, 8 followers, 80 ms pause | `FAIL init signal 11` (SIGSEGV) | child exit by signal |
| Six keys forced into one TT cluster; depth-40 store, then a depth-1 store of a different key into the same probed slot | `tt_race hit 0 depth 1 key32 5` | fail |
| `stop()` from `after_main_` while helpers are joined | `stop_flag_after_search 0`, best move still `d2d4` | fail |
| 4 threads, depth 5 | `nodes_result 3175`, `nodes_published 3752` after join | fail |
| Ponder movetime does not start before `ponderhit` | pass | |
| Explicit `stop()` on a 2-thread depth-32 search | `stop_latency_ms 1` | pass |

`ALL FAIL failures 4`.

## Root causes and fixes

**Attack tables.** `attacks::init()` set a non-atomic `initialized` flag before filling knight, king, and magic tables. `Board::Board()` calls `init()`. A second thread could observe the flag and read null magic pointers. `init()` is now `std::call_once` around the fill. The pause hook, when set, sleeps inside the once-callback, so other callers block until the tables exist. The concurrent test sees 20 legal start moves and zero bad boards.

**Transposition replacement.** Store treated "not the same position" as permission to overwrite the probed slot after the lock had been dropped. A full cluster picks the first slot on an equal replacement value (`depth - 4 * age`, strict `<`), so two racers that both probed slot 0 both wrote slot 0. The locked store now refuses the write when the slot no longer matches the probe snapshot, the occupant is a different key, and its replacement value is at least the incoming depth. Same-position depth rules are unchanged. The exclusive owner (`store_owned`, one thread) does not take this check, so its replacement decisions are the old ones.

**Stop during helper shutdown.** After the main worker returned, the old wind-down did `external_stop = stop.load(); stop = true; join; stop = external_stop`. A `stop()` that arrived after the load was cleared. Shutdown now sets a separate `finish` flag, joins, and clears only `finish`. `stop()` is a release store. `stop_requested()` is an acquire load. The wind-down is an RAII object, so an exception from the main worker still joins the helpers instead of destroying joinable `std::thread`s.

**Reported nodes.** `result.nodes` was sampled inside the main worker before helpers were joined, and helpers publish `nodes_` every 1024 nodes plus at exit. The result is now the sum of `worker->nodes()` after the join.

**Ponder.** `ponder_hit_ns == 0` meant both "not hit yet" and a real clock reading of zero, so a hit at the steady-clock epoch never started the clock. `ponderhit()` now sets a `ponder_hit` flag and records the timestamp. `elapsed_ms()`, the hard-time check, and the soft-time predicate read the flag. Info `time` and `SearchInfo::elapsed_ms` use `elapsed_ms()`, so a ponder search reports own-clock time (0 until the hit) rather than wall time from `go`. `go infinite ponder` used to wake and print `bestmove` on `ponderhit` alone, because the wait predicate treated any ponder hit as completion. It now waits for `stop` while `infinite` is set.

**Command thread.** `go perft` and `bench` ran on the thread that reads UCI, so `stop`, `isready`, and `quit` were not read until the command finished. Both now run on the search worker. `stop` sets the shared flag. Perft polls it at subtree depth 4 and above, prints `info string perft stopped`, and does not print a `nodes` total. Bench polls between positions, prints `info string bench stopped`, and skips the summary. A finished perft 1 is still `nodes 20`. A finished bench still prints the same summary line. Depth 0 perft stays on the command thread (`nodes 1`).

## Evidence after the fixes

`docs/evidence/post-fix-concurrency.txt` (release binary):

```
init_race bad_boards 0
tt_race hit 1 depth 40 key32 6
stop_flag_after_search 1 best d2d4
nodes_result 2903 nodes_published 2903
stop_latency_ms 1
ALL PASS failures 0
```

SMP node totals move between runs. The check is that the reported total equals the sum after join, not a particular node count.

ThreadSanitizer (`-fsanitize=thread` on the same sources; the target still adds `-O3`) also reported `ALL PASS failures 0` and printed no race report. Under TSan, `stop_latency_ms` was 19. Log: `docs/evidence/tsan-concurrency.txt`. That run covers the suite only. It does not exercise `prefetch` against `clear` / `resize`.

One-thread bench against a binary built from `e3a699a8` with the same compiler and march (`docs/evidence/bench-signature.txt`):

| Depth | Baseline nodes | Fixed nodes |
| --- | ---: | ---: |
| 1 | 884 | 884 |
| 4 | 4948 | 4948 |
| 6 | 15736 | 15736 |
| 8 | 67223 | 67223 |

`tests/uci_concurrency.py` against `/tmp/forge-build/forge` (`docs/evidence/uci-concurrency.txt`), all pass:

- `go infinite ponder` on `7k/6Q1/6K1/8/8/8/8/8 b - - 0 1` reaches depth 64, `ponderhit` does not print `bestmove`, and a later `stop` prints one `bestmove 0000`.
- 64 `isready` commands during `go infinite` with 2 threads each get their own `readyok` line, then one `bestmove` after `stop`.
- `go perft 7` answers `stop` and `isready` within the 2 second wait, prints `info string perft stopped`, and does not print a `nodes` total. `go perft 1` still prints `nodes 20`.
- `bench 10` answers `stop` with `info string bench stopped`. A later `bench 1` prints `nodes 884`.
- `quit` returns exit code 0.

## Limitations

- `prefetch` is `__builtin_prefetch` on the cluster and does not take the stripe lock. `clear`, `resize`, `new_search`, and destruction are still unsafe concurrent with search or prefetch. The table comment already requires quiescence. An exclusive lease around resize would not make prefetch safe.
- `generation_` and `epoch_` are plain integers. Search only reads them. `new_search` / `clear` / `resize` write them and must stay outside a live search.
- `nnue::enabled` and the tune integers are written from the command thread after `stop_search` has joined the worker.
- On a one-thread exclusive search, `hashfull` from a foreign thread takes the exclusive gate and blocks until the search ends. UCI prints `hashfull` on the owner thread.
- Helper threads do not apply time or node limits themselves. They exit when the main thread stores `stop` or `finish`, at the existing 1024-node check. They can overshoot. Seldepth in `info` is the main worker's seldepth.
- Info `nodes` during the search is still `total_nodes()` at emit time, so it can lag a helper's latest 1024-node publish. The `bestmove` search's `SearchInfo::nodes` is the post-join sum.
- On the locked (multi-thread) store path, a slot that changed between probe and store is kept when the new occupant is a different key of equal or higher replacement value. That includes an entry written by the same thread's deeper search. One-thread exclusive stores do not do this, which is why the bench signature matches. Multi-thread node counts were already nondeterministic; this audit does not claim an Elo change.
- A `ponderhit` whose steady-clock timestamp is exactly zero is treated as a hit because of the flag, and elapsed time is measured from that epoch. This host's clock was not at zero during the tests, so that single reading was not executed.
- Perft stop is checked at depth 4 and above, so the largest uninterruptible chunk is one depth-3 subtree. Depth 0 and 1 do not poll.
- `FORGE_INIT_PAUSE_MS` and `Searcher::after_main_` exist so the tests can widen the two windows. Unset, the pause does not sleep. A null hook does not run.
- Not tested: Windows, the lock's ThinLTO/PGO recipe, `FORGE_PORTABLE`, or a steady clock sitting on the epoch. No match was played.
