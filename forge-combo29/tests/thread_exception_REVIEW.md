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
