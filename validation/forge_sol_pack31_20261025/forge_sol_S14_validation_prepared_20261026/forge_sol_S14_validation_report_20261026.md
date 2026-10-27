# S14 validation-only preparation report — 2026-10-26

**PREPARED, not native-qualified or adopted. No engine patch. Do not advance S14's delivered-job count yet.**

The supplied source already has fixed MovePicker arrays, fixed MoveList storage, an O(1) squares_ mailbox and in-place std::sort in the inspected GCC14 library. Existing reviewed ptype/scoring-hoist candidates are not duplicated. The distinct gap is reproducible allocation/order validation. No new speed or Elo result exists.

|Check|Status|Observed scope|
|---|---|---|
|Historical oracle provenance|PASS|Original C++99b2a12b2bfccaf087ab270cdea64828c9064b70dffd0cf9874bd699d8703023 and runner67e09b0d1f018d91770bc5cd3d3e89f544aba5b162c009754b679cabf2e9ae38 retained|
|Python parser/build initial RED|PASS controls|Missing-function stubs fail positive tests; not engine failures|
|Python suite|PASS47|Synthetic structural/build-identity fixtures; no fixture binary executed|
|Qualification-omission mutation|PASS RED4|Removing tests/support/flags/original-receipt checks makes4 negative tests fail; mutant retained, not claimed as historical/native code|
|Actual source-bound plans|PASS source/artifact identity|L/Lprime/B inventories, canonical core/main/test/support/flags/original receipt and compiler hashes checked; no compiler execution|
|Reference Std|REUSED|Pinned original S11 canonical Release evidence; not new CTest/JUnit runs|
|L core alias|PASS source proof only|All src/include hashes equal Lprime; Lp core owner explicit; no full-L-Std claim|
|C++ syntax/link/runtime|UNVERIFIED|Driver/counter not compiled or executed|
|20FEN×6mode/64-prefix native equality|UNVERIFIED|No native streams exist|
|Native allocation windows/8positive/2negative controls|UNVERIFIED|No native allocation-zero claim|
|Direct C allocation coverage|UNCOVERED|malloc/calloc/realloc/C-aligned families not interposed|
|Windows, speed, Elo|UNVERIFIED|No PC run, NPS benchmark or match; games0|

Adapted diagnostic SHA256: `43ee756193ab1899c1bd20e42fc1bf75f565cf6d3e0b7e5200e4e8d0f51a3e88`. Counter header SHA256: `e289e0c0d4ee4a25adc7f378eafa6088ab010b1f423a940cdd5cd3ce5a743e81`. Source bindings SHA256: `0c841cbb8206fffb2e98055240b8e87e340dbc8a8ef53909da88f27400a63acf`. These are diagnostic files outside every engine source tree.

Each constructor and each next() has its own thread-local entry-call window. Formatting, setup, history seeding, Board construction/FEN parsing, legality checks and make/unmake are outside. All returned moves are drained; only the first64 plus legality flags are serialized. Mailbox consistency is checked on roots and after each legal make/unmake. Positive allocation calls escape and use volatile function pointers; successful controls are required before any zero report. No universal heap-free statement follows from this limited instrumentation. Probe compilation/instrumentation can affect code generation, so results concern the named diagnostic build/windows.

The structural comparator requires distinct Lprime/B roles, exact declared source/core/workload identities, all8positive controls,120 ordered records, valid prefix/count/terminator/mailbox/window accounting and zero reported C++ allocation entries. It rejects incomplete or extra output. It cannot by itself prove that a real process produced the stream. Synthetic fixture passes are never native observations.

Qualification reuse is explicit: canonical main/core/test/support/flag/original-receipt identities are rechecked against closed S11 records. No new forge main, source change, node benchmark, perft, FMA scan or CTest result is fabricated. Lprime main remains e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b; B remains55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406. This prepares validation of existing code, not a candidate-versus-base strength experiment.

The preregister contains exact compile/runtime array references and finite limits. Next: after S11–S13 and root's native window, compile the exact diagnostic against each bound core, verify link maps, run normal plus both failing controls, preserve original evidence, and compare mandatory Lprime/B records. If a real allocation appears, investigate that demonstrated call before proposing a minimal isolated engine fix. Otherwise S14 contributes no engine code to S29. S13's frozen packet and its separate provenance addendum are unchanged.
