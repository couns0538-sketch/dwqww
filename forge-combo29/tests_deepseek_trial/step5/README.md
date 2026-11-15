# Step 5 - reading the ThreadSanitizer output

## What the logs contain

Both stderr logs are empty:

```
tsan-t2.stderr.log   0 bytes   sha256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
tsan-t4.stderr.log   0 bytes   sha256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

`e3b0c44...` is the sha256 of the empty file, so these are genuinely empty and not
truncated or partially written.

**There were no TSan reports at all, so there is nothing to group.** No report
count, no stacks, no frames in `nnue_v3.cpp` or `Worker::static_evaluate_v3` to
list, and no suppression file was used (none was passed and none exists).

The job asks, for every *different* report, how often it occurred and whether a
frame lies in `nnue_v3.cpp` / `Worker::static_evaluate_v3`. The answer for this
run is "no reports", which I state plainly rather than presenting an empty table
as if it were an analysis.

## Why I treated "no reports" as a result that needed defending

A sanitizer that reports nothing because it never saw a second thread, or because
it was not linked, would look identical to a clean run. The checks below are the
reason I am willing to write "0 reports" and mean it.

| check | result | evidence |
|---|---|---|
| TSan detects a race on this machine | yes - known-race C program reports `data race` | `step5/tsan-positive-control.txt` |
| TSan runtime is in the engine binary | yes - `libtsan.so.2` linked; `TSAN_OPTIONS=help=1` prints the flag list from the engine; the release binary prints nothing | `step5/tsan-armed.txt` |
| all translation units instrumented | yes - all 9 `.o` files reference `__tsan_*` | `step5/tsan-armed.txt` |
| the v3 evaluator really ran | yes - gdb breakpoint on `nnue_v3.cpp:523` hit | `step5/gdb-v3-hit.txt` |
| it ran on helper threads, not only main | yes - with Threads=4, four distinct `Worker`s hit `Worker::static_evaluate_v3`, three with `emit_info=false` (helpers) and one with `emit_info=true` (main) | `step5/gdb-v3-helper-threads.txt` |
| the threads really overlapped | yes - node counts on one position at depth 12 grow 8002 (T1) / 29550 (T2) / 53872 (T4) | `step5/threads-node-growth.txt` |
| no search was cut off by the next command | yes - 500 `bestmove` and 500 `info depth 8` lines in each stdout log, max depth 8 | `step4/` stdout logs |

## A hypothesis about why this code is quiet, offered as a hypothesis

The transposition table is built with `FORGE_SPD_TT_NOTLS=1` (CMakeLists.txt), so
the TT is shared and not thread-local. In multi-threaded search
`Searcher::search` does **not** take the exclusive lease (`single_threaded` is
false), so each worker goes through `probe_tt` / `store_tt`, which use
`TranspositionTable::probe_body<true>` / `store_body<true>` and take the per-stripe
`std::mutex` (`lock_stripe`). The lock-free `probe_owned` / `store_owned` variants
are only reachable from the worker on the lease's own thread, i.e. a
single-threaded search. That is consistent with TSan staying silent here, and it
means a race in the TT is not expected on the multi-threaded path.

I did not prove this by instrumenting anything; it is reading the code, and it is
offered as a plausible reason for the clean result, not as a finding. I did not
judge whether any of this makes the code correct - the job asked only for what the
tool printed, and the tool printed nothing.
