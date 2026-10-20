# Forge 6.4 — 20 October 2026 — Cycle 7: UCI clock-origin hypothesis

Branch head checked before work: `87a319fdcd028ae7058036735b7e75adebfaaa84`. The saved STATE.json lease was inactive and no owned Forge/fastchess job was visible in this container. Current cloud cgroup CPU quota is 4 CPU-equivalents (cpu.max=400000 100000; effective cpuset 0-4), different from the original match's recorded 8 CPU-equivalents. No overlapping native CPU measurements.

## Source-grounded finding
In current Forge 6.4, `src/uci.cpp` receives `go`, calls synchronous `stop_search()`, parses limits and starts a worker. `src/search.cpp` starts its elapsed timer at the beginning of `Worker::search()`, *after* UCI dispatch and possible thread-admission delay. The match runner's wall clock already advances meanwhile. Therefore 351 ms of internal hard budget measured from worker entry does not bound time from the UCI command's arrival. This is a source-backed discrepancy; it has **not** been shown to cause the original 1,404 ms Candidate timeout.

## Provisional repair (not applied to engine source)
`uci-clock-origin.patch` stages `SearchLimits.start_time`, records `go_received` before dispatch, and honors that timestamp in `Worker::search`. Non-UCI callers retain their previous time origin. This is a **review-only patch**, not yet a validated engine change. Source anchors were checked one-for-one against current GitHub blobs:
- include/forge/search.hpp: f3f96e4bbd8d7c315aa1a6819b8e3dc27fe51ab6
- src/search.cpp: ca5b354137b9341f16a23e55805eed1f7681d333
- src/uci.cpp: 9bf1b757e09b5314a29101d444ae660d68b28d62

The patch's initial malformed hunk count was corrected; `git apply --check` and `git apply` passed on a synthetic exact-context fixture, not the full source tree.

## Executed checks
Linux GCC 14 standalone C++20 model with `-O2 -Wall -Wextra -Wpedantic -Werror -pthread`: PASS. A deliberately introduced 440 ms worker-admission delay yielded old worker-local elapsed=0 ms, corrected go-origin elapsed=440 ms, exceeding the frozen hard limit of 351 ms; default direct-search origin remained local. Previous synthetic UCI timeout diagnostic suite: 17/17 PASS. These do **not** validate Forge's executable, engine-time-management correctness, speed, or Elo.

The original first fastchess TT-tag test is **failed_no_resume**: 6 complete games/3 opening pairs, 1 Candidate timeout, no native SPRT H0 or H1 decision. Zero new native games this cycle; no verified Elo gain. Original frozen binaries, full metadata-bearing first-match raw archive and full tree are not locally mounted. The blocked raw archive was neither uploaded nor repackaged for publication.

## Next steps
Recover exact full engine tree/frozen binaries via existing artifact restoration, verify hashes, then apply the patch on a disposable branch and run full CMake Release tests, perft, UCI zero/short clock, ponderhit, sanitizers and controlled warm tests. A timing change can affect move selection, so do not merge without those checks. If a new matched baseline/candidate pair is needed for TT-tag strength, freeze both under a separately preregistered protocol; never pool or resume the failed attempt. Native fastchess H1 remains the strength acceptance gate. Keep all old checkpoints.

Local complete evidence with original standalone stdout, previous diagnostic stderr, commands, checksum manifest, patch and model: `forge64_cycle7_time_origin_20261020.zip` (conversation download; not a GitHub upload).
