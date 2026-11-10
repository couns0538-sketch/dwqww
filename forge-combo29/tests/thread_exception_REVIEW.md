# F4: partial helper startup terminates the process

Date: 2026-11-10 UTC. Production source tested: b6e896f0bfc05ff69cdf0d0e83eda9fa9e32b1fa.
No production source was changed for this reproduction.

## Finding and scope

High confidence, dynamically reproduced on Linux: `Searcher::search` in src/search.cpp:1827-1832 creates helpers in a vector of std::thread without an exception cleanup guard. With Threads=3, if the first helper is created successfully and the second creation throws, vector unwinding destroys an already-joinable thread and calls std::terminate. A completed but unjoined thread is also joinable. Normal joins at lines 1837/1842 are never reached.

This is an exceptional resource-exhaustion failure path, not evidence of failure during ordinary play. The test injects the POSIX error EAGAIN at the pthread_create boundary; it does not exhaust actual operating-system resources. No performance or playing-strength claim.

## Reproduction

From forge-combo29 run `tests/thread_exception_check.sh`.
Compiler: g++-14 (Debian 14.2.0-19) 14.2.0.
The script uses `-std=c++20 -O2 -pthread -static-libstdc++ -ffp-contract=off -fno-fast-math`, NNUE_HIDDEN=256, SLIDER_PEXT=0, NNUE_ZMM=0 and `-Wl,--wrap=pthread_create`. Other experiment/fix switches use source defaults. NNUE is disabled at runtime. Static libstdc++ is necessary to intercept std::thread's pthread_create reference.

Three isolated child processes test Searcher(1,3), depth=1:
1. No injection: both helpers are created and search returns normally, exit 0.
2. Fail the first helper: the outer catch receives std::system_error with EAGAIN (11), exit 42 (an intentional harness marker).
3. Fail the second helper: the outer catch is not reached; waitpid reports WIFSIGNALED with SIGABRT (6).

Core dumps are disabled in children. The parent reports success only if all three expected outcomes occur. The harness is deliberately a bug-reproduction test, not a future fixed-behavior regression: after a production fix, update its expectation rather than treating safe handling as a regression.

## Observed output

RETURNED normally fail_at=0 creates=2
OBSERVED fail_at=0 exit=0
INJECT pthread_create EAGAIN call=1
CAUGHT system_error fail_at=1 creates=1 code=11
OBSERVED fail_at=1 exit=42
INJECT pthread_create EAGAIN call=2
terminate called without an active exception
OBSERVED fail_at=2 signal=6
REPRODUCED second-helper creation exception terminates process with SIGABRT (6)

The final saved source was rebuilt and run to obtain this output. Harness exit status was 0. No production fix is included.

A future fix must ensure every successfully created helper is signaled to stop and joined on all exceptional exits while referenced local state remains alive. Merely reserving vector capacity does not handle OS thread-creation failure.

## Default-off exception-safety candidate

`FORGE_FIX_SMP_EXCEPTIONS=1` adds a stop-and-join scope around helper startup and the main search. Every successfully started helper is joined before referenced locals are destroyed. Helper exceptions are saved in separate per-helper slots and read/rethrown only after all joins. An exception from the calling thread has priority over helper exceptions during unwinding; otherwise the lowest-index helper exception is propagated. The old implementation remains under `#else`.

API behavior changes deliberately from process termination to a catchable exception. This is a correctness candidate, not a bit-exact claim for exceptional runs. The caller still needs an appropriate exception handler. Internal cleanup uses helper_shutdown and never overwrites external cancellation. The exception switch is defined in search.hpp and independently enables the internal latch field/check/reset, even when the separate stop-latch switch is off. Ordinary consecutive searches need no newly imposed reset_stop call. A preliminary committed version used shared.stop when the stop-latch switch was off; review identified that ordinary-reuse side effect, and the follow-up correction removes it.

Updated startup tests count successful joins. Run:

- `tests/thread_exception_check.sh /tmp/f4-off`
- `tests/thread_exception_check.sh /tmp/f4-on -DFORGE_FIX_SMP_EXCEPTIONS=1`
- `tests/thread_exception_check.sh /tmp/f4-on-latch -DFORGE_FIX_SMP_EXCEPTIONS=1 -DFORGE_FIX_SMP_STOP_LATCH=1`

All three configurations passed their configured expectations. Baseline still reproduces SIGABRT (6). Both enabled configurations propagate system_error EAGAIN (11): first failure after 0 joins, second failure after exactly 1 join. Normal controls create and join both helpers.

Additional test: `tests/thread_exception_workers_check.sh` (equivalent individual compile/run commands executed). It injects a single bad_alloc during the main search call or inside one helper's search-call argument copy, without production hooks. Both latch modes passed:

- `PASS main allocation exception propagated after 2 joins`
- `PASS consecutive searches reusable without reset_stop`
- `PASS helper allocation exception propagated after 2 joins`
- `PASS consecutive searches reusable without reset_stop`

These injection tests cover exception propagation and cleanup, not every possible allocation site, OS join failure, or engine-state recovery after arbitrary deep-search exceptions. No sanitizer was used for these static-libstdc++ exception harnesses. Full lock pins and independent review remain separate gates; no promotion or speed claim.

Compatibility regression also passed with all four SMP fixes enabled:
`tests/run_smp_nodes.sh /tmp/forge-f4-smp -DFORGE_FIX_SMP_EXCEPTIONS=1 -DFORGE_FIX_SMP_STOP_LATCH=1 -DFORGE_FIX_SMP_NODE_RESET=1 -DFORGE_FIX_SMP_FINAL_NODES=1`, followed by `SMP_NODES_FINAL=1 /tmp/forge-f4-smp` and `SMP_STOP_JOIN=1 /tmp/forge-f4-smp`.
Observed: stale helper counter reset PASS; post-join returned=42 PASS; external stop during join remains latched until explicit reset PASS.

After the standalone-latch correction, all three startup configurations, both worker-exception latch modes and the all-four-SMP compatibility tests above were rebuilt and rerun successfully. The worker harness now explicitly requires two consecutive nonzero-node searches without reset_stop after each injected exception. Production source is identical between these final focused tests and the parent team's combined-pin candidate (apart from any later, separately recorded work).
