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
- `native_allocation_red_pinned_headers.log`: independent rerun of the same final test using unchanged
  `/tmp/forge-astra2-base/include` and `/tmp/forge-astra2-base/src` headers, again32,424/8,152.
  `base_source_pins.json` identifies the original allocator/iteration source bytes.
- `header_allocation_green.log`: corrected production inline functions, same 32,424 checks, zero failures.
  This header-only screen links the unchanged base library for tuning values, with global snapshot and actual
  Worker tests excluded. Complete native candidate target remains to be run by the parent.
- Test domain: time0..INT_MAX, increment0..INT_MAX, overhead0/10/1000, movestogo0/1/2/40/50/80, ponderfalse/true;
  factors through29.4 (maximum supported product), movetime and unmanaged searches. Final native target also
  checks real Worker allocation, immutable snapshot values and preset preservation.
- `header_ubsan.log`: 32,424 checks, zero failures and zero UBSan/float-cast-overflow diagnostics.
  Only the new inline arithmetic/test is instrumented; the unchanged library supplies tuning globals.
  This is not a full-engine sanitizer run.
- Process test: Threads1/2 clocks, huge increments, tiny clocks, movestogo1, no answer before ponderhit,
  immediate ponderhit, one legal answer, and live OFF/ON changes. Pending native run. No speed/Elo claim.

Commands (from this branch):
```
g++-14 -std=c++20 -O2 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 -DASTRA2_TM_PRE_FIX -Iinclude -Isrc tests/tm_softhard_tests.cpp /tmp/forge-astra2-build-base/libforge_core.a -pthread -o /tmp/astra2_tm_red
/tmp/astra2_tm_red
# Reproducible RED against pinned unchanged headers after candidate edits:
g++-14 -std=c++20 -O2 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 -DASTRA2_TM_PRE_FIX -I/tmp/forge-astra2-base/include -I/tmp/forge-astra2-base/src tests/tm_softhard_tests.cpp /tmp/forge-astra2-build-base/libforge_core.a -pthread -o /tmp/astra2_tm_red_pinned
/tmp/astra2_tm_red_pinned
g++-14 -std=c++20 -O2 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 -DASTRA2_TM_HEADER_ONLY -Iinclude -Isrc tests/tm_softhard_tests.cpp /tmp/forge-astra2-build-base/libforge_core.a -pthread -o /tmp/astra2_tm_header_green
/tmp/astra2_tm_header_green
g++-14 -std=c++20 -O1 -g1 -fsanitize=undefined,float-cast-overflow -fno-sanitize-recover=all -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 -DASTRA2_TM_HEADER_ONLY -Iinclude -Isrc tests/tm_softhard_tests.cpp /tmp/forge-astra2-build-base/libforge_core.a -pthread -o /tmp/astra2_tm_header_ubsan
UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 /tmp/astra2_tm_header_ubsan
cmake --build BUILD --target forge_tm_softhard_tests forge
ctest --test-dir BUILD -R 'forge_tm_softhard_tests|tm_softhard_uci_regression' --output-on-failure
```

IDEA_SOURCE: user's invariant and Forge's own allocator/iteration rule. No other-engine code or tuned constants.

## Final native qualification

Implementation commit: `97da33b7e74fe280cb3ddbe2108efee1d40f9fb1`. Complete Release build PASS.
Actual linked worker/option regression **32,433/32,433**; UCI clock/ponder lifecycle CTest PASS.
All five OFF and ON fixed-depth pins PASS: **312866 / 862329 / 3024920 / 12389307 / 34048354**.
Perft5 **4865609**, NNUE FMA **0**. Exact flags and executable hash: `qualification.json`.
All measured bench records: `BENCH_RESULTS.md`. No NPS or Elo gain claimed.

Full CTest: **55/57**, exit8. `forge_tests` has the four unchanged tactical lines. The additional
`forge_tt_mate_tb_tests` failure was its two-thread search returning centipawn scores instead of finding
mate (450/e8e4), not a false mate claim. A direct candidate rerun passed; 20 alternating baseline/candidate
repetitions all passed. An adaptive baseline-only replay (predeclared maximum200, stop on first failure)
then reproduced the same failure class on run12: untouched base score465/e8e4. This establishes that the
failure also exists in the baseline, not its root cause or comparative failure rate. Original failing full
log and every replay remain under `ctest/`, `tt_repetition/`, `base_tt_adaptive/` and `tt_mate_tb_recheck.log`.
No test expectation was weakened and the original full run is not relabelled as passing.

The bounded time-budget repair is ready for independent review. The intermittent baseline SMP mate
search needs a separate investigation. Full-engine sanitizers, Windows and strength gates remain UNVERIFIED.
J4's experimental TimeManV2 was not imported. B3 is next, on its own bundle-based branch.
