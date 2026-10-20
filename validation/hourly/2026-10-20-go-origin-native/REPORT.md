# Forge 6.4 — cycle 8: independent native-timing probe prepared
20 October 2026 UTC. Work branch parent: `ec013151745b524a7f7095b834ff97f75fecad2c`. The saved central lease is inactive; no Forge/fastchess processes were present in this Linux namespace. Remote jobs cannot be excluded by that observation. The original TT-tag fastchess test is terminal failed_no_resume, with 6 games/3 pairs/one Candidate timeout and no SPRT decision.

## One continued hypothesis and change
Continues cycle 7's *provisional* go-clock-origin repair, without changing production source. Source review found the first patch charged UCI admission delays to **unbounded** `go depth`/`go nodes`, `go infinite` and ponder commands, even though the intended correction concerns a timed clock. The new `uci-clock-origin-scoped.patch` only supplies `start_time` for finite clock or movetime requests, excluding infinite and ponder. Direct `Searcher::search` callers still default to worker-local start. The main search's existing ponderhit clock rebase remains untouched. Exact branch blobs inspected: `src/uci.cpp` 9bf1b757, `src/search.cpp` ca5b3541, `include/forge/search.hpp` f3f96e4b.

## Current executed evidence (Linux, not native Forge)
- Independently compiled a pthread_create LD_PRELOAD admission-delay shim with GCC and a three-mode UCI fixture with GCC/C++20.
- 440ms forced thread-admission delay, 1200ms clock: unpatched fixture first `info time`=12ms, scoped fixture=452ms.
- Unbounded `go depth 1` under identical delay: scoped fixture `info time`=12ms.
- Deliberately bad old unscoped timing fixture **failed** the new negative regression as intended: `go depth 1` reported 452ms. Scoped fixture **passed**.
- Three fixture subprocesses per probe completed with valid `bestmove e2e4`, zero abnormal exits. Original JSONL journals and stdout/stderr are retained in the local cycle archive.
- `git apply --check` plus application passed on a synthetic exact-context fixture; Python syntax and Bash syntax checked.
- The test driver refuses to overwrite existing output journals. Compiled shim is diagnostic-only, not linked into Forge.

No actual Forge executable or CMake suite was run in the local sandbox: the full exact 6.4 checkout and frozen runner binaries were unavailable here, and direct git network access was blocked by DNS. A disposable full-source Linux CMake/CTest+UCI probe driver is included for execution where GitHub Actions is available. Its pass has **not** been claimed in this report.

## Decision and next step
Time-accounting patch: **provisionally improved / unvalidated on real engine**. TT-tag correctness previously verified; TT-tag speed and strength **unknown**. Native strength acceptance: **none**. New games: **0**. Keep old failed match/orphan PGNs immutable, do not resume or pool. Next: execute disposable-tree Release CTest and controlled real-engine admission delay; if passed, separately validate timing under warmed load. Strength of TT-tag must then receive a separately preregistered native logistic SPRT H0=0/H1=5 at 10+0.1, paired openings, exactly frozen assets; no short-score substitutions.

The original blocked metadata-bearing match archive was not uploaded, repackaged, or disclosed through another endpoint.
