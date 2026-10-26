# S13 child TT prefetch — source preparation, 2026-10-26

**PREPARED; native qualification UNVERIFIED. Not adopted.** No compiler, engine, sanitizer, timing or match ran for this job. Do not advance the delivered-job count from this source preparation.

Patch `forge_sol_S13_ttprefetch_20261026.patch`, SHA256 `cc3efc9659a00e2b2da8c4853f7c1c2f601e95e16e1805bc2cbf8cc4b91a249a`. Six files,61 insertions,0 deletions (four production/build files plus additive README/IDEA_SOURCE notes). Applies to supplied L/Lprime/B. Source lock1ab50b2dd64d9b2f752f7f1285f6968cad2fd792; net SHA25674c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b remains unchanged.

The original already prefetches after qsearch/main make and already asserts TTEntry16/TTCluster64. The only new prefetch requests are immediately after null-move and ProbCut make. Parent-key restoration resumes an existing search frame and probe handle; no redundant prefetches were added after every unmake. Existing TT layout, coherent access, score context, replacement and lifecycle are unchanged. No NNUE/value/move-order/tuned-constant change and no allocation in make/unmake.

`FORGE_S13_TT_CHILD_PREFETCH` and UCI `TtChildPrefetch` both default OFF. The requested flag is atomic, captured once into immutable search limits before helpers start; each worker uses its own copied bool. ON announces `info string TtChildPrefetch active` once per Searcher facade. The UCI bench facade inherits the chosen option. Public CMake definitions keep headers consistent. Build-OFF guard erasure exactly restores the original four production/build files on all three bases.

|Check|Status|Evidence/limit|
|---|---|---|
|New source contract on unfixed base|PASS RED control|Original exit1: missing OFF build switch; not a native result|
|Original pure source suite|PASS8|Source only|
|Independent source review|PASS with minor proof gap|No production blocker; old guard checker hid alternatebranches|
|Guard-checker mutation controls|PASS RED2 then GREEN10|Oldchecker preserved; fixed checker rejects #else/#elif; no enginepatch change|
|Independent re-review of checker fix|UNVERIFIED|Follow-up tool refused with agentthreadlimit; root review pending|
|Git check/GNU dry/GNU actual `-p1 -F0`, L/Lprime/B|PASS9|Successor uses `--no-backup-if-mismatch`; exact applied bytes verified|
|Canonical inventories/network unchanged|PASS|75/77/78 files; only6 intended private paths changed|
|Build-OFF exact source erasure|PASS|Four files on all3 bases; not compiled CPP/ELF evidence|
|Full Release/perft/FMA/5-depth OFF and ON|UNVERIFIED|Required fixed node refs308972/745494/2460422/11901452/31111774|
|Full ASan/UBSan + leak + ON T1/T2|UNVERIFIED|Must keep original14/15 inventories and4known diagnostics only|
|Actual-source request-count diagnostic|UNVERIFIED|Written, not compiled; one worker/four fixed FENs/d10|
|Hardware prefetch execution/CPU speed/PC eligibility|UNVERIFIED|No measurement/claim|
|Equal-time matches/Elo|UNVERIFIED|Games0; no strength claim|

The initial nine application commands all passed, then their inventory observer failed because GNU patch created `B/src/search.cpp.orig` for an offset hunk. Raw logs/trace, original helper and private backup are retained. The backup equals original B search.cpp exactly. The successor explicitly prevents such backups and completes all nine source checks. This was an observer failure, not an engine failure. The original checker and its two failed mutation tests also remain in this packet.

The deferred C++ diagnostic includes actual search.cpp, replaces its builtin prefetch only for request counting, and links the same ON core with a map that must exclude archive search.cpp.o. It compares actual OFF/ON moves/scores/PV/depth/nodes and null attempts. ProbCut requests are derived from total extra requests minus matching null attempts, not directly traced. It proves neither hardware request completion, SMP behavior nor speed. Its negative mutation removes only the two added calls while retaining the option and must fail coverage. Both runs remain UNVERIFIED.

Exact deferred build/FIRST/bench/perft/CTest/ASAN/probe command templates, frozen FENs, resources and acceptance limits are in `forge_sol_S13_native_preregister_20261026.json`. Substitute NEW isolated views/builds only after the ordered S10/S11/S12 work and root native grant. Every new engine main must receive bare bench11 first. No PC/GPU access or plugin installation is claimed. Next: native S13 qualification, then advisory timing only if correctness closes. No adoption from this source-only packet.
