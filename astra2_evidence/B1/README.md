# Astra round 2 B1 — protected SmpV2 port

Base: `origin/forge-bundle-int` = `b7c177222038e9332965a95ec53ea3b94e90dbc9`.
The base does **not** contain SmpV2. Its older SmpBestThread selector is a different feature.
The authoritative Forge FB2-J5 implementation used for the narrow port is
`bf6839e9e65108db76f028532dc15f9587a41fe7` (`origin/fable-fb2-j5`),
`src/search.cpp`, `fb2::smp_select_result` and the helper depth/aspiration hooks.
No unrelated J5, NNUE-v3 or other branch changes were imported.

IDEA_SOURCE: the user's deeper/equal-or-better proven-result invariant, original Forge J5 helper
diversification, and the observed Forge abort-PV mismatch. No code or tuned constants from another engine.

## Review correction status

The initial implementation was checkpointed at `9d92b2f`. Its old selector/abort reproduction logs,
74-check native run, UCI transcript and bench files are retained as **pre-review evidence**, not
acceptance evidence for this corrected revision. In particular, the old node-1000 fixed-move
assertion and all-worker abort retention were rejected in review and are no longer requirements.
Historical compile commands below refer to that pre-review source/API; the corrected selector
adds a third `depth_cap` argument with a default of 64.

Review regression before correction: `review_regression_red_source.cpp`, linked against the
pre-review candidate core with the same native command as below, produced **87 checks / 4 failures**
in `review_regression_red.log`: three losing-TB protection cases and one actual Threads=1 ON/OFF
behavior difference. Current tests compare ON/OFF main results at five node caps without hardcoding
any move, score or depth, and add six abstract requested-depth boundary cases. Full post-review
native qualification is root-owned; old logs do not substitute for it.

## Option and implementation

`SmpV2`, UCI check, **default false**. The pending option is written only after UCI stops/joins
an active search; Searcher snapshots it before launching helpers, Workers read only their copy.

With it enabled:
- Odd helpers search one ply ahead; even helpers widen aspiration windows, as in J5. Explicit
  `go mate` keeps its requested maximum depth (no helper depth skew for that command).
- Results with valid moves/PVs compete by strictly greater **capped depth**. The rank is
  min(actual completed depth, requested go depth / mate-depth cap); main wins ties. Thus a helper
  at requested N+1 cannot displace a main result at N merely because of helper depth skew.
  Actual selected metadata retains its actual depth; only ranking is capped.
- A main/current valid mate score of either sign, or a TB score of either sign while Syzygy
  score encoding is active, is replaced only by a deeper, valid proven score at least as high.
- Invalid sentinels/out-of-range scores and malformed/empty helper results are ignored.
- Node/time accounting remains the main result's accounting (including existing SmpExactNodes
  post-join summation when requested). The selected score/PV/depth is published together.
- The corrected SmpV2 selector takes precedence over SmpBestThread when both are requested;
  running the older selector first would discard the original main result before protection.
- SmpHelpersPastDepth still discards completed iterations beyond its reporting limit. SmpV2's
  one-ply helper skew is reflected in the reported completed search depth.
- BundlePreset continues to change only its six original options; it preserves SmpV2.
- Aborted **helpers** retain their last completed score/depth/PV tuple while SmpV2 is enabled,
  so a partially revised helper PV cannot carry the previous iteration's proven score into selection.
  The **main worker always retains its original partial-PV policy**, including with SmpV2 ON.
  Therefore Threads=1 behavior is unchanged for node-limited as well as fixed-depth searches.
  OFF retains all original behavior.

There is no independent proof-provenance tag in SearchInfo. Protection uses Forge's existing
reserved score conventions, with TB encoding enabled only while Syzygy is active. Actual TB
files are not installed, so live Syzygy-file validation is **UNVERIFIED**. No Elo or speed claim.

## Initial reproductions before repairs (pre-review source/API)

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

A second production behavior was reproduced before the initial guard was added (the all-worker
guard was subsequently rejected in review; see correction status above): fresh startpos,
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
That original regression required ON to retain the completed tuple and pinned the OFF result.
It is preserved only in the historical checkpoint and logs. The current regression instead requires
ON/OFF **main-worker equality**, with no fixed move/score/depth assertion. Helper tuple retention
supports the protected selector without changing main-thread search policy. Snapshot/preset
preservation adds six native checks.

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
