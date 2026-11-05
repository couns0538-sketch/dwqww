STATE: READY FOR TIMING
# B1 change 1: FORGE_SPD_TT_NOTLS (TT probe / store without the emulated-TLS lease check)

Worker b1tt (Job B part 1), started 09:18 PC clock. Status: checks (a), (b), (c1)-(c4) PASS, notes final 09:49
(plain builds; worker scratch total ~105 MB: `F:\ospd\src\b1_*` 8 x ~1.5 MB, `F:\ospd\jobb\b1` 93 MB);
switch default line `#define FORGE_SPD_TT_NOTLS 0` (one line, `include/forge/search.hpp` only).
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
Builds: the job's plain line (`-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math
-march=znver5 -static -pthread -DFORGE_EXPOSE_TUNABLES=1`, g++ 15.2 ucrt64), run inside each source copy by
`F:\ospd\jobb\b1\tools\plain_build.sh` (assert build: `nodebug_build.sh` = the same line without `-DNDEBUG`).
No build printed a warning; every exe has 0 `vfmadd`.

| exe | sha256 | what |
|---|---|---|
| `jobb\b1\lock\forge.exe` | f205cbc3... | plain build of `F:\ospd\src\lock` (reference for (a) and (b)) |
| `jobb\b1\tt_notls\s0\forge.exe` | c6bb787b... | b1_tt_notls, switch 0 (default) |
| `jobb\b1\tt_notls\s1\forge.exe` | a4a90317... | b1_tt_notls, `-DFORGE_SPD_TT_NOTLS=1` (the candidate) |
| `jobb\b1\tt_notls\count_s0\forge.exe` | 1051c894... | counter verify copy, switch 0 |
| `jobb\b1\tt_notls\count_s1\forge.exe` | 628b9ae3... | counter verify copy, switch 1 |
| `jobb\b1\tt_notls\assert_s1\forge.exe` | 78786ea4... | b1_tt_notls, switch 1, no `-DNDEBUG` |

Patch `opus_speed/patches/b1_tt_notls.patch` sha256 7c7054ca...: applied with `patch -p1` to a fresh `cp -r` of the
lock (`F:\ospd\src\b1_tt_notls_ptest`) it reproduces `F:\ospd\src\b1_tt_notls` exactly (`diff -r` empty).

**(a) switch 0 = lock: PASS.** `cmp -l lock\forge.exe tt_notls\s0\forge.exe` differs in 3 bytes only: 137, 138
(PE link timestamp) and 217 (PE checksum); log `jobb\b1\tt_notls\cmp_s0_vs_lock.txt`. Every other byte (all code and
data) is the lock plain build's.

**(b) switch 1 node identity: PASS** (`lp_check.py run` net on and `--opt UseNNUE=false`, then `compare` against the
lock plain build's runs; log `jobb\b1\tt_notls\s1\lp_pair.log`, JSONs `lp_on.json` / `lp_off.json` there, reference
`jobb\b1\lock\lp_on.json` / `lp_off.json`):
- net on: bench d11/13/16/20/22 = 312866 / 862329 / 3024920 / 12389307 / 34048354 (= pins), perft 5 startpos 4865609,
  kiwipete 193690690 (= pins), the 8 bench FENs at `go depth 13`: nodes and bestmove equal -> `NODE IDENTITY: ALL OK`.
- net off: bench 375354 / 907205 / 2448617 / 13573040 / 24506465 (= net-off pins), perft equal, 8 FENs equal ->
  `NODE IDENTITY: ALL OK`.

**(c1) counter build: PASS** (the dynamic proof). Verify copy `F:\ospd\src\b1_tt_notls_count` = b1_tt_notls plus
counters (diff `jobb\b1\tt_notls\verify_count.diff`, made by `jobb\b1\tools\make_count_copy.py`; never shipped):
calls of `has_exclusive_access()` (hea), TT probe bodies, TT store bodies past the handle check, lease
constructions and `hashfull()` calls, printed at process exit. Run: `bench 16`, then the 8 bench FENs with
`ucinewgame` + `go depth 13` (driver `jobb\b1\tools\uci_drive.py`, commands `cmds_bench16_fens13.txt`; logs
`jobb\b1\tt_notls\count_s0\run_bench16_fens13.log`, `count_s1\...`):

| build | bench d16 nodes | hea | probe | store | lease | hashfull |
|---|---|---|---|---|---|---|
| switch 0 (lock code) | 3024920 | 6,317,388 | 3,882,939 | 2,330,433 | 16 | 104 |
| switch 1 | 3024920 | 104,016 | 3,882,939 | 2,330,433 | 16 | 104 |

Both rows are exact identities: switch 0 hea = probe + store + lease + 1000 x hashfull (6,213,372 + 16 + 104,000);
switch 1 hea = lease + 1000 x hashfull (16 + 104,000), i.e. **zero calls per TT access**. The 104 hashfull calls are
the per-iteration `info` lines of the 8 `go` searches (13 iterations each); each samples 1000 clusters through
`lock_stripe` and keeps doing so with the switch on (by design: hashfull is not a hot path). Probe and store counts
and all bestmoves are the same in both builds.

**(c2) assert build: PASS.** `jobb\b1\tt_notls\assert_s1\forge.exe` = b1_tt_notls at switch 1 without `-DNDEBUG`, so
`assert(has_exclusive_access())` runs at the top of every `probe_owned` / `store_owned` call (the assertion text
`has_exclusive_access()` is in that exe and absent from the `-DNDEBUG` switch-1 exe: `grep -c` 1 vs 0). The full
`lp_check` pair ran without an assertion failure and matched the lock plain build everywhere (bench d11-d22, perft,
8 FENs at `go depth 13`; net on and net off: `NODE IDENTITY: ALL OK` twice; log `jobb\b1\tt_notls\assert_s1\lp_pair.log`).
So every owner call in those searches came from a thread that held this table's lease. (The lock's own asserts,
e.g. root-effort bounds and MoveList capacity, were live too and held.)

**(c3) Threads 1 / 2 / 4 `go depth 12`: PASS.** Driver `jobb\b1\tools\threads_go_test.py` on the switch-1 exe, one
process: Threads 1 (2 FENs) -> 2 (8 bench FENs) -> 4 (8 bench FENs) -> 1 (the same 2 FENs), `ucinewgame` +
`go depth 12` each, waiting for `bestmove` (timeout 600 s per search), then `quit`. All 20 searches reached depth 12
and returned a bestmove, the process exited with code 0, and the Threads=1 node counts after the multi-thread
searches equal those before (56720, 76930 both times: the flag and the lease are right after helpers existed).
Logs `jobb\b1\tt_notls\threads_s1.txt`, `threads_s1.uci.log` (09:25:18-09:25:21). Multi-thread node counts are not
deterministic and are not compared. Not run: the TSan CI row (no TSan on this toolchain here; CI item for the crew).

**(c4) codegen: PASS (plain build).** `objdump -d -C` of `jobb\b1\lock\forge.exe` and `jobb\b1\tt_notls\s1\forge.exe`
(listings `jobb\b1\lock\forge.dis`, `jobb\b1\tt_notls\s1\forge.dis`; helpers `jobb\b1\tools\fn_calls.py`,
`fallthrough.py`). In both exes `has_exclusive_access()` is inlined into `lock_stripe()`, which holds the
`call __emutls_get_address`.
- Lock plain: `Worker::search` calls the out-of-line `TranspositionTable::probe` (1 site) and `store` (3 sites),
  `Worker::qsearch` calls `probe` (1) and `store` (2); `probe` and `store` each call `lock_stripe` -> emutls on every
  TT access.
- Switch 1: the owner test is `cmpb $0x0,0x5b1b2(%reg)` / `movzbl 0x5b1b2(%reg)` + `test` (offset 0x5b1b2 =
  `tt_owned_`, the padding byte after `aborted_` at 0x5b1b1; `time_managed_` 0x5b1b0 and `seldepth_` 0x5b1b4 have the
  same offsets and use counts as in the lock build, so no member moved).
  - probe: owned branch -> `probe_body<false>` (179 instructions, **no call instruction at all**); not-owned branch
    -> `probe_body<true>` -> `lock_stripe`. qsearch 0x14001e094 / search 0x14001f612.
  - store (4 code paths after GCC merged the sites): each `tt_owned_ == 0` branch jumps to a block that calls
    `lock_stripe` (0x14001ee18, 0x14001f09c in qsearch; 0x140021c4f, 0x14002235c in search); each owned path is the
    inlined `store_body<false>` and walks to the entry writes with **no call** (from 0x14001ea0e: 61 instructions;
    0x14001ed0f -> 0x14001f160: 4 + 44; 0x1400219d1 -> 0x140021eeb: 76, the only call after it is the lock's
    `update_correction`; 0x140021e5d -> 0x140022467: 4 + 58).
  - So on the owned path of `Worker::search` / `qsearch` no TT access reaches `__emutls_get_address`; it stays
    reachable only on the not-owned branches (Threads > 1, Shared access), in `hashfull()` and in the lease code.
- Not verified here: the codegen of the LTO+PGO kit build. The kit's frozen v1 workload (`bench 11/13/16`, one
  thread, lease held) never executes the not-owned branch, so PGO should move it to a cold partition; check with
  objdump on the kit exe before timing (spec S4 no-go: "emutls call still on the hot path").

## Summary of checks
| check | result | log |
|---|---|---|
| patch applies to a fresh lock copy, reproduces the tree | PASS | (diff -r empty) |
| (a) switch 0 vs lock plain, `cmp -l` | PASS: bytes 137, 138, 217 only | `jobb\b1\tt_notls\cmp_s0_vs_lock.txt` |
| (b) switch 1 lp_check net on, pins + 8 FENs | NODE IDENTITY: ALL OK | `jobb\b1\tt_notls\s1\lp_pair.log` |
| (b) switch 1 lp_check net off, net-off pins + 8 FENs | NODE IDENTITY: ALL OK | same |
| (c1) counter: hea calls per TT access | 0 with the switch (104,016 = 16 leases + 104 x 1000 hashfull samples) vs 6,317,388 without | `jobb\b1\tt_notls\count_s*\run_bench16_fens13.log` |
| (c2) assert build, lp_check net on + off | no assertion; ALL OK twice | `jobb\b1\tt_notls\assert_s1\lp_pair.log` |
| (c3) Threads 1/2/4/1 `go depth 12` | PASS (no hang, no crash, exit 0) | `jobb\b1\tt_notls\threads_s1.txt` |
| (c4) objdump plain build | owned path call-free; emutls only behind `tt_owned_ == 0` | `jobb\b1\tt_notls\s1\forge.dis` |

## Risks / open items
- Code size: the switch-1 plain build carries both probe bodies as out-of-line functions and inlines both store
  bodies at every store site (Worker::search 2412 -> 2747 instructions, qsearch 809 -> 1056 in the plain build).
  The kit's LTO+PGO layout will differ; the ABBA decides (UNPROVEN, no estimate given here beyond the spec's).
- The flag relies on the lock's structure: the lease is taken in `Searcher::search` and the main worker runs on the
  same thread at lock :1522. If a later change moves the main worker to another thread while the lease stays on the
  caller, the assert build catches it (owner calls assert `has_exclusive_access()`), the `-DNDEBUG` build does not.
- `probe_owned` / `store_owned` are private; only Worker (friend under the switch) can call them.
- Not run here (coordinator / crew): kit pc1 = pc2 build, 12k-FEN identity (`fens_12k_v2.txt`), T12-03 level 3/5,
  TSan CI row, ABBA.

## Stack note (09:47, extra; not part of the brief's checks)
`b1_tt_notls.patch` then `b1_prefetch_early.patch` apply together to one fresh lock copy (`F:\ospd\src\b1_stack_ptest`;
the second patch's search.cpp hunks land at offsets 90 / 102, no fuzz). Plain build with both switches at 1
(`jobb\b1\stack\s11\forge.exe`, sha256 df63457d..., no warnings, 0 vfmadd): `bench 16` = 3024920 and the 8 bench FENs
at `go depth 13` give the lock's nodes (72062 209792 125478 51234 80137 64111 174097 85418) and bestmoves; log
`jobb\b1\stack\s11\run_bench16_fens13.log`. Not run on the stack: net off, d20 / d22, perft, switch-0 cmp.

## Disclosure
At 09:14 one scratch diff of this patch was written outside the job's write area, to Git Bash `/tmp`
(`C:\Users\Administrator\AppData\Local\Temp\b1_tt_notls_check.diff`, 12,623 bytes, identical content to the patch
body); left in place (no deletes).
