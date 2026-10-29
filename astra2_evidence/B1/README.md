# Astra round 2 B1 — protected SmpV2 port

Base: `origin/forge-bundle-int` = `b7c177222038e9332965a95ec53ea3b94e90dbc9`.
The base does **not** contain SmpV2. Its older SmpBestThread selector is a different feature.
The authoritative Forge FB2-J5 implementation used for the narrow port is
`bf6839e9e65108db76f028532dc15f9587a41fe7` (`origin/fable-fb2-j5`),
`src/search.cpp`, `fb2::smp_select_result` and the helper depth/aspiration hooks.
No unrelated J5, NNUE-v3 or other branch changes were imported.

IDEA_SOURCE: the user's deeper/equal-or-better proven-result invariant, original Forge J5 helper
diversification, and the observed Forge abort-PV mismatch. No code or tuned constants from another engine.

## Option and implementation

`SmpV2`, UCI check, **default false**. The pending option is written only after UCI stops/joins
an active search; Searcher snapshots it before launching helpers, Workers read only their copy.

With it enabled:
- Odd helpers search one ply ahead; even helpers widen aspiration windows, as in J5. Explicit
  `go mate` keeps its requested maximum depth (no helper depth skew for that command).
- Completed results with valid moves/PVs compete by strictly greater depth. Main wins depth ties.
- A main/current valid mate score of either sign, or a positive TB-win-band score while Syzygy
  score encoding is active, is replaced only by a deeper, valid proven score at least as high.
- Invalid sentinels/out-of-range scores and malformed/empty helper results are ignored.
- Node/time accounting remains the main result's accounting (including existing SmpExactNodes
  post-join summation when requested). The selected score/PV/depth is published together.
- The corrected SmpV2 selector takes precedence over SmpBestThread when both are requested;
  running the older selector first would discard the original main result before protection.
- SmpHelpersPastDepth still discards completed iterations beyond its reporting limit. SmpV2's
  one-ply helper skew is reflected in the reported completed search depth.
- BundlePreset continues to change only its six original options; it preserves SmpV2.
- Aborted iterations retain their last completed score/depth/PV tuple on **all workers**, including
  thread 0, while SmpV2 is enabled. This deliberately affects ON node/time-aborted searches even
  at Threads=1. Fixed-depth single-thread search remains unchanged. OFF retains the original
  partial-PV adoption behavior exactly.

There is no independent proof-provenance tag in SearchInfo. Protection uses Forge's existing
reserved score conventions, with TB encoding enabled only while Syzygy is active. Actual TB
files are not installed, so live Syzygy-file validation is **UNVERIFIED**. No Elo or speed claim.

## Reproductions before repairs

`historical_selector.cpp` is the exact selector function extracted from the named J5 source;
`historical_selector_provenance.txt` records its source SHA-256. It is linked to the same
selector regression test using the bundle's SearchInfo type; no surrogate ranking algorithm.

```
g++-14 -std=c++20 -O2 -Iinclude tests/smp_v2_tests.cpp \
  astra2_evidence/B1/historical_selector.cpp -o /tmp/astra2_b1_historical_test
/tmp/astra2_b1_historical_test
```

Before repair: **66 checks, 21 failures, exit 1**, original output `selector_red.log`.
After repair, the same 66 checks against the extracted production selector: **66/66**, exit 0,
`selector_green.log`; extraction retained in `candidate_selector_standalone.cpp`.
This initial standalone check does not replace the complete linked-engine test.

A second genuine production defect was reproduced before its guard was added: fresh startpos,
`go nodes 1000`, SmpV2 ON, returns depth 4 / score 30 but a **c2c4** partial PV; a fresh completed
depth-4 search returns the same score with **e2e4**. A new PV had been attached to an old score.
The native test linked the built, unguarded candidate's `libforge_core.a`:

```
g++-14 -std=c++20 -O2 -pthread -DFORGE_NNUE_HIDDEN=256 \
  -DFORGE_SMP_V2_NATIVE_TESTS=1 -Iinclude tests/smp_v2_tests.cpp \
  /tmp/forge-astra2-build-b1/libforge_core.a -o /tmp/astra2_b1_abort_red
/tmp/astra2_b1_abort_red
```

Before abort repair: **74 checks, 1 failure, exit 1**, original output `abort_red.log`.
The regression requires ON to retain the completed tuple and OFF to retain its pre-existing
node-1000 depth-4 / score-30 / c2c4 result. Snapshot/preset preservation adds six native checks.

## Complete native qualification

Root-owned build/CTest/bench receipts in this directory record the final commands and results;
never substitute the standalone unit outputs for full-engine qualification.

Relevant commands after Release build:

```
/tmp/forge-astra2-build-b1/forge_smp_v2_tests
python3 tests/smp_v2_uci_tests.py /tmp/forge-astra2-build-b1/forge \
  --log /tmp/forge-astra2-build-b1/smp-v2-uci-regression.log
ctest --test-dir /tmp/forge-astra2-build-b1 --output-on-failure -j1
```

The process test reuses the repository UCI driver and keeps the raw transcript. It covers
Threads 2 and 3, SmpV2/SmpBestThread/SmpHelpersPastDepth together, BundlePreset B1/OFF, restricted
root moves, a forced mate-in-one with coherent score/PV, option toggles during infinite search,
and an empty legal searchmoves intersection. Existing tactical and SmpExactNodes failures must
be reported separately; this patch changes no existing test expectation.

Required OFF bench pins (d11/13/16/20/22): **312866 / 862329 / 3024920 / 12389307 / 34048354**.
Required startpos perft5: **4865609**. Actual raw runs and qualification verdict are root-recorded;
unexecuted checks remain UNVERIFIED until those logs exist.
