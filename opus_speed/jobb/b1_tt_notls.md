# B1 change 1: FORGE_SPD_TT_NOTLS (TT probe / store without the emulated-TLS lease check)

Worker b1tt (Job B part 1), started 09:18 PC clock. Status: IN PROGRESS (checks being filled in as they land).
Spec: `opus-deepres-20261104:notes/SPEC_SPEED.md` section S4 (review fixes S4-1, S4-2 applied), card T05D-01.
Patch: `opus_speed/patches/b1_tt_notls.patch` (against the lock source `F:\ospd\src\lock`, apply with `patch -p1`
inside a fresh lock copy). Edited tree: `F:\ospd\src\b1_tt_notls`. Builds and logs: `F:\ospd\jobb\b1\tt_notls\`.
No timing was done and no nps number is reported here; the coordinator's ABBA decides.

## Design (own words)
The PC toolchain emulates `thread_local`, so every read of `TranspositionTable::active_lease_` is a call to
`__emutls_get_address`. The lock's `lock_stripe()` calls `has_exclusive_access()` (that TLS read plus a walk of the
lease chain) on every TT probe and store, although in a one-worker `go` or `bench` the search thread holds the
table's ExclusiveLease and `lock_stripe()` then only hands back a deferred (unlocked) `std::unique_lock`.

With the switch at 1:
- `Searcher::search` knows when it took the lease (TTAccess::Exclusive and one worker) and that the main worker
  runs on the same thread right below (lock :1522). A scope guard sets `Worker::tt_owned_` on `workers_.front()` to
  `exclusive.has_value()` after the lease is emplaced and restores the previous value when `Searcher::search`
  returns or throws (so a nested search, which the lease's `previous_` chain allows, leaves it as it was). Helpers
  exist only when there is no lease, and their flag is never set.
- `TranspositionTable` gets one probe body and one store body, each a member template with a compile-time
  `TakeLock` parameter: `const auto lock = TakeLock ? lock_stripe(index) : std::unique_lock<std::mutex>();`.
  The rest of each body is the lock's text unchanged (entry choice, aging, replacement; the store's handle check
  stays the first statement). Public `probe` / `store` call the `TakeLock = true` body, so every other caller keeps
  `lock_stripe`; new private `probe_owned` / `store_owned` call the `TakeLock = false` body and `assert()` that this
  thread holds the lease (compiled out under `-DNDEBUG`; active in the assert build). Worker is a friend of the
  table under the switch, Searcher a friend of Worker under the switch.
- The six Worker call sites (probe: qsearch, search; store: qsearch x2, ProbCut, main) call two small Worker
  helpers `probe_tt` / `store_tt` that pick `tt_owned_ ? *_owned : *` (one predictable branch per access).
  `hashfull`, the lease code and every non-search caller keep `lock_stripe`.
- `tt_owned_` sits right after `aborted_` in Worker: it fills existing padding before `int seldepth_`, so no other
  member moves, and it shares a cache line with the per-node `aborted_` flag.

## Lines touched (all inside `#if FORGE_SPD_TT_NOTLS`, lock text verbatim under `#else`; the patch only adds lines)
- `include/forge/search.hpp`: the switch guard after the includes; TT private section after `lock_stripe` (friend
  Worker, `probe_body` / `store_body` templates, `probe_owned` / `store_owned`); Worker: `friend class Searcher`,
  `bool tt_owned_` after `aborted_`, helpers `probe_tt` / `store_tt` before `search()`.
- `src/search.cpp`: lock :246-302 (probe, store) -> `#if` new bodies + wrappers `#else` lock text `#endif`;
  call sites lock :786, :817, :868, :910, :1023, :1214; scope guard after lock :1515 (lease emplace block).
- Diff size: +152 / -0 lines.

## Why node-identical
Under the lease, `has_exclusive_access()` is already true for this thread and this table, so `lock_stripe()` returns
`std::unique_lock(stripe, std::defer_lock)`: no mutex is taken and the lock's destructor does nothing. Skipping it
removes only the TLS lookup and the chain walk. The probe / store bodies are the lock's text (same entries read and
written in the same order, same handle checks), and the flag is true only in exactly the case where the lock took
the deferred path (lease taken by this call, main worker on the lease's thread). Foreign accessors are still drained
and blocked by the lease exactly as before (the lease code is untouched).

## Checks
(filled in below as they complete)
