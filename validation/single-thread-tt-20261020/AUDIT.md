# Single-worker TT lock bypass: source audit

2026-10-20. Initial read-only review of Forge6.4.11, parent-provided source
`c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`; follow-up reviews root's candidate
implementation and adds standalone validation drivers in this directory only.
This reviewer changed no engine/CMake/Git files and ran no timing experiment or
full-engine build. Later checks below distinguish actual API checks from smoke.

Initial baseline file SHA256 (inventory line references below refer to this source):

```text
include/forge/search.hpp 2b4685145205c5cb66d3a10cc3e337680f67f25df105b752f8f7f859e6d396a6
src/search.cpp d7c7bc1fc1ab807344aa78499d93c8f7866616ee514c45ac825160c2869ef8e4
src/uci.cpp 24c03dc7a24a3fb1815387e54e204208a180e1305e2262e614f7599fd753f65c
```

**Finding:** current UCI Threads1 search has one TT accessor thread. The reviewed
candidate's opt-in coarse gate, sequential stripe drain and owner-thread-only
bypass preserve coherent foreign entry access. Its original all1024-held-stripe
prototype exceeds the available TSan detector's64-lock limit and is superseded.
`workers_.size()==1` alone is insufficient: ordinary locked external probes do
not synchronize with an unprotected bypassing worker.

## Complete active-source access inventory

| Access | Current callers and synchronization/lifetime |
|---|---|
| `probe` | qsearch `search.cpp:715`, main search `:835`; takes one stripe and returns a value snapshot plus private owner/key/cluster/slot/epoch. Direct tests/audit tools also call the public API. |
| `store` | qsearch `:746,:797`, ProbCut `:948`, main completion `:1134`; checks handle, locks its original stripe, admits against the selected slot's **current** contents. |
| `hashfull` | iteration/terminal reporting `:1221`, inline on the main search worker; public `Searcher::hashfull_permille()` and direct TT stress monitor. Up to1000 stripe acquisitions per emitted iteration. No UCI input-thread hashfull call exists. |
| `prefetch` | qsearch `:776`, main search `:1046`; no entry-field loads/lock, but resolves storage pointer/count and therefore requires storage lifetime. |
| metadata | public `generation()`/`cluster_count()` (`search.hpp:119–120`), used by TT tests; `cluster_for()` reads pointer/count. Generation/epoch stay fixed throughout one search. |
| lifecycle | constructor→resize; `resize` `search.cpp:183`, `clear` `:193`, inline `new_search` `search.hpp:115`, destruction. They require **all** accessors quiescent; stripes do not make concurrent lifecycle calls safe. |
| facade/control | `resize_hash`, `clear_hash`, `clear` (`search.cpp:1398–1407`); `search` advances generation before spawning helpers (`:1419`); `set_threads` changes/deletes workers (`:1390`). Public facade exposes TT reference and main worker (`search.hpp:366–367`); standalone SharedSearchState/Worker also exist. |

`tests/tt_coherence_tests.cpp:244–289` intentionally runs two writers, two readers
and hashfull concurrently; default access must remain locked. Rule50/friend
tests directly invoke worker recursion and TT operations outside facade search.
`tests/tests.cpp:537` constructs a helper directly. Benchmarks and audit tools
use synchronous Searcher calls. Parallel book expansion constructs a separate
Searcher/TT inside each task thread (`tools/book/bookgen.cpp:391`); its Hash
clears occur between completed calls. No other active C++ TT-storage access was
found across src/include/tests/bench/tools; archived validation/release copies
are not part of this source inventory.

## Why the current UCI single-worker interval is exclusive

`uci.cpp:144–153` raises stop, notifies ponder/infinite waiters, and joins the
outer worker. That worker calls synchronous `Searcher::search` (`:354`), whose
helpers are joined before returning (`search.cpp:1427–1431`). At Threads1 the
helper loop is empty. Search output/hashfull runs on that same outer worker.

Every setoption, including Hash, Threads, Clear Hash and UseNNUE, first takes
this stop/join path (`uci.cpp:190–191`). So do ucinewgame, position, go, bench,
stop, quit and final EOF cleanup. Bench uses its own local Searcher after joining
the game worker. Book-hit responses bypass search after the old worker joins.
`uci`/`isready` only print; `ponderhit` only changes atomics/condition state.
`isready`, a stop flag, or emitted bestmove alone is not the join barrier.
Ponder/infinite may leave the outer thread waiting after search returns, but
the same join still precedes every mutation. Default Searcher destruction does
not itself stop an externally running search; UCI establishes quiescence first.

## At most two implementation choices

1. **Preferred bounded experiment: opt-in gated stripe drain.** Keep existing
   public probe/store/hashfull algorithm bodies and opaque handles. Default
   Searcher policy remains Shared; only UCI go and UCI bench explicitly opt in.
   After quiescent new_search, exact1T acquires one coarse gate, release-stores
   exclusive_requested=true, then locks/unlocks each existing stripe in ascending
   order. Publish the table-bound TLS owner only after every stripe drains.
   Owner-thread entry calls bypass synchronization. A foreign entry call locks
   its stripe, acquire-loads requested, and either returns holding the stripe
   when false or releases it, waits on the coarse gate, then retries. Never wait
   on the gate while holding a stripe. Destruction restores TLS, release-stores
   false after the last entry access, then releases the gate. Constructor catch
   clears requested before gate unwind; publish no TLS on failure. This holds
   at most gate+one stripe during drain, rather than1024 simultaneous mutexes.
   Shared/SMP callers add a TLS check and acquire flag read; fast owner calls
   avoid their per-access mutex operations. Setup still drains1024 stripes and
   may hurt tiny searches. No helper may be launched or joined under the lease.
   Stop/ponderhit never alter its context. TLS uses a lexical owner chain;
   same-table nesting reuses the prior owner and must not clear its request.
   A→B→A lookup finds A in the chain. This prevents self-reacquisition, not
   cross-thread A→B/B→A ABBA; do not promise arbitrary nested-table lock ordering.
   Document whole-search foreign diagnostic blocking, potentially until stop.
   Foreign callers must not hold locks needed by search, especially output
   mutexes. Current UCI input print commands do not access TT. The guarded
   experiment is stronger than an unprotected UCI-only worker context.
2. **Retain locks.** Choose this if the bounded lease fails correctness,
   calibrated speed is immaterial, or its fixed cost/liveness tradeoff is not
   acceptable. An unprotected UCI-only worker context has lower fixed cost but
   weakens robustness to future diagnostic callers; it is no longer preferred.

**Drain/publication proof:** an accessor that passed a false flag check before
the request must finish before the owner drains its stripe. An accessor locking
a stripe after its drain synchronizes with that unlock; requested=true therefore
happens before its flag load, which cannot observe pre-request false. It waits
without holding a stripe. On exit, the release-store false publishes the owner's
entry writes even to a newcomer that never waited on the gate. The actual code
at search.cpp:186–228 implements this ordering and the exception cleanup.

The TT skill's usual instruction is "Never hold locks across recursion or worker
joins." This design intentionally retains the coarse gate across recursion:
owner-only bypass removes recursive reacquisition, and exact1T removes helper
join deadlock. This is a narrowly justified exception. Per-call stripes still
never escape an ordinary operation or drain step.

**Lifecycle limit:** the lease is not a foreign-accessor drain barrier. A blocked
foreign probe/hashfull can resume as the lease ends, after the outer worker joins;
immediate resize/clear/new_search would then be unsafe unless that accessor also
quiesces. Probe resolves its storage reference before acquiring a stripe, and
lifecycle methods do not acquire stripes. Public metadata/prefetch also do not
wait on this lease. Retain the existing all-accessors-quiescent lifecycle
contract; claim foreign entry-call safety only while storage/generation are
stable. Current UCI exports no table reference and runs no such observer, so
its existing lifecycle proof holds. Arbitrary foreign concurrent lifecycle calls
remain unsupported.

## Required proof and validation before acceptance

- Preserve the opaque probe-time owner/key/slot/epoch handle, matching-tag
  before empty, first-empty/tie/age choices, current-slot admission, independent
  move update, rejected-score rule50 context and stale/foreign/default-handle
  rejection. Share the algorithm body; never reselect at store. Run the existing
  delayed-store/replacement tests against both shared and authorized exclusive
  contexts, plus scope restoration, owner-table identity and TLS-chain checks.
- Use an untimed test-only witness to establish that real UCI Threads1 actually
  reaches fast probe/store, while default public Searcher/Worker/direct TT
  callers and Threads2/4 never do. Otherwise unchanged benchmarks can validate only
  the fallback. Verify context restoration for terminal/restricted/zero-node,
  expired request, stop, ponder, infinite and ordinary completion paths.
- Add barrier-controlled foreign probe/store/hashfull tests: establish a live
  exclusive lease, queue callers, verify they cannot complete before release,
  then release and join every accessor before any lifecycle mutation. Verify
  coherent tuples and opaque delayed stores afterwards. Test partial-acquisition
  exception cleanup, repeated lease scopes and supported TLS-chain nesting;
  no deadlock, stale TLS or permanently held stripe is acceptable. Run these
  against the actual table under TSan, with bounded test deadlines.
- Run all9 Release and ASan/UBSan CTests, TT tuple/hashfull TSan stress, actual
  full-engine TSan with small Hash and Threads1/2/4. Exercise 1→4→1 transitions,
  stop followed immediately by Hash/Threads/Clear Hash/ucinewgame/position/go,
  repeated restarts, and isready/uci/ponderhit during active1T search. Preserve
  exact stdin/stdout/stderr and legal bestmoves. Use the existing full-engine
  driver plus explicit active-search lifecycle cases; its current option path
  quiesces before options and cannot alone test those shutdown edges. Do not
  test concurrent lifecycle misuse as if the baseline contract promised safety.
- Require exact parent-versus-candidate cold/warm1T scores, PVs, depths and nodes,
  unchanged419798 Linux/351063 Windows benchmark signatures, and the established
  Windows/Wine correctness/artifact checks. Benchmark signatures alone need not
  exercise an explicitly opted-in fast path. No changed search/rule50/clock
  policy is allowed.
- Expected value is plausible: probes at many nonterminal main/qsearch nodes
  and many stores each currently acquire an uncontended mutex, plus
  reporting samples. No call counts, saved cycles, speed or Elo are measured
  here. Measure actual opted-in UCI search only after correctness, with a fresh
  preregistered/calibrated setting; do not retry failed shared-VM/hosted noise
  profiles or alter their thresholds. Reject the speed claim if calibration
  fails or savings are immaterial. Keep the frozen649-versus651 match unchanged.

## Follow-up implementation review and executed evidence

- The original1024-held-lock smoke entered main and acquired64 mutexes, then
  GCC14 TSan emitted `CHECK failed: sanitizer_deadlock_detector.h:67` with
  `(0x40,0x40)` on the65th lock. It did not complete and hit the15s deadline.
  `TSAN_OPTIONS` was unset. Preserve `tsan-lock-smoke.*`; this is detector
  capacity failure, not a reported engine race. No check was disabled.
- The revised `tsan-gated-drain-smoke.*` holds one gate while sequentially
  draining1024 mutexes. It entered main, printed the expected completion marker
  and exited0 with default TSan settings. This establishes only lock-pattern
  compatibility, not full-engine race freedom.
- Independent real-library driver `actual-api-concurrency.cpp`, linked against
  root's gated Release core, passed all7 groups with empty stderr and exit0.
  `gated-release-v3-actual-api.json` records exact flags, input/core/binary hashes
  and deadlines; inputs stayed unchanged during compile/run. It uses public APIs
  only. A custom ostream buffer pauses the real owner at its first info output,
  after ownership publication, and actual pthread trylock EBUSY witnesses prove
  foreign probe/store/hashfull are blocked. No sleep-based assertion is used.
- Default omitted-policy1T and Exclusive-request4T diagnostics complete while
  the main worker is paused. Explicit Exclusive1T after1→4→1 blocks all three
  foreign methods until external stop/release. Owner callback checks snapshot,
  delayed slot, current admission, rule50 context and invalid default handles.
  Every accessor joins before resize/clear; old resize handles are rejected.
  Zero-node return, nested other-table ownership restoration and an injected
  ostream exception followed by successful foreign TT access also pass.
- GNU-wrap injects EAGAIN on actual owner lock call300 in the final group,
  forcing std::mutex::lock to throw during a partial stripe drain. Foreign
  probe/store/hashfull and a fresh Exclusive search subsequently succeed:
  requested-flag reset, gate release and no stale owner are exercised directly.
- Same-Searcher recursive search is not a supported way to test same-table
  lease nesting: it reenters mutable Worker state. No such call is made. The
  prototype-linked driver artifact was never executed after the header layout
  changed; its separate not-run record is retained.

Full-engine TSan, ASan and target Windows validation remain root-owned checks;
the independent driver and smokes do not replace them. No speed/Elo claim.
