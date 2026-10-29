# Astra round 2 B4 — strict UCI metadata and option diagnostics

Base: `b7c177222038e9332965a95ec53ea3b94e90dbc9`, `origin/forge-bundle-int`.
Branch: `astra2-uci-strict`. No changes to search, NNUE, tuning values or preset composition.

IDEA_SOURCE: the user's B4 strict-UCI contract and this repository's option registry/parser.
No external engine code or tuned constants.

## Behavior

- Every one of the 64 entries in `forge::tune::parameters()` is advertised in every build. The existing
  20 SPSA parameters retain their order; the other 44 follow. Types, defaults and min/max come from
  the same existing registry. `FORGE_EXPOSE_TUNABLES` is retained as a compatibility build switch.
- `DebugSearchDelayMs` is advertised only in builds containing that test hook; release builds still
  reject its name. Its invalid-value diagnostic now matches other integer options.
- Unknown `setoption` names emit `info string unknown option <name>`; malformed commands with no
  parsed name emit the same prefix with an empty name.
- A valid `BundlePreset B1` through `B4` enables change diagnostics. A later accepted option-value
  change emits `info string override <name> after preset`. Invalid values, refused exclusive options,
  repeated equivalent values and `Clear Hash` do not claim an override.
- `BundlePreset OFF` resets the original six bundle options and clears preset tracking. An invalid
  preset neither changes options nor clears tracking. This is UCI-thread state only, accessed after
  existing `stop_search()` joins the worker threads.
- Scalar assignments use a small value-change observer without changing validation, clamping or
  setter side effects. Hash and profiling have UCI-side requested-value tracking where no getter is
  available; Threads and prefetch use existing getters. String paths use their accepted request value.
  For example, a failing Book File load leaves its old option unchanged; an NNUEFile request still
  stores its path and follows the existing fail-loud unusable-network policy.

These are unconditional protocol correctness requirements: making their advertisement conditional on a
new default-OFF option would prevent a strict runner from discovering that option's hidden parameters.
No new search feature is introduced; search defaults and the five OFF bench pins remain the contract.

## Native regression

The new Python test reuses the repository UCI process driver and compares all registered names, ranges
and defaults with the actual `uci` response. It tests exact unknown diagnostics, successful changes,
no-op assignments, clamping, invalid values, CorrHist exclusivity, buttons, preset resets, and a final
live search. It runs against both `forge` and `forge_debughooks` through CTest.

Before implementation, against the real baseline executable:

```
python3 tests/uci_strict_tests.py /tmp/forge-astra2-build-base/forge \
  --log astra2_evidence/B4/native_red.transcript > astra2_evidence/B4/native_red.log
```

Result: **150 checks, 90 failures, exit 1**. The original transcript and exit receipt are retained.
Python syntax and `git diff --check` passed after implementation. Root-owned complete native build,
GREEN runs, benchmarks, perft and CTest receipts will qualify the final implementation separately.

Only two pre-existing expectation contracts are changed explicitly:
1. `tools/uci_options_regression.py`: unknown/malformed names now produce the requested diagnostic.
2. `tools/nnue_int16_regression.py --absent`: an absent compile-time option is now reported as unknown;
   absence from `uci` and unchanged bench pins remain required.

The existing SPSA test already accepts all registered tunables, so its assertions are unchanged.

## Limits

No native fastchess executable was found on PATH or in the available workspaces; the similarly named
old plan fixture is not a match runner. An actual fastchess `-strict` invocation is **UNVERIFIED** until
one is available. The native protocol regression verifies discoverability and option acceptance directly.
No playing-strength or speed claim. Windows and sanitizer execution of this branch remain root-owned
and must be reported as UNVERIFIED unless corresponding original receipts exist.
