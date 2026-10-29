# Round 3 F6 — nominal search-depth metadata

IDEA_SOURCE: the user's code-review F6 request and Forge's existing iterative-deepening/SmpV2 result flow; no external engine code or tuned constants.

This change records the last completed iterative-deepening loop depth before SmpV2 helper skew. `SearchInfo::depth` continues to mean actual searched depth. The SmpV2 selector still ranks capped actual depths; no ranking, search, abort, option, or UCI-output policy changes.

## Source changes

- `include/forge/search_types.hpp:75`: append `nominal_depth = 0` after existing members (including conditional lazy-accumulator statistics). Zero means no completed iteration. This changes the type's size/ABI: rebuild core and all dependents together; do not link a newly compiled test to an old core.
- `src/search/iterative.inc:93`: terminal/adjudicated-root iterations report their nominal depth.
- `src/search/iterative.inc:227`: completed ordinary/helper iterations record the loop depth separately from `search_depth`. The existing past-limit helper behavior and aborted-main partial-PV behavior remain intact.
- `src/search/searcher.inc:162`: the legacy SmpBestThread manual result copy also copies nominal metadata. SmpV2 already copies the complete result object.
- `tests/smp_v2_tests.cpp`: synthetic selector checks now verify metadata transfer; a helper with actual 13 / nominal 11 beats a main with actual 12 / nominal 12 at cap 14, but ties and loses to main at cap 12. Native tests exercise fresh direct workers (helper 4/3, main 3/3, terminal helper 3/3, zero-budget 0/0) and extend existing fresh ON/OFF node-cap comparisons to nominal depth. No expected chess move or evaluation was added.

## Tests-first evidence

Exact command for both syntax runs (working directory: repository root):

```sh
g++-14 -std=c++20 -fsyntax-only -DFORGE_NNUE_HIDDEN=256 -DFORGE_SMP_V2_NATIVE_TESTS=1 -Iinclude tests/smp_v2_tests.cpp
```

- `nominal_depth_red_syntax.log`: exit 1, exclusively absent `SearchInfo::nominal_depth` diagnostics after adding the tests and before adding production metadata.
- `nominal_depth_green_syntax.log`: exit 0 after the production change.
- `nominal_depth_source_sha256.txt`: exact source snapshots at the implementation handoff.

The syntax failure is a missing-metadata contract regression, not a runtime chess failure. Native execution, full build, CTest, OFF benchmark pins, perft and sanitizer qualification are **UNVERIFIED by this implementation handoff** and assigned to the parent integration runner. The new native test is expected to report 108 checks when it executes, but that count has not yet been observed. SmpBestThread's private manual-copy path is covered by source review and existing integration lifecycle tests, not a newly added private-access test.

No Elo, speed, playing-strength or benchmark-identity claim is made here.
