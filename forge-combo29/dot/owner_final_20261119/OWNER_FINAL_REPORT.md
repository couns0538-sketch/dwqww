# Owner-final validation report

UTC 2026-11-19T01:56:30.620058+00:00

## Outcome
Completed the finite follow-up requested directly by the owner, not an Opus Job31. No genuine normal-build disagreement was observed. The last two NONE map entries now have scoped direct evidence, and H47’s previously omitted fastquiet reads are tested. This does **not** establish that every state or feature is correct. No strength/Elo or speed claim is made.

Plan/prediction commit: `3157180c420a167bb6960b8019576285bd3927df`, published before native testing. Frozen diagnostic builds extend Job30 count21 with H47F, H51 and H75 (42 counters total); wrong22 changes private reference values only. Production source is unchanged in the repository; diagnostic patches apply to scratch copies. Build/source hashes and commands are in build_manifest.txt, source_freeze.txt and build logs.

## Baseline and core verification
Six fresh original r15d/kF no-option/no-net gates each returned bench11=312866, bench13=862329, perft5=4865609. Core PC20 is Threads1/Hash16, same synthetic hidden768 net and exact settings retained from Job30. K3 uses persistent Hash1. All previous39 counters match per search; all normal42 difference totals are zero. Strict final-info comparison excludes only time/nps and preserves hashfull/PV. All six class files include all42 totals and every emitted class family.

|Phase|Searches|Last completed depth nodes|H47F uses|H47F differ|
|---|---:|---:|---:|---:|
|K1|200|4097080|1180563|0|
|K2|200|4097080|1180563|425984|
|K3_count|200|3351324|961712|0|
|S1|1000|16543291|5023977|0|
|S2|1370|4569803|1622486|0|
|S3|1412|16296118|7758168|0|

S2 emits actual softnodes5612423, distinct from last-depth4569803. S3 is20 games/1412 searches at requested hard limit20000/search, independently replayed legal histories; strict canonical matches both count21 and original r15d on every ply. H52 hard_nodes=uses=1 per search. S3 H86 continued27125973 are diagnostic events, **not UCI-reported actual hard nodes**; last-depth nodes16296118. Core native completion reported01:44:41.481550UTC. No native reruns were performed for independent QA.

## Added coverage and remaining limits
- **H47F**: actual direct Pawn-site and emit_quiets_from piece-site mask loads compared with fresh original unconditional threat recipe. Both sites and pawn/minor, rook, queen and king-empty groups reached. K2 deliberately detects exactly425984 White uses out of1180563, without changing actual search outputs. Unit is mask load, not emitted move. Shared attack primitives/formulas, not all lifetime/invalidation histories or absolute legality. Earlier H47 omissions are preserved historically, not retrospectively claimed tested.
- **H51**: emergency root fallback TT probe, not PV extraction. Four cold/primed x White/Black empty-reserve cases across r15d/kF/count/wrong agree strict canonical/legal bestmoves. Normal4 uses/0 differences; wrong4/2 exactly White. Hit/miss2/2, selected/no-selection2/2, reserve_empty4, hard_expired0. Two priming searches per engine are separate from target totals. Elapsed-hard-limit branch, concurrency/resize and all replacement states remain untested; root candidates and scalar TT reference primitives shared. Core H51 uses0 does not count as passing reach.
- **H75**: DeadMaterial-enabled60-case engine suite at depth4 compares bitboard guard against independent square-array blockers. All four binaries have16287 last-depth nodes and identical strict canonical output. H75 normal17349/0; wrong17349/8781 exactly White. All8 blocker patterns reached. H32 newly enabled reference has984 recognized/dead-return events,1214 candidate-unrecognized and3385 guard-rejected. Separate60-case direct-helper suite is60/0, wrong60/30; recognition Boolean/score matches original for all cases. Bare/single-minor roots are12 early exits with zero production helper calls; their coverage is **unit-only**, not search-reached. This is a finite guard/recognizer comparison, not independent proof of chess recognition theory, all transitions or stale bitboards. See H75_REPORT.md for all42 targeted totals and detailed classes. DefaultPC20 DeadMaterial=false remains nonreach.

## Evidence and publication
Independent raw QA: core_independent_QA.txt, H51_independent_QA.txt, H75_independent_QA.txt. Core eight-transcript SHA/byte/line manifest: core_raw_manifest.txt; targeted manifests H51_manifest.txt and H75_local_raw_manifest.txt. Reproducible harnesses and raw inputs/transcripts are local. Hunk map now has NONE0, with explicit partial/domain limits. **Raw-text archive publication is in progress, not complete.** The first900KB archive chunk was readback-verified at commit5b9d35e659b502bc8b0f3b8ec467baa3bdaa191b. See the evidence archive manifest and publication progress for verified availability; local existence alone is not an upload claim. No executable/net/book is included by this report.
