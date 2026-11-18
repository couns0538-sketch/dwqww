# dot Job8: incremental v3 output shadowed inside search

1. **Step0 PASS.** Unchanged r15d and kF, PC20+net768, fresh process per bench: bench11=882074 and bench13=4275906 on both; required checksum/active markers present.
2. **Hook and patch:** Worker::static_evaluate_v3 net output compared with nnue::v3::evaluate_reference on the same Board before returning raw value to search. Each variant patch3458bytes,39 inserted lines across3 files; all additions guarded by FORGE_SHADOW_EVAL. Original and patched line references below.
3. **K1/K2 PASS.** Each shadow build preserves all1000 W1 trees and16543291 nodes. Deliberately omitting a departed h1/h8-rook feature produces60580 detected differences in200 searches; first fast125/ref191. No fallback control needed.
4. **Prediction graded: all stated predictions PASS.** S1 zero differences and48.6363% calls/nodes within48–50%; S2 zero differences and42.3638% within30–80%;20 game move lists equal; S3 all1000 rows equal. Prediction unedited.
5. **Workloads:** S1 each8046050 checked net outputs,0 differences. S2 each2411437 checked outputs,0 differences across20 games/1386 searches. True-scalar S3 matches fresh original kF on all1000 depth9 rows. Table below distinguishes shadow counts from unshadowed scalar comparison.

## Timing and identity
Claim2026-11-18T16:22:17Z, commit471eb5ce56ac5a6c1f0bf5a84e3487a4ea29873a. K1/K2 complete by16:26:17Z; Step2 checkpointbc266867e9a269ca8e7246ed256bf5e2d6ae2b5b published before immutable predictionaa73ae3ae97f86e7ccd338d89d729f0ef6cbb3d6, observed16:27:16Z. S1/S2/S3 began after prediction. All native work complete16:33:13Z, including fresh original-kF S3 protocol correction. Publication/reporting follow; no experiment crossed minute50 cutoff17:12:17Z.

Pinned base commit6b98f2170a3210e71beed04bbd2553972c253ed7 with the Job6/7 documented PCr15/r15d and carbon2-final patch chain. Actual tested program SHA256s:

| Program | SHA256 |
|---|---|
| r15d unchanged |bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6|
| kF unchanged |340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea|
| r15d-shadow |e12f903e6c9de037a474547ca1687a8cb5510b9588b178620fa09b82dacf5f0a|
| kF-shadow |cc18bdcc740b2db3fccc0d148ee3623a79fef91ccdfb345f075de256afb90898|
| kF-control, deliberately wrong |12f905b6ced0ca3903d1b6689c2db95c4263f777d5675e5d4ec11a283bf0ff9e|
| kFscalar, unshadowed |c397e59ecd008a3cd13f1ef252ddf398909f425f0bfaa88981cfa40c4a84db2d|

GNU C++14.2.0, libstdc++.so.6.0.33, glibc2.41; C++20 Release O3/NDEBUG, strictFP, -march=x86-64-v4. Shadow variants add only -DFORGE_SHADOW_EVAL=1 and diagnostic patch, with scratch source/build paths. Control changes only collect_changes in a separate scratch tree. Source in the repository and original binaries were not changed.

Same synthetic hidden768 test net asJob7: checksum30ab43b4ba5db5f3, SHA256 c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7. NOT the owner's trained net. PC20, Threads1, Hash16, OwnBookfalse; every process loads NNUEArchFile then NNUEArchtrue and verifies checksum plus active line. Exact option commands and binaryhashes are in raw transcripts. No runtime/performance conclusion: reference checking is deliberately expensive and independent runs overlapped.

W1 positions are the preserved Job7 list, SHA2563c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521, generated from the authorized PGN recipe and validated there. It remains local under owner's no-data rule. Full raw UCI transcripts contain the exact tested commands. No executable, net, book, PGN, standalone position/move dataset or generated program committed.

## Step1: exact functions, independent state, and patch scope
| Role | Original kF | Original r15d | Meaning |
|---|---|---|---|
| Search dispatch |src/search.cpp:1755–1757|src/search.cpp:1284–1286|Calls Worker::static_evaluate_v3 when v3 is active; dead-material/non-net bypasses do not count as net calls.|
| Fast v3 function |src/search.cpp:3874–3939|src/search.cpp:3367–3422|Obtains raw net integer through cached/incremental/refreshed paths, then returns value.|
| Fresh reference |src/nnue_v3.cpp:762–768|src/nnue_v3.cpp:770–776|Allocates a fresh local Accumulator, refreshes from Board, then output_sum_scalar and finish.|
| UCI eval reference route |src/uci.cpp:901–911, call906|src/uci.cpp:820–829, call825|The same reference function used by eval, but now called inside search for every fast net result.|
| New comparison |patched search.cpp:3943–3954|patched search.cpp:3426 onward|Counts call, computes reference, compares integers; never replaces or changes fast value.|
| Summary output |patched uci.cpp:450–453|patched uci.cpp:365 onward|One shadow evals/differ line immediately before each normal bestmove.|

The hook is before raw value return (patched kF3965) and therefore before caller correction history/rule50 processing. For example corrected_eval is a separate routine at originalkFsearch.cpp:1887 onward. Reference uses const Net/Board plus a newly allocated temporary; it does not modify the search accumulator, cache, TT or histories. The fresh/reference and incremental paths still share feature definitions/net weights, so this is not a proof of an independently specified feature mapping.

Process-global atomic counters reset at Searcher::search entry, covering worker evaluations within one serialized UCI search. They are read after search/worker completion. First-five diagnostic counter is process-wide and not reset; additional differences remain counted but are not printed. Opening-book bypass emits zeros; OwnBookfalse in these tests. This diagnostic's counter scope does NOT support independent concurrent external Searcher instances in one process; no multithreaded test is claimed.

All additions, including declarations/resets/output, are within #if FORGE_SHADOW_EVAL. Preprocessing with the macro undefined removes diagnostic symbols; no separate macro-off executable was rebuilt, so no byte-for-byte binary identity claim. K1 establishes actual search-tree preservation when enabled on the tested inputs.

[shadow_eval.patch.txt](dot/job8/shadow_eval.patch.txt) targets kF; SHA2567e198580c27c40a145b3bc590d0e8f511cbb29ae8cde2c2cf6a53adcd2798d32. [shadow_eval_r15d.patch.txt](dot/job8/shadow_eval_r15d.patch.txt) uses equivalent r15d contexts; SHA25678db7bd81c8ec7ea8cb3742ade178bcccb0cff883f82f8620e14a8feb658236f. Both3458bytes,39 inserted/0 deleted lines in include/forge/search.hpp,src/search.cpp,src/uci.cpp; clean applications without offset/fuzz/reject. These are diagnostic text patches, not production repairs.

## Step2: tree-preservation gate and positive control
K1 uses fresh processes, PC20+net768,T1,H16, W1all1000 depth9, ucinewgame+isready before each. For each program, every row's nodes/bestmove and normalized info lines match its own Job7 baseline;16543291 nodes and8046050 net calls,0 output differences. Normalization excludes time,nps,hashfull and the new diagnostic lines. No gate failed.

K2 is a separate deliberately broken kF-shadow copy. [K2_deliberate_rook_omission.patch.txt](dot/job8/K2_deliberate_rook_omission.patch.txt),1278bytes, alters collect_changes at originalkFsrc/nnue_v3.cpp:205–213: omit at most one removal when a rook at square7(h1) or63(h8) has a matching same-piece add elsewhere in the dirty list. This excludes mere corner-rook captures; castling rook departure qualifies. Remaining columns are compacted, not left uninitialized. Only incremental consumers use collect_changes; evaluate_reference refreshes actual Board occupancy and is unchanged.

The200-row depth9 control used4064049 nodes and1666957 checked calls, reporting60580 differences and exactly five diagnostic samples. First sample:
```text
info string shadow differ fast 125 ref 191 fen r1b2r1k/4bppp/p2Np3/3pP3/P2P4/7P/4BPPK/3R4 b - - 0 22
```
No commoner fallback was needed. This proves the check detects this planted incremental fault and reaches a relevant fast path; it is NOT a discovered defect in unchanged r15d/kF. The control is never used in S1/S2/S3.

## Step3 results and prediction
| Workload | Program | Searches/games | Searched nodes | Checked net calls | Differences | First difference |
|---|---|---:|---:|---:|---:|---|
| K1 depth9 gate |r15d-shadow|1000 searches|16543291|8046050|0|none|
| K1 depth9 gate |kF-shadow|1000 searches|16543291|8046050|0|none|
| K2 depth9 deliberate fault |kF-control|200 searches|4064049|1666957|60580|fast125/ref191 above|
| S1 depth9 |r15d-shadow|1000 searches|16543291|8046050|0|none|
| S1 depth9 |kF-shadow|1000 searches|16543291|8046050|0|none|
| S2 softnodes2000 |r15d-shadow|20 games/1386 searches|5692214|2411437|0|none|
| S2 softnodes2000 |kF-shadow|20 games/1386 searches|5692214|2411437|0|none|
| S3 depth9 |kFscalar|1000 searches|16543291|not shadowed|0 differing rows|none|
| S3 depth9 |fresh original kF|1000 searches|16543291|not shadowed|0 differing rows|none|

S1 was rerun in fresh processes after prediction, not reused from K1. K1 already informed its predicted48–50% range, explicitly stated in prediction. Observed8046050/16543291=0.486363323960148. S2 observed2411437/5692214=0.4236377971734724, within30–80%. These are net-call/node ratios, not instrumented fractions of unique nodes: root/cache-related calls can be counted separately and no per-node boolean was added.

S2 node denominator comes from the explicit `info string softnodes nodes N` line, not the last completed-depth info. OriginalkFsearch.cpp:3735 sets result.nodes to total_nodes+extra_nodes, and3746–3752 emits this actual count. Every S2 search requires exactly one shadow summary and one softnodes-total line. This avoids undercounting work in an interrupted iteration.

S2 starts each of the first20 W1 positions once per program, ucinewgame+isready once pergame, then before everyply sends `position fen <start FEN> moves <moves so far>` and `go softnodes 2000`. Python-chess validates every chosen move and ends on is_game_over(claim_draw=True) or200plies. All20 games ended by game-over/claimable-draw rules; maximum125plies, none hit200. Both programs' move lists and per-search node/eval/differ counts match in all20 games. Full input/output history remains in raw transcripts; standalone move datasets remain local.

### S2 per-game results (both programs, same values)
| Game | Plies/searches | Actual nodes | Evals | Differ | Move lists equal |
|---|---:|---:|---:|---:|---|
|1|66|251033|126663|0|yes|
|2|104|439259|217232|0|yes|
|3|65|247022|112557|0|yes|
|4|81|338406|154976|0|yes|
|5|81|283603|87980|0|yes|
|6|82|357222|125972|0|yes|
|7|33|129149|54756|0|yes|
|8|64|262504|102349|0|yes|
|9|122|563911|206797|0|yes|
|10|47|214452|94440|0|yes|
|11|26|99689|37741|0|yes|
|12|21|88608|45098|0|yes|
|13|3|4275|305|0|yes|
|14|66|251033|126663|0|yes|
|15|117|512905|243056|0|yes|
|16|66|245498|112664|0|yes|
|17|52|194494|97934|0|yes|
|18|125|545972|184192|0|yes|
|19|122|479922|198919|0|yes|
|20|43|183257|81143|0|yes|

### S3: genuinely scalar v3 translation unit
Only src/nnue_v3.cpp was recompiled with appended `-mno-avx512f -mno-avx2 -fno-tree-vectorize`; all eight other object hashes remain identical to originalkF. Effective macros V3_AVX5120/V3_AVX2=0 and active line `kernel scalar` verified. No source/CMake edit; original object set copied, that one object recompiled, then relinked. This avoids Job7's ineffective ZMM-only switch.

The first scalar run was initially compared with preserved Job7kF rows. Before finalizing, I noticed the fresh-process-per-workload requirement and added a fresh original-kF S3 process, completed16:33:13Z. Final comparison uses these two fresh Job8 processes:1000/1000 rows equal in nodes and bestmove,16543291 nodes each; all normalized info/bestmove lines also agree. Both full transcripts retained. S3 is unshadowed and does not add to S1/S2 evaluation-check totals.

## Facts, suspicions, what was not done, uncertainty
Facts: hard gates passed; enabled diagnostic preserves tested trees; planted incremental error detected; unchanged shadowed programs match fresh-reference integers on every counted S1/S2 call;20 game paths agree; true scalar-v3 comparison agrees on1000 roots. All prediction ranges/results hold. No source repair or speed/strength promotion proposed.

Suspicions: no new production defect demonstrated. A passing output comparison can still miss accumulator errors hidden by rounding/clamping or defects shared by feature/reference helpers. Positive control detects one deliberate mechanism, not every possible instrumentation failure.

What I did not do: owner's trained net, other compilers/CPUs, multiple search threads, concurrent independent Searchers, broad fuzzing/sanitizers, bytewise accumulator comparison, every king-bucket/EP/castle/promotion branch counter, macro-off executable rebuild, or source changes in repository. No game-strength or speed inference from synthetic-net games.

What I am not sure about: unvisited positions/sequences, different weights exposing hidden rounding cases, and shared-feature-definition mistakes outside this oracle's independence. Reference equality is strong evidence for tested integer outputs, not universal correctness.

The PC's own net (a different file of the same kind), its compiler and processor; more than one search thread;
positions and move sequences these workloads do not reach.

## Evidence and publication
[Step0 r15d](dot/job8/r15d_gate.raw.txt), [Step0 kF](dot/job8/kF_gate.raw.txt), [Step2 checkpoint](dot/job8/step2_checkpoint.txt), [prediction](dot/job8/prediction.md), [workload summaries](dot/job8/workloads_summary.txt), [shadow design](dot/job8/shadow_design.txt), [shadow build identity](dot/job8/shadow_build_identity.txt), [control identity](dot/job8/K2_control_build_identity.txt), [scalar identity](dot/job8/kfscalar_identity.txt), [raw manifest](dot/job8/raw_manifest.json.txt), [publication log](dot/job8/publication_log.txt).

Nine complete raw workload transcripts are split into116 ordered <=100000-byte text parts; manifest gives original/part SHA256s and lengths. Concatenating each ordered part list reconstructs the original. Only raw terminal logs, patches, aggregate reports and prose/build evidence published. No standalone FEN/move datasets, net, book, PGN or program. Supporting files under dot/job8; the specifically requested REPORT_dot_job8.md path is treated as the named exception to the later general location sentence.

Publication completed and readback verified: all124 evidence files, including116 raw parts across9 transcripts. Final raw manifest and fresh-S3 summary independently rechecked2026-11-18T17:07:22Z; no publication errors or denied dataset attempts in Job8.

## Last command before report commit
```text
$ git status --short; ls -R forge-combo29/dot/job8
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job6.md
?? forge-combo29/REPORT_dot_job7.md
?? forge-combo29/REPORT_dot_job8.md
?? forge-combo29/dot/job2/K1_base_count_search_extract.txt
?? forge-combo29/dot/job2/K1_base_diagnostic_gate.raw.txt
?? forge-combo29/dot/job2/K1_base_plain_search_extract.txt
?? forge-combo29/dot/job2/K1_matrix.py.txt
?? forge-combo29/dot/job2/K1_matrix_console.txt
?? forge-combo29/dot/job2/K1_pc_count_search_extract.txt
?? forge-combo29/dot/job2/K1_pc_diagnostic_gate.raw.txt
?? forge-combo29/dot/job2/K1_pc_plain_search_extract.txt
?? forge-combo29/dot/job2/K1_summary.json.txt
?? forge-combo29/dot/job2/K2_analysis.txt
?? forge-combo29/dot/job2/K2_base_raw.txt
?? forge-combo29/dot/job2/K2_base_search_extract.txt
?? forge-combo29/dot/job2/K2_cap.py.txt
?? forge-combo29/dot/job2/K2_console.txt
?? forge-combo29/dot/job2/K2_fault_replay.py.txt
?? forge-combo29/dot/job2/K2_fault_result.txt
?? forge-combo29/dot/job2/K2_pc_raw.txt
?? forge-combo29/dot/job2/K2_pc_search_extract.txt
?? forge-combo29/dot/job2/K2_replay_count.raw.txt
?? forge-combo29/dot/job2/K2_replay_fault.raw.txt
?? forge-combo29/dot/job2/K2_replay_plain.raw.txt
?? forge-combo29/dot/job2/K2_summary.json.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_only.patch.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/manifest.sha256.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_only.patch.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_planted_overrun.patch.txt
?? forge-combo29/dot/job3/
?? forge-combo29/dot/job4/
?? forge-combo29/dot/job5/
?? forge-combo29/dot/job6/
?? forge-combo29/dot/job7/
?? forge-combo29/dot/job8/
forge-combo29/dot/job8:
K1_kF-shadow.driver.txt
K1_kF-shadow.progress.txt
K1_kF-shadow.raw.txt
K1_kF-shadow.rows.txt
K1_kF-shadow.summary.txt
K1_r15d-shadow.driver.txt
K1_r15d-shadow.progress.txt
K1_r15d-shadow.raw.txt
K1_r15d-shadow.rows.txt
K1_r15d-shadow.summary.txt
K2_control_build.txt
K2_control_build_identity.txt
K2_control_configure.txt
K2_control_design.txt
K2_deliberate_rook_omission.patch.txt
K2_kF-control.driver.txt
K2_kF-control.progress.txt
K2_kF-control.raw.txt
K2_kF-control.rows.txt
K2_kF-control.summary.txt
S1_kF-shadow.driver.txt
S1_kF-shadow.progress.txt
S1_kF-shadow.raw.txt
S1_kF-shadow.rows.txt
S1_kF-shadow.summary.txt
S1_r15d-shadow.driver.txt
S1_r15d-shadow.progress.txt
S1_r15d-shadow.raw.txt
S1_r15d-shadow.rows.txt
S1_r15d-shadow.summary.txt
S2_comparison.txt
S2_kF-shadow.driver.txt
S2_kF-shadow.raw.txt
S2_kF-shadow.summary.txt
S2_r15d-shadow.driver.txt
S2_r15d-shadow.raw.txt
S2_r15d-shadow.summary.txt
S3_kF.driver.txt
S3_kF.raw.txt
S3_kF.rows.txt
S3_kFscalar.raw.txt
S3_kFscalar.rows.txt
S3_progress.txt
S3_recipe.txt
S3_summary.txt
kF_gate.raw.txt
kf_shadow_build.txt
kf_shadow_patch_check.txt
kfscalar_build.txt
kfscalar_identity.txt
local_finding_record.json.txt
prediction.md
publication_log.txt
r15d_gate.raw.txt
r15d_shadow_build.txt
r15d_shadow_patch_check.txt
raw
raw_manifest.json.txt
shadow_build_identity.txt
shadow_design.txt
shadow_eval.patch.txt
shadow_eval_r15d.patch.txt
stamps.txt
step0_driver.txt
step0_summary.txt
step2_checkpoint.txt
workloads_summary.txt

forge-combo29/dot/job8/raw:
K1_kF-shadow.raw.txt.part01.txt
K1_kF-shadow.raw.txt.part02.txt
K1_kF-shadow.raw.txt.part03.txt
K1_kF-shadow.raw.txt.part04.txt
K1_kF-shadow.raw.txt.part05.txt
K1_kF-shadow.raw.txt.part06.txt
K1_kF-shadow.raw.txt.part07.txt
K1_kF-shadow.raw.txt.part08.txt
K1_kF-shadow.raw.txt.part09.txt
K1_kF-shadow.raw.txt.part10.txt
K1_kF-shadow.raw.txt.part11.txt
K1_kF-shadow.raw.txt.part12.txt
K1_r15d-shadow.raw.txt.part01.txt
K1_r15d-shadow.raw.txt.part02.txt
K1_r15d-shadow.raw.txt.part03.txt
K1_r15d-shadow.raw.txt.part04.txt
K1_r15d-shadow.raw.txt.part05.txt
K1_r15d-shadow.raw.txt.part06.txt
K1_r15d-shadow.raw.txt.part07.txt
K1_r15d-shadow.raw.txt.part08.txt
K1_r15d-shadow.raw.txt.part09.txt
K1_r15d-shadow.raw.txt.part10.txt
K1_r15d-shadow.raw.txt.part11.txt
K1_r15d-shadow.raw.txt.part12.txt
K2_kF-control.raw.txt.part01.txt
K2_kF-control.raw.txt.part02.txt
K2_kF-control.raw.txt.part03.txt
S1_kF-shadow.raw.txt.part01.txt
S1_kF-shadow.raw.txt.part02.txt
S1_kF-shadow.raw.txt.part03.txt
S1_kF-shadow.raw.txt.part04.txt
S1_kF-shadow.raw.txt.part05.txt
S1_kF-shadow.raw.txt.part06.txt
S1_kF-shadow.raw.txt.part07.txt
S1_kF-shadow.raw.txt.part08.txt
S1_kF-shadow.raw.txt.part09.txt
S1_kF-shadow.raw.txt.part10.txt
S1_kF-shadow.raw.txt.part11.txt
S1_kF-shadow.raw.txt.part12.txt
S1_r15d-shadow.raw.txt.part01.txt
S1_r15d-shadow.raw.txt.part02.txt
S1_r15d-shadow.raw.txt.part03.txt
S1_r15d-shadow.raw.txt.part04.txt
S1_r15d-shadow.raw.txt.part05.txt
S1_r15d-shadow.raw.txt.part06.txt
S1_r15d-shadow.raw.txt.part07.txt
S1_r15d-shadow.raw.txt.part08.txt
S1_r15d-shadow.raw.txt.part09.txt
S1_r15d-shadow.raw.txt.part10.txt
S1_r15d-shadow.raw.txt.part11.txt
S1_r15d-shadow.raw.txt.part12.txt
S2_kF-shadow.raw.txt.part01.txt
S2_kF-shadow.raw.txt.part02.txt
S2_kF-shadow.raw.txt.part03.txt
S2_kF-shadow.raw.txt.part04.txt
S2_kF-shadow.raw.txt.part05.txt
S2_kF-shadow.raw.txt.part06.txt
S2_kF-shadow.raw.txt.part07.txt
S2_kF-shadow.raw.txt.part08.txt
S2_kF-shadow.raw.txt.part09.txt
S2_kF-shadow.raw.txt.part10.txt
S2_kF-shadow.raw.txt.part11.txt
S2_kF-shadow.raw.txt.part12.txt
S2_kF-shadow.raw.txt.part13.txt
S2_kF-shadow.raw.txt.part14.txt
S2_kF-shadow.raw.txt.part15.txt
S2_kF-shadow.raw.txt.part16.txt
S2_kF-shadow.raw.txt.part17.txt
S2_kF-shadow.raw.txt.part18.txt
S2_kF-shadow.raw.txt.part19.txt
S2_kF-shadow.raw.txt.part20.txt
S2_kF-shadow.raw.txt.part21.txt
S2_r15d-shadow.raw.txt.part01.txt
S2_r15d-shadow.raw.txt.part02.txt
S2_r15d-shadow.raw.txt.part03.txt
S2_r15d-shadow.raw.txt.part04.txt
S2_r15d-shadow.raw.txt.part05.txt
S2_r15d-shadow.raw.txt.part06.txt
S2_r15d-shadow.raw.txt.part07.txt
S2_r15d-shadow.raw.txt.part08.txt
S2_r15d-shadow.raw.txt.part09.txt
S2_r15d-shadow.raw.txt.part10.txt
S2_r15d-shadow.raw.txt.part11.txt
S2_r15d-shadow.raw.txt.part12.txt
S2_r15d-shadow.raw.txt.part13.txt
S2_r15d-shadow.raw.txt.part14.txt
S2_r15d-shadow.raw.txt.part15.txt
S2_r15d-shadow.raw.txt.part16.txt
S2_r15d-shadow.raw.txt.part17.txt
S2_r15d-shadow.raw.txt.part18.txt
S2_r15d-shadow.raw.txt.part19.txt
S2_r15d-shadow.raw.txt.part20.txt
S2_r15d-shadow.raw.txt.part21.txt
S3_kF.raw.txt.part01.txt
S3_kF.raw.txt.part02.txt
S3_kF.raw.txt.part03.txt
S3_kF.raw.txt.part04.txt
S3_kF.raw.txt.part05.txt
S3_kF.raw.txt.part06.txt
S3_kF.raw.txt.part07.txt
S3_kF.raw.txt.part08.txt
S3_kF.raw.txt.part09.txt
S3_kF.raw.txt.part10.txt
S3_kF.raw.txt.part11.txt
S3_kFscalar.raw.txt.part01.txt
S3_kFscalar.raw.txt.part02.txt
S3_kFscalar.raw.txt.part03.txt
S3_kFscalar.raw.txt.part04.txt
S3_kFscalar.raw.txt.part05.txt
S3_kFscalar.raw.txt.part06.txt
S3_kFscalar.raw.txt.part07.txt
S3_kFscalar.raw.txt.part08.txt
S3_kFscalar.raw.txt.part09.txt
S3_kFscalar.raw.txt.part10.txt
S3_kFscalar.raw.txt.part11.txt
S3_kFscalar.raw.txt.part12.txt
```

This local listing includes retained structured rows, local-only records and full unsplit logs. It is not a claim that every listed file was committed. The verified publication log and manifest define remote evidence. Local checkout is not fast-forwarded to connector commits; no reset/clean was performed.
