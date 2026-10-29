# B2: soft/hard time invariant — 2026-10-29

Base: `b7c177222038e9332965a95ec53ea3b94e90dbc9`, branch `astra2-tm-softhard`.
This is a narrow repair of the bundle allocator. FB2-J4 TimeManV2 is absent from the bundle and is NOT ported.

UCI option `TmSoftHardClamp`, check, default false. ON caps the nominal clock soft allocation and the
iteration-level scaled soft deadline at the hard limit. OFF preserves the old arithmetic. This does not remove
per-node clock polling latency or scheduler delay and is not a proof that a process cannot forfeit on time.
The worker uses the existing per-search fb2 snapshot; UCI stops and joins before writes. Presets continue to own
only their six original options and preserve this independent option. The UCI watchdog gets the same requested
budget mode; the hard allocation itself is unchanged.

## Regression evidence

- `native_allocation_red.log`: unchanged production allocator, 32,424 checks, 8,152 failures. Exact trigger:
  time100/inc10000/overhead10 produces soft90/hard54; movestogo1 produces90/72.
- `ASTRA2_TM_PRE_FIX` in the same test invokes the original allocator; its scaled-deadline side uses the exact
  original iteration expression, explicitly marked in source (not a claim of a live full-engine RED there).
- `header_allocation_green.log`: corrected production inline functions, same 32,424 checks, zero failures.
  This header-only screen links the unchanged base library for tuning values, with global snapshot and actual
  Worker tests excluded. Complete native candidate target remains to be run by the parent.
- Test domain: time0..INT_MAX, increment0..INT_MAX, overhead0/10/1000, movestogo0/1/2/40/50/80, ponderfalse/true;
  factors through29.4 (maximum supported product), movetime and unmanaged searches. Final native target also
  checks real Worker allocation, immutable snapshot values and preset preservation.
- Process test: Threads1/2 clocks, huge increments, tiny clocks, movestogo1, no answer before ponderhit,
  immediate ponderhit, one legal answer, and live OFF/ON changes. Pending native run. No speed/Elo claim.

Commands (from this branch):
```
g++-14 -std=c++20 -O2 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 -DASTRA2_TM_PRE_FIX -Iinclude -Isrc tests/tm_softhard_tests.cpp /tmp/forge-astra2-build-base/libforge_core.a -pthread -o /tmp/astra2_tm_red
/tmp/astra2_tm_red
# The RED command must use the unmodified base headers; run was taken before source edits.
g++-14 -std=c++20 -O2 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 -DASTRA2_TM_HEADER_ONLY -Iinclude -Isrc tests/tm_softhard_tests.cpp /tmp/forge-astra2-build-base/libforge_core.a -pthread -o /tmp/astra2_tm_header_green
/tmp/astra2_tm_header_green
cmake --build BUILD --target forge_tm_softhard_tests forge
ctest --test-dir BUILD -R 'forge_tm_softhard_tests|tm_softhard_uci_regression' --output-on-failure
```

IDEA_SOURCE: user's invariant and Forge's own allocator/iteration rule. No other-engine code or tuned constants.
