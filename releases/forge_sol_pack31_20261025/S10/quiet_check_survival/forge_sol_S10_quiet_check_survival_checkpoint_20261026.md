# S10 QuietCheckLmpSurvival checkpoint — 2026-10-26

Decision: **REJECTED search screen; not adopted.** The single original WAC ON run solved269/300, below the fixed283 requirement, with0 illegal moves. It was not repeated. The two-source correctness qualification completed. No speed or Elo claim.

The hypothesis retained legal quiet checks after ordinary quiets had been pruned by MovePicker. The standalone patch remains build-OFF and UCI-OFF by default. Patch SHA256 `2c195c2d15f044128b68a2efc39500314b3310f551c53980b9965773358089e3`; original controller SHA256 `d6b8b9909373903e2ac3d2aca10e731acffeaff8352db8619d0577945f55b08b`.

|Depth|OFF both bases|ON both bases|
|---|---:|---:|
|11|308972|342968|
|13|745494|913565|
|16|2460422|2423687|
|20|11901452|10956860|
|22|31111774|27358618|

The registered deep20% node guard passed. d13 increased22.54%; all observed values remain visible. Node counts do not establish speed or playing strength.

|Check|Lprime|B|
|---|---|---|
|FIRST bare OFF d11 before UCI|308972 PASS|308972 PASS|
|Release full configured CTest|14/14,4 known,0 new|15/15,4 known,0 new|
|ASan/UBSan full configured CTest|14/14,4 known,0 new|15/15,4 known,0 new|
|Release perft5 start / kiwi|4865609 /193690690|4865609 /193690690|
|Scoped NNUE ELF/object FMA counts|0 /0|0 /0|
|Compile-OFF production preprocessing|All8 TUs exact bytes/tokens|All8 TUs exact bytes/tokens|
|ASan FIRST /OFF /ON d11|308972 /308972 /342968|Same|
|Supplement ON/T2 ASan|3 legal searches PASS|3 legal searches PASS|
|Source/runtime artifacts|Unchanged|Unchanged|

Full CTests exercise their default-OFF configuration. ON code also passed the five-depth Release sweep, ASan d11 and the bounded T2 supplement. Leak checking remained enabled; the supplement observed unlimited RLIMIT_AS before and after execution, without a setter. It replayed the original full CTest inventories/JUnit before launching. The exact one active marker appeared before the first of three bestmoves in each drained T2 transcript.

A non-monotonic reported node-counter sequence in the original T2 trace has been recorded for S22. Its root cause is UNVERIFIED; no race, timing-forfeit or causal attribution is claimed here. The original trace is preserved without a rerun or engine change.

Original data transport:397 files,129,342,967 bytes, including commands, raw streams, CPP proofs, JUnit, generated recipes and hashes. All398 archive members including the mapping were independently verified through Python and GNU decoding. Private engine source trees, build ELFs, objects and archives were excluded from this transport and remain intact locally.

Archive `forge_sol_S10_quiet_check_survival_evidence_20261026.tar.gz` —16617977 bytes; SHA256 `aa45a3b35995837eff8791295657a239434cd54f4e9e72e9fb237e882570fa40`. Mapping SHA256 `5e6e523f49e7d7895ea83f401e54faa77a49af3cc5400e3a1f83b89cd415a374`. Receipt SHA256 `25c31b01bcb86c9fafc32e725960f4d2dfe9fd0568ed30c8c8d245e68f90ffec`. Source/script/review files are standalone small artifacts; publication remains root-owned until actual GitHub retrieval is verified.

Windows, owner-PC performance CI and playing-strength gates remain UNVERIFIED. No matches were run. The next frozen S10 experiment is ImprovingRazorGuard; its original Lprime run is active.
