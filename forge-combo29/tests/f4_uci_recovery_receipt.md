# End-to-end F4 UCI exception recovery

The original F4 Searcher cleanup joined workers before propagating an exception,
but the UCI worker and bench call sites did not catch it. Injected exceptions
therefore terminated the actual engine process. Recovery is now guarded by
existing default-off `FORGE_FIX_SMP_EXCEPTIONS`.

## Behavior

- The actual UCI worker catches both standard and non-standard exceptions from
  Searcher::search and emits `info string search error`.
- Fallback is the first board-ordered legal move admitted by searchmoves when
  that restriction is present. No legal admitted move yields `bestmove 0000`.
  Unrestricted searches retain the first board-ordered legal move.
- The original infinite/ponder condition-variable wait remains after recovery.
  No fallback bestmove is sent until stop or the applicable ponderhit.
- Bench catches search exceptions, prints the same diagnostic and an
  unrestricted first-legal/0000 fallback, aborts the incomplete benchmark and
  returns to the command loop. It does not publish a misleading partial node
  signature. A later bench and normal search remain usable.
- With F4 off, original call sites remain under `#else`, without catches.

## Injected tests through the actual CLI

`f4_uci_inject.cpp` supplies test-only linker wrappers around Searcher::search
and pthread_create, plus one-shot allocation failure. Static libstdc++ is
required for reliable pthread interception. There are no production test hooks.

The first created thread is the UCI worker. With Threads=3, creation of its
first helper injects a helper-local allocation failure; completion of its
second helper creation arms a main-worker allocation failure. Direct facade
injections test standard and non-standard exceptions. Bench additionally tests
an allocation failure inside its actual Searcher call.

Evidence files preserve these distinct stages:

- `f4_uci_red_results.json`: before UCI recovery, all 11 original scenarios
  abort with SIGABRT, including main/helper allocation and bench exceptions.
- `f4_uci_green_results.json`: initial unrestricted fallback passes all 11
  original recovery scenarios.
- `f4_uci_off_results.json`: F4-disabled post-change build retains all 11
  original abort outcomes. This is expected disabled-path behavior, not a
  claimed passing recovery suite.
- `f4_uci_restriction_red_results.json`: the initial fallback still passes the
  original 11, but fails all four newly added searchmoves scenarios.
- `f4_uci_restricted_results.json`: final restricted fallback passes all 15.

Every green scenario verifies exactly one injection and diagnostic, the
expected deterministic fallback, readiness, a subsequent real depth-two search,
and clean process exit. Bench cases additionally rerun a real bench. Infinite
and ponder cases verify readiness and no early bestmove before release.
The four searchmoves scenarios cover e2e4-only, explicit empty, illegal-only,
and input order g1f3/e2e4 (board order must choose e2e4).

## Reproduce

From `forge-combo29`:

```sh
tests/f4_uci_build.sh /tmp/f4-uci-enabled 1
python3 tests/f4_uci_recovery.py /tmp/f4-uci-enabled --output /tmp/f4-enabled.json
# Expected to fail the recovery suite because F4 is disabled:
tests/f4_uci_build.sh /tmp/f4-uci-disabled 0
python3 tests/f4_uci_recovery.py /tmp/f4-uci-disabled --output /tmp/f4-disabled.json
```

GCC 14, C++20, O1, debug symbols, pthread, strict FP, NNUE hidden 256,
portable slider/NNUE paths. Other review flags stay at defaults, proving the
F4 catch/cleanup path works standalone. Binary hashes and full command/output
transcripts are retained in each JSON result.

Uninjected F4-on/off smoke checks both matched bench 11 node counts 312866 with
NNUE on and 375354 with NNUE off. No timing/strength conclusion is drawn.
Full immutable-lock binary identity is a separate parent validation task.

## Explicit limits

These catches cover exceptions propagated from Searcher::search, not failures
constructing the outer UCI std::thread, startup objects, or the bench Searcher
before its search call. The test failures are one-shot; this is not a claim of
reliable recovery under persistent memory exhaustion or failed output/mutex
operations. The wrapper tests are Linux-specific; production catches and
fallback selection use ordinary C++ constructs. No production search policy or
locked constants, network or dataset were changed.
