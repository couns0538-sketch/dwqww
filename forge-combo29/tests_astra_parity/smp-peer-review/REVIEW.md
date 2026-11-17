# Independent review of the frozen SMP softnodes amendment

PASS: no blocking finding in the reviewed native harness, controller, auditor or recorder. This is a source/metadata review with synthetic accounting checks; no chess engine or new soak batch was run by this reviewer. Production source, Git, root state and older evidence were untouched.

The reviewed rule matches Fable0017, commit8bd329545d4ad9d0ac50d8dc1dd697f14b0daa1a, SHA c6c15eb30c204424339dbad34bdebeed320440358ce9c2f5afdac3efee35848c. The entire label parser was compared byte-for-byte against the predecessor after applying only the declared signature/field additions and extra item4 clause. Threads1 retains the old expression. Threads>1 adds only exact-info nodes<2500 with valid X>=2500 when the old rule did not already pass. Runtime passes the configured thread count. The marker records reliance on the new exception; it does not replace printed nodes with X.

Strict whole-decimal nodes/X parsing, strict depth parsing and duplicate-depth rejection are unchanged. Exact versus bound-only selection, whole-line field retention, single correctly ordered softnodes line, bestmove/PV matching, score range, legality and sanitizer checks remain enforced. A malformed depth can make the new Boolean exception true while the separate parser error still rejects the search; the existing final error gate is retained. The native author's recorded46 synthetic checks passed, including T1 rejection of both observed cases, T2/T4 acceptance at X2500, rejection below2500, malformed/missingX, and unchanged item2/item3 gates. All native input hashes verified; the measured UCI transport is byte-identical.

The controller requires the explicit root smpSoftnodesResolution decision and global blockFurtherEngineWork=false; it does not clear the stop itself. New findings still block further launches. Earlier waves require passing recorded audits, so first wave[2,8] is enforced. Its new seeds are202611160103 and202611160109. All72 planned seeds are unique and disjoint from the predecessor plan. Native command bounds and aggregate-thread cap remain. All26 source files, both sanitizer engine binaries, build flags and16 objects matched the unchanged prior declaration during review.

The recorder pins original and extended predecessor namespaces by exact digests, verifies their raw/audit/package evidence, and retains failed indices2/8 with zero clean credit. Original depth64 failure and unused protocols also remain unchanged. New rows and totals use smpPairedSoftnodes, so index reuse cannot overwrite old rows. Previous clean108games/15514searches remain separately reported. Sampling-exception observations, completed-pair observations and accepted-clean counts are distinct; failed or interrupted batches receive no clean credit. State updates never clear a preexisting global stop, and source/engine pins and explicit0017 authorization are checked again before recording.

The reviewer independently reran all24 synthetic accounting tests:24 passed. These cover clean/faulted/interrupted evidence, duplicate accounting, SMP markers, invalidX, T1 rejection, historical failures and separate prior clean coverage. Six recorder pins and13 external pins verified. Exact commands/output are in ACCOUNTING-CHECKS.txt; reviewed hashes in REVIEWED-PINS.txt. PRELIMINARY-CHECKS.txt retains source, parser and seed checks. No claim is made that the amended soak has completed.

Frozen key hashes:

- native ab599afccbdd999555c4ba30c32e41d94b6a32de9ea1b13ebf4ebcaae6bc3af7
- control e5cc8336c496099d9b5b1247ac33a044069bface4de97721c695457f8229541a
- audit 5a5965605911321e4bc68a2cb96b29ddd1bc9048e494575f34fe712cd2da7ea9
- plan 5780a9e6a0c08ca2d12efeeffc806b54579560ee119c13292d48425968ed21ea
- recorder 8ebb7808c92ca68b38c2874535e70533e70e1cd8786432a4419cfdeaa9fb9c27
- accounting 8a65c7dd8db052bd133c3573377041de82516092a666c986c845a89c04eb5e82
