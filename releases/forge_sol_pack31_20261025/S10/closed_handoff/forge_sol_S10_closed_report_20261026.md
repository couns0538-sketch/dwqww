# Forge Sol S10 closed report — 2026-10-26

All four original frozen search experiments have completed their registered screens. **All four are rejected and remain OFF by default; no accepted engine change, speed gain or Elo gain is claimed.** Accepted source remains `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`, network MD5 `6d22f612c855e17c62d396d32da99ea4`. No NNUE/net format, evaluation-value, TT or move-ordering patch is included. Supplied S10 idea-board/source audits were used as ideas only; each independent patch adds its provenance to IDEA_SOURCE.md and README. Existing RefutLmr P23b, QsEvasionSeeNonPv P27R and timepack2/3/4 were excluded.

|Feature|One original ON WAC|Deep-node guard|Lprime full Std|B full Std|Decision|
|---|---:|---|---|---|---|
|QuietCheckLmpSurvival|269/300|PASS|PASS Release+ASAN14/14 each|PASS Release+ASAN15/15 each|REJECTED|
|ImprovingRazorGuard|270/300|FAIL d20|PASS Release+ASAN14/14 each|FAIL bounded OFF22 attempt; remainder UNVERIFIED|REJECTED|
|SingularSiblingLmr|263/300|FAIL d20|PASS Release+ASAN14/14 each|PASS Release+ASAN15/15 each|REJECTED|
|CaptureHistoryLmp|258/300|FAIL d20,d22|PASS Release+ASAN14/14 each|PASS Release+ASAN15/15 each|REJECTED|

The registered WAC floor was283/300 at1000ms/position. Each feature had exactly one Lprime screen; no B screen or retry was run. All1200 original WAC searches returned legal moves. WAC scores and node counts are screening evidence, not equal-time Elo measurements. There were no fastchess matches or PGNs.

|Depth|Fixed OFF reference|QuietCheckLmpSurvival ON|ImprovingRazorGuard ON|SingularSiblingLmr ON|CaptureHistoryLmp ON|
|---|---:|---:|---:|---:|---:|
|11|308972|342968|301162|336273|304755|
|13|745494|913565|785078|708742|813494|
|16|2460422|2423687|2851256|2814343|2591604|
|20|11901452|10956860|9011938|14837257|8234313|
|22|31111774|27358618|25347487|32299567|23665760|

All completed full cases matched all five fixed OFF references. All three complete B cases matched their Lprime ON counts. Improving-razor B matched OFF11/13/16/20 and ON11=301162 before its original OFF22 observer deadline expired; it produced no completed d22 summary. The timeout receipt is181.674795928s with owned SIGTERM returncode−15, empty stderr, drained capture and no remaining group members. No spontaneous crash, engine clock defect, d22 NPS or root cause is inferred. No source/timer change or retry rescued that case. Its remaining full Std/perft/FMA/ASAN/T2 checks are UNVERIFIED. The other two later default OFF22 cases completed normally.

Seven source cases completed the entire Release and ASan/UBSan configurations: four Lprime and three B,202 configured CTest case executions total. Each full inventory passed with exactly the four pinned known diagnostic lines and zero new FAILs. Their startpos/kiwipete perft5 counts were4865609/193690690. Scoped NNUE ELF/object FMA counts were0 in both profiles; no FMA-contract/fast-math changes were permitted. Eight production translation units per complete case proved compile-OFF token equality with the matching original source. Every new main ELF's first execution was bare bench11 before UCI, returning308972. All source and recorded runtime-artifact hashes were unchanged at closure.

The approved v2 ON/Threads=2 ASan supplement passed for all seven fully qualified cases:21 legal search/ponder checks, typed ON option and exactly one active marker before first bestmove, drained normal EOF, empty sanitizer stderr, and unchanged sources/artifacts. Leak checking remained enabled. Unlimited RLIMIT_AS was observed before and after, with no limit setter. The retired v1 supplement and its red controls/review are retained; it was not run on an engine. V2 review `d936207ef9d9f6496f62039fa681b9ad467ff1fa3faf191935ae977887f75659` and nine green controls bound the final adapter.

Execution was sequential onCPU2/nice19. The unchanged limits were2400s/case and180s/component. GCC14.2 SHA256 `6b3696e4dcb85e1c949c732a02befa50e3983ecf94ce7e8e58d9d503b954b79d`; flags `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`, LTO OFF. Frozen controller SHA256 `d6b8b9909373903e2ac3d2aca10e731acffeaff8352db8619d0577945f55b08b`. Full exact command lines, compiler outputs, build recipes, JUnit, source/protocol hashes and original UCI/WAC streams are in the corresponding data archives. No owner-PC/Windows execution, speed comparison or strength acceptance has occurred.

The capture-history WAC window has a separate execution-condition annotation: a root Git upload begun before the exclusive-window warning may have overlapped its start. Successful upload completion was observed21:30:15UTC; actual completion/CPU phase are UNOBSERVED. No repeat was run and no tactical effect is attributed. That candidate already failed both registered deep-node limits before WAC. See the retained dated execution-condition sidecar.

|Patch|SHA256|Diffstat|
|---|---|---|
|forge_sol_S10_quiet_check_survival_20261026.patch|`2c195c2d15f044128b68a2efc39500314b3310f551c53980b9965773358089e3`|0 files,+66/−1|
|forge_sol_S10_improving_razor_20261026.patch|`398a1bdac9606dea0b0b1b938dcd8e6ec7e6b8674435aee3584c3af6c8eda286`|0 files,+61/−1|
|forge_sol_S10_singular_siblings_20261026.patch|`83b9e88b25347cf862761e54c1447d4f4edeccb1582c85dc6f5aff68d2712668`|0 files,+66/−0|
|forge_sol_S10_capture_history_lmp_20261026.patch|`f7e9bf21fc8e80244545012f458024f7f42738cca22f498180d762408966ad63`|0 files,+63/−0|

Each patch has its own compile-OFF and atomically stored UCI-OFF option; worker snapshots avoid reading a mutable option. Applications/checks to L/Lprime/B and original-source preservation were frozen before native execution.18 preparation controls and36 Git/GNU application/check operations passed; original failed helper attempts and all reviews remain in the prepared checkpoint.

- QuietCheckLmpSurvival: When late-quiet pruning has activated, retain legal quiet checks while dropping other quiets. The existing futility check exemption cannot recover moves already skipped by the picker.
- ImprovingRazorGuard: Do not razor a non-PV node whose static evaluation is improving. Preserve the existing razor margin and qsearch fallback for other nodes.
- SingularSiblingLmr: After a TT move proves singular, reduce its later non-checking quiet siblings by one additional ply at non-PV nodes. This does not alter the singularity test itself.
- CaptureHistoryLmp: At shallow non-PV nodes, prune late captures only when their capture history is negative, SEE is losing, and the move neither checks nor promotes. Reuse the existing history-prune depth and LMP count thresholds.

|Sealed original-data archive|SHA256|Bytes|Original data files|
|---|---|---:|---:|
|forge_sol_S10_quiet_check_survival_evidence_20261026.tar.gz|`aa45a3b35995837eff8791295657a239434cd54f4e9e72e9fb237e882570fa40`|16617977|397|
|forge_sol_S10_improving_razor_evidence_20261026.tar.gz|`4b5322ac6ed3341604e771e6872c2ec0e5838b6bff99462b9b4679d1d8c4284e`|8430332|260|
|forge_sol_S10_singular_siblings_evidence_20261026.tar.gz|`88c64edd7498445e8254453a4479492a944b10354a88860f5aa20b0f2c0d5227`|16620161|397|
|forge_sol_S10_capture_history_lmp_evidence_20261026.tar.gz|`59f0436d68caa260f2eb11a1d738a799248016f85e3f4c80e7f0b63db1714ee0`|16616405|397|

The four data-only archives preserve1451 original files/453349179 bytes. Complete original→member mappings include SHA256/size. Both Python and GNU decoders verified every member byte, and original files were rehashed unchanged. Private source trees, ELFs, object files and caches are excluded from publication encoding, remain intact locally, and were not deleted. Source patches/controllers/tests and concise reports are separate small artifacts. Root owns publication; local sealing is not a remote-publication claim.

The source/result/archive SHA256 map is `forge_sol_S10_consolidated_results_20261026.json` (`a5ad73d081ec5680f9d4d00315f9a3949d3084f02f4060894d85378cbe73b78f`). It explicitly marks the partial B failure and all unrun checks. The batch checkpoint is `/tmp/forge_sol_S10_native_20261026/forge_sol_S10_native_batch_20261026.json`.

Next: root publishes and verifies the final S10 source/evidence/checkpoint, retaining all four rejected patches separately. Resume the already-frozen S11 always-on material-history-key experiment only after a separate native grant. Its first meaningful gates are the actual C++ algebra/API oracle and fixed-node full Std; native1M scalar/AVX parity and any advisory ABBA remain UNVERIFIED. Do not revisit S10 thresholds/results or repeat the completed WAC investigations. A future default-d22 resource policy must be separately preregistered for a new case, not applied retroactively.
