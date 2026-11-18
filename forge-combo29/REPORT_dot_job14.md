# Dot Job 14

## 1. Step 0: PASS
Unchanged r15d SHA256 bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6 and kF 340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea, no options/no loaded net, fresh process per command: both bench11=312866 nodes, bench13=862329 nodes, go perft5=4865609 nodes. Six raw logs committed under dot/job14.

## 2. C-count5: patch, SHA256 and corrected clean build
C_count5_full.patch.txt SHA256 f86499a829e8a2af952f1c2a5f61d550e628b93029d1774e2c380f37bc5f49a9; C_wrong5_full.patch.txt SHA25698a324d87042ebbbe3ed57743e99fb65e48591b2365e52e8baa37b85bd0dc5a5. Full patches apply to original kF; incremental fromJob13 also provided. Engine repository source untouched.
Final C-count5 SHA25614e0a5935fcde67fae88fb300c4428be2bd915ca4492cd708ddbf9619d766779; C-wrong5 SHA2563f3b04ca1264bb61c7a6f733e8e39be5642942daaeedc15f0db8423e41bfa85f. Both clean-first builds frozen19:49:13 UTC, GCC14.2.0/CMake4.4.5/libstdc++.so.6.0.33/glibc2.41, C++20 Release O3 NDEBUG, strict FP, march=x86-64-v4; full flags in build_manifest.txt. Old four fault macros disabled, WRONG5 only in control.

### Pre-prediction build correction, not concealed
The initial count binary d244cf9ebda40cbcd22275bcbfc1bcb561bfd5f8c94c5527b5a6bedbd8d522e6 contained a stale inline older-generation classification after a header edit while search.cpp was compiling. Its object finished after the header timestamp, so incremental rebuild skipped search.cpp. The count's preclean K3 older_generation2662552 disagreed with wrong's1105870 despite identical tree/uses/other classes. Both frozen sources were rebuilt --clean-first, without further source edits; count hash changed, wrong hash remained unchanged. All gates rerun before prediction; corrected classes agree at every search. Original binaries remain local, complete preclean transcripts preserved with suffix _preclean, old hashes and incremental/clean logs disclosed. No preclean aggregate used for final normal-build conclusions. Core nodes/bestmove/old-counter gates had not failed; this ancillary class-consistency check caught an instrumentation-build problem.

### Reference scope
H82 reference and class semantics (source-only before native gates).
Every owned fast probe (header SIMD and scalar branches), locked fast probe, owned fast store and locked fast store receives one H82 comparison. Probe reference copies pre-call cluster by value then plain-scans first matching occupied key, first empty, otherwise strict-min(depth-4age), retaining earliest ties. Compare actual hit/miss and selected slot. Store reference plain-scans pre-call first matching occupied key; absent key selects originally supplied probe slot exactly as r15d store_body, not newly computed replacement. Compare actual candidate entry address and whether it matched key. This observes chosen write target before admission; rejected stores still count a use. Existing H18 separately checks resulting cluster payload.
Classes use pre-call snapshot before deliberate faults. hit = any occupied matching key, miss_empty = no key hit and at least one empty, miss_full = no key hit and all4 occupied. The three partition all H82 uses, combining probes and stores. probes/stores are also printed and partition uses. older_generation is overlapping: probe HIT on occupied entry whose generation differs from current; OR store selected occupied entry of differing generation (which old-generation admission rule admits). A full-miss probe selecting old victim does NOT increment older_generation, because it neither hit nor wrote it.
Wrong5 changes reference slot to(slot+1)&3 only miss_full, including both full-miss probe and full-miss store cases; no hit/miss/class/current-generation state changes. Thus all fullmiss comparisons should differ, other classes unchanged. Actual lane masks, selected pointer, admission, TT payload, generation counters and search values unmodified. Old WRONG,WRONG2,WRONG3,WRONG4 undefined. All12 previous counters still require native equality gate.
Diagnostics share process-global first5 cap, include current FEN via pre-existing RAII BoardContext, store move or0000 for probe. H82 records only synchronous Worker-context operations; direct external TT API calls outside Worker not counted. No multithread proof, stale/foreign-handle guard validation, sample-generation delta proof, absolute hash correctness or unseen-cluster guarantee. Scalar oracle shares occupied/generation/key32 helpers but not SIMD lane masks. Owned helper index arithmetic unchanged, key32 supplied from actual verification_key (not independently tested here).

Independent source review, observed UTC2026-11-18 19:46:43.
Opened counting scratch include/forge/search.hpp244-330, src/search.cpp618-765, include/forge/shortcut_count.hpp36-48, and original r15d src/search.cpp490-524 and539-568. No source edits by reviewer.

No discrepancy found in H82 reference selection semantics. By-value TTCluster snapshot is scanned scalar for first occupied matching verification key and first empty entry. Probe miss chooses firstempty or earliest strict minimum depth-4*generation_age in a full cluster, exactly the r15d choice. Store re-finds first existing matching key, otherwise uses supplied saved probe slot; it correctly does NOT recompute a fresh replacement slot after subtree search, since r15d preserves supplied slot on a miss. Actual owned AVX512 mask result and locked/scalar path are compared to the reference at all hook returns/selected-store points. Reference is local and does not mutate actual entries, generation counters or search state.

Class definitions: hit/miss_empty/miss_full partition all probe+store uses according to the pre-call snapshot. Store miss_empty means the cluster contains at least one empty entry, not necessarily that supplied destination is empty. Older-generation flag overlaps these classes and applies to probe hits or selected store destinations whose occupied generation differs before mutation. Stores on older selected entries satisfy actual admission predicate via generation mismatch, so this class represents an admitted older-generation write. Probes on older hits refresh actual generation after reference snapshot. Probes+stores should equal H82 uses; hit+miss_empty+miss_full should equal H82 uses. Class definitions must accompany counts rather than imply disjoint older-generation fourthclass.

Store caveat: H82 observes the selected destination and whether that selected entry matched, BEFORE admission/move-write decisions. A rejected same-generation store still counts as a store selection/use, even if no payload is written. H82 alone therefore verifies selection, not whether every use writes bytes. Existing H18 post-store whole-cluster reference remains responsible for payload/admission/move semantics. Readonly H82 scan does not reproduce r15d owner/epoch/handle rejection because worker fast API relies on valid caller handles.

Wrong5 is isolated: only cls==miss_full changes local expected slot to(slot+1)&3; hit bit and actual table/returned slot are untouched. This affects full-miss probe and store comparisons but no other class; because four distinct slots exist, changed expected slot must differ for a normallycorrect fullmiss. Runtime some-but-not-all result still required.

Coverage limits: no independent hashfull sample-counter check; no proof of generation/lifecycle races or malformed caller handles. Required T1 workloads may not reach locked multi-thread branch. Reference operates on the existing cluster selected by shared hash/index helper, so wrong cluster-index computation shared with reference is outside this specific slot/lane-mask test. Diagnostics use live scoped Worker Board context; calls outside that context are not counted. Counter totals are per probe/store call, not per searched node or successful write. No claim of full concurrency or all-input TT correctness follows from zero differences.

## 3. K1, K3 and class-specific control: PASS on final clean builds
K1 first200 W1 entries (197 distinct), depth9, Hash16/reset each:4097080 last-completed-depth nodes, all200 nodes/bestmove rows and twelve old per-row counters match Job13 K1.
K3 first200, Hash1, one process, isready before each and no ucinewgame between: unchanged r15d and count5 each3351324 last-completed-depth nodes, all200 rows equal. Full miss class2596221 >0 permitted control. Wrong5 rotates only local full-miss reference slot;2596221/4542519 differ, strictly some and fewer than all. Wrong5 search tree and all other counters unchanged; class tables equal per search after clean rebuild.

| Counter | K1 uses/differ | K3 count uses/differ | K3 wrong uses/differ |
|---|---:|---:|---:|
| B1 | 2564528/0 | 2041466/0 | 2041466/0 |
| B2 | 2689044/0 | 2156087/0 | 2156087/0 |
| B5 | 2607489/0 | 2326016/0 | 2326016/0 |
| B6 | 3895460/0 | 3170149/0 | 3170149/0 |
| S-B1 | 2564528/0 | 2041466/0 | 2041466/0 |
| S-B2 | 2689044/0 | 2156087/0 | 2156087/0 |
| S-B4 | 2564528/0 | 2041466/0 | 2041466/0 |
| S-B7 | 3895323/0 | 3174994/0 | 3174994/0 |
| H28 | 341487/0 | 259781/0 | 259781/0 |
| H18 | 2063485/0 | 3178604/0 | 3178604/0 |
| H27 | 1124811/0 | 934797/0 | 934797/0 |
| H25 | 5483925/0 | 4227826/0 | 4227826/0 |
| H82 | 5760791/0 | 4542519/0 | 4542519/2596221 |

H82 classes: hit/miss_empty/miss_full partition uses; older_generation overlaps. Probes+stores separately partition uses. Store means selection, not every call writes payload.
| Run | Hit | Miss empty | Miss full | Older generation | Probes | Stores |
|---|---:|---:|---:|---:|---:|---:|
| K1 | 2396151 | 3364640 | 0 | 0 | 3697306 | 2063485 |
| K3_count | 1779182 | 167116 | 2596221 | 1105870 | 2925861 | 1616658 |
| K3_wrong | 1779182 | 167116 | 2596221 | 1105870 | 2925861 | 1616658 |

First five control raw diagnostics; move0000 denotes a probe without a candidate move, not an actual played null move:
```text
info string shortcut disagreement H82 premove_fen r1bb1rk1/5ppp/p1q1pB2/P2p4/1ppP4/2P1P2P/1P1NBPP1/R3QRK1 w - - 1 17 move 0000
info string shortcut disagreement H82 premove_fen r1bb1rk1/5ppp/p1q1pB2/P2p4/1ppP4/2P1P2P/1P1NBPP1/R3QRK1 w - - 1 17 move 0000
info string shortcut disagreement H82 premove_fen r1bq1rk1/5ppp/p3p3/3P4/P1pb4/5P1P/1p1NB1PK/R2QR3 w - - 0 20 move 0000
info string shortcut disagreement H82 premove_fen r1bq1r1k/4bppp/p3p3/3p4/P1pPPP2/7P/1P2B1P1/R3QK2 b - - 0 20 move 0000
info string shortcut disagreement H82 premove_fen r1bq1r1k/4bppp/p3p3/3p4/P1pPPP2/7P/1P2B1P1/R3QK2 b - - 0 20 move 0000
```

## 4. Prediction graded: all PASS
Immutable prediction commit b033c790da31dff895f864b97d989aed129d68af, after corrected gate validation and before any S1/S2/S3 run. Extrapolated200-entry gate and prior workloads, not blind to those histories. Fraction denominator is all H82 probe+store calls.
| Workload | Predicted uses | Actual uses | Predicted full-miss share | Actual share | Predicted/actual differences |
|---|---:|---:|---:|---:|---:|
| S1 | 20000000–28000000 | 25127532 | 0–1% | 0.0000119391% | 0/0 |
| S2 | 6000000–10000000 | 8190621 | 0–10% | 0.0141381% | 0/0 |
| S3 | 18000000–28000000 | 22568423 | 50–80% | 62.7210% | 0/0 |

## 5. S1, S2 and S3
S1:1000 W1 entries/990distinct,16543291 last-completed-depth nodes; all nodes/bestmove rows match Job7 and old12 per-row uses match Job13. S2:same20distinct starts asJob13,1370legalplies/searches,5612423 actual softnodes total; all moves and old12 per-ply counters unchanged. S3:all1000 W1 entries sequentially, Hash1/no resets, count5 and unchangedr15d each15051338 last-completed-depth nodes; every row equal. All13 normal counters zero differences.
| Counter | S1 uses/differ | S2 uses/differ | S3 uses/differ |
|---|---:|---:|---:|
| B1 | 9079813/0 | 3212417/0 | 8309613/0 |
| B2 | 9638809/0 | 3468791/0 | 8898022/0 |
| B5 | 10935512/0 | 4071447/0 | 10392232/0 |
| B6 | 15430637/0 | 5227491/0 | 14030703/0 |
| S-B1 | 9079813/0 | 3212417/0 | 8309613/0 |
| S-B2 | 9638809/0 | 3468791/0 | 8898022/0 |
| S-B4 | 9079813/0 | 3212417/0 | 8309613/0 |
| S-B7 | 15531178/0 | 5255554/0 | 14119318/0 |
| H28 | 1376393/0 | 493901/0 | 1247950/0 |
| H18 | 9040060/0 | 2638740/0 | 16530047/0 |
| H27 | 5029379/0 | 1610870/0 | 4523609/0 |
| H25 | 23565361/0 | 6954922/0 | 19675312/0 |
| H82 | 25127532/0 | 8190621/0 | 22568423/0 |

| Run | Hit | Miss empty | Miss full | Older generation | Probes | Stores |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 9305229 | 15822300 | 3 | 0 | 16087474 | 9040058 |
| S2 | 3841883 | 4347580 | 1158 | 514098 | 5552660 | 2637961 |
| S3_count | 8246159 | 167116 | 14155148 | 5778109 | 14571274 | 7997149 |

H18 uses need not equal H82 stores: H18 also counts replacement/locked-probe comparisons. H82 probe/store diagnostics only count live Worker-context operations. Full-miss S1 count3 and S2 count1158 show sparse reach under Hash16; persistent Hash1 strongly exercises this class.

## 6. L1 and L1c: literal liveness NOT SHOWN
Job14 Step4 session differential; execution complete observed date -u19:45:23 UTC on2026-11-18.

Source ambiguity and interpretation fixed before running
Literal L1 maps five stated transitions to searches11,21,31,41,51 respectively: Hash1;ucinewgame;HistRework0;HistRework2+NNUEArchFile net768+NNUEArch true;Hash16. L1c then says HistRework0 before31 'instead of the reload step', although reload is literally at41, not31. No script can simultaneously satisfy both descriptions. Therefore run1=L1 exactly as written; run2=L1c_literal31 implements the explicitly numbered31 command, which already exists and changes nothing; run3=L1c_exploratory41 instead changes the actual reload transition at41, explicitly exploratory and not a substitute for the numbered31 control.

Method
Each of the three comparisons launches one fresh unchanged r15d process and one fresh unchanged kF process, six processes total. Each process runs W1 positions1-60 sequentially at depth9, PC20 plus active net768 checksum30ab43b4ba5db5f3, Threads1, initial Hash16. Only the specified search21 transition sends ucinewgame; isready before every search. Search41 baseline emits loaded+active net confirmation with the same checksum (verified in raw transcript). All UCI commands and complete engine stdout retained. No source/instrumentation changes and no local run script committed.

Results (nodes always sum of last completed-depth info nodes)
L1:60searches/program;734524nodes each. All60bestmove lines equal; all60final-info lines equal after removing only time and nps. Hashfull retained and equal in all60. Exact unnormalized final-info lines differ37/60, firstsearch1; every difference disappears after removing only time/nps. Thus the assignment's literal byte-identical final-info demand is NOT met, but deterministic search fields agree.
L1c_literal31:60searches/program;734524nodes each. All60bestmoves and canonical final-info lines equal, including all before31. Exact final-info lines differ30/60, firstsearch1, solelytime/nps. No behavioral difference at or after31. Requested numbered31 liveness control therefore does NOT show Step4 live. This is the stated stop condition for interpreting Step4, not a reason to silently substitute another control.
L1c_exploratory41:60searches/program;r15d734524nodes,kF637868nodes. First40bestmoves/canonical final-info lines equal. First behavioral difference41;12bestmove differences,20canonical final-info/node differences,17hashfull differences. Exact final-info lines differ44/60 including volatile differences before41. This demonstrates responsiveness to withholding the actual HistRework2+reload transition, but does not repair or pass the literal31 control.

Exact first L1 final-info pair
r15d: info depth 9 seldepth 19 score cp -74 nodes 7372 nps 1843000 hashfull 1 time 4 pv d8a5 d1e1 g7g6 e5g4 f6g4 e2g4 d7f6 g4e6 e7d8 e6c8
kF: info depth 9 seldepth 19 score cp -74 nodes 7372 nps 1474400 hashfull 1 time 5 pv d8a5 d1e1 g7g6 e5g4 f6g4 e2g4 d7f6 g4e6 e7d8 e6c8

Exploratory41 first difference (deliberate different script, not engine bug)
Before search41 r15d gets HistRework2, NNUEArchFile same net, NNUEArch true; kF gets HistRework0 and no reload.
FEN: r5k1/pQ3p2/2prb1pp/2q1N3/P5P1/2P4P/2P2P2/R3R1K1 b - - 0 26
r15d: info depth 9 seldepth 25 score cp 77 nodes 18786 nps 1565500 hashfull 127 time 12 pv c5f2 g1f2 f7f6 b7a8 e6c8 e5g6 d6d2 f2e3 d2d3 e3d3 a7a6 a8c6
r15d: bestmove c5f2
kF: info depth 9 seldepth 22 score cp -125 nodes 21425 nps 1947727 hashfull 144 time 11 pv a8f8 b7f7 f8f7 e1e2 e6d5 a1b1 c5c3 b1b8 f7f8 e5g6 c3h3 g6f8
kF: bestmove a8f8

Evidence files: L1_r15d.raw.txt,L1_kf.raw.txt,L1c_literal31_r15d.raw.txt,L1c_literal31_kf.raw.txt,L1c_exploratory41_r15d.raw.txt,L1c_exploratory41_kf.raw.txt. Derived per-search *.rows.local.json and L1_comparison.local.json remain local, not publication candidates. Full raw transcript chunks and this prose are the evidence to preserve.

Limits
Positions and sessions these scripts do not reach; the PC's net, compiler and build; more than one search thread; Hash sizes other than1and16. The compound transition does not isolate net reload from HistRework changes. L1's equality is observed only for deterministic fields; exact transcript/time/nps equality was not achieved. Step4 is not shown live under the literal requested control, so row85 must retain this limitation rather than be marked unconditionally covered.

## 7. Map again
# Job14 updated86-hunk coverage map

Same original86 IDs/ranges preserved. H18 evidence extended; H82 NONE to PARTIAL_DIRECT. H85 remains NONE because literal requested liveness control is not shown. NONE30 to29. Partial evidence is not exhaustive proof. Full-miss class reached withHash1; class controls and matched workloads described in report.

|ID|File|kF range|Changedlines|Change|Coverage/evidence|Limit|
|---:|---|---|---:|---|---|---|
|1|src/board.cpp|2-8|1|Add assert header|NO_BEHAVIOUR: Header only; runtime assertions disabled by NDEBUG in original Release build.|Header only; runtime assertions disabled by NDEBUG in original Release build.|
|2|src/board.cpp|834-841|3|Mask king destinations attacked by enemy pawns/king before expensive safety test|NONE: Job10 B7/perft exercises move generation but no per-use independent early-mask counter; no inspected external report isolates this hunk.|Job10 B7/perft exercises move generation but no per-use independent early-mask counter; no inspected external report isolates this hunk.|
|3|src/board.cpp|852-872|15|has_legal_move fast safe-pawn witness and no-ray pin shortcut|NONE: Job10/11 B2/S-B2 checks quiet picker, not has_legal_move early witnesses; broad node equality is not isolated coverage.|Job10/11 B2/S-B2 checks quiet picker, not has_legal_move early witnesses; broad node equality is not isolated coverage.|
|4|src/board.cpp|1165-1171|2|Extend make_move signature with supplied key/check hint|DIRECT: Job10 B5/B6 counters at every shortcut use; Job11 repeats same old counter uses. Signature itself defines no new algorithm.|Job10 B5/B6 counters at every shortcut use; Job11 repeats same old counter uses. Signature itself defines no new algorithm.|
|5|src/board.cpp|1179-1195|9|Conditional Undo cache save and optional old-EP hash update/debug shadow|DIRECT: Job11 S-B7 recomputes restored fields cache-free; Job10 B6 independent incremental key comparison covers supplied-key uses. NDEBUG shadow off normally.|Job11 S-B7 recomputes restored fields cache-free; Job10 B6 independent incremental key comparison covers supplied-key uses. NDEBUG shadow off normally.|
|6|src/board.cpp|1198-1238|25|Skip capture/mover/promotion hash XORs when precomputed key supplied|DIRECT: Job10 B6 compares every supplied key with incremental reference incl capture/promotion terms; repeated Job11. No per-move-class tally.|Job10 B6 compares every supplied key with incremental reference incl capture/promotion terms; repeated Job11. No per-move-class tally.|
|7|src/board.cpp|1242-1298|64|Consume precomputed key and known false gives-check; otherwise full paths|DIRECT: Job10 B5 recomputes checkers for every known0; B6 independently accumulates full key. Job11 repeats counts; S-B1 independently verifies quiet gives-check input.|Job10 B5 recomputes checkers for every known0; B6 independently accumulates full key. Job11 repeats counts; S-B1 independently verifies quiet gives-check input.|
|8|src/board.cpp|1331-1338|3|Restore Undo fields only if valid else invalidate|DIRECT: Job11 S-B7 validates every restored-valid cache against piece-square oracle; invalid-field payload intentionally unobservable until refresh.|Job11 S-B7 validates every restored-valid cache against piece-square oracle; invalid-field payload intentionally unobservable until refresh.|
|9|src/board.cpp|1343-1350|3|Conditional cache save for null move|DIRECT: Job11 S-B7 null-unmake reconstruction validates restored-valid fields; no null-only tally.|Job11 S-B7 null-unmake reconstruction validates restored-valid fields; no null-only tally.|
|10|src/board.cpp|1370-1377|3|Conditional cache restoration on null unmake|DIRECT: Job11 S-B7 includes null-unmake at every valid restore, compared with piece-array oracle.|Job11 S-B7 includes null-unmake at every valid restore, compared with piece-array oracle.|
|11|src/board.cpp|1516-1534|14|SEE contact/ray-empty early success before full exchange loop|NONE: Job10 B8 was source-read only, no SEE reference counter. External sol3 asserts reported by handoff but exact coverage not inspected here.|Job10 B8 was source-read only, no SEE reference counter. External sol3 asserts reported by handoff but exact coverage not inspected here.|
|12|src/board.cpp|1536-1564|22|SEE actual-ray-empty early success and factored attacker gather; off-branch pawn refutation|NONE: Job10 B8 source proof only; no local independent SEE loop comparison. HOIST0 pawn early-refutation is not in build; other added lines active.|Job10 B8 source proof only; no local independent SEE loop comparison. HOIST0 pawn early-refutation is not in build; other added lines active.|
|13|src/nnue_v3.cpp|696-701|8|Remove out-of-line king_key; move identical expression to header h76|NO_BEHAVIOUR: Same orientation/bucket/flip formula inspected old body vs new inline body. Linkage/inlining relocation, not changed answer for valid inputs.|Same orientation/bucket/flip formula inspected old body vs new inline body. Linkage/inlining relocation, not changed answer for valid inputs.|
|14|src/nnue_v3.cpp|814-828|12|Resize/reinitialize only metadata instead of value-zeroing accumulator arrays|PARTIAL: Job7 W2 reload/switch lifecycle differential; Job8 every v3 search output independently shadowed against fresh scalar evaluation. No allocation-path count or hidden-size-switch coverage.|Job7 W2 reload/switch lifecycle differential; Job8 every v3 search output independently shadowed against fresh scalar evaluation. No allocation-path count or hidden-size-switch coverage.|
|15|src/nnue_v3.cpp|899-1042|138|Add fused one-perspective update plus opposite refresh and output|PARTIAL: Job8 S1/S2 every fast v3 result compared with fresh scalar evaluation; positive incremental-error control. No dedicated XOR-fusion branch hit count, so cannot assert every case/line exercised. Job7 alone only differential, not independent.|Job8 S1/S2 every fast v3 result compared with fresh scalar evaluation; positive incremental-error control. No dedicated XOR-fusion branch hit count, so cannot assert every case/line exercised. Job7 alone only differential, not independent.|
|16|src/nnue_v3.cpp|1064-1110|52|Reorder AVX512 refresh by hidden lane, zero-change copy fast path, borrow piece bitboards|PARTIAL: Job8 per-evaluation fresh reference and scalar-kernel differential cover observable outputs on reached calls; no zero-change-path or individual refresh branch counts.|Job8 per-evaluation fresh reference and scalar-kernel differential cover observable outputs on reached calls; no zero-change-path or individual refresh branch counts.|
|17|src/search.cpp|21-27|2|Default-enable bad-capture prefix reuse instead of separate array|NONE: NONE|No per-use independent mechanism test identified.|
|18|src/search.cpp|525-661|131|Fast TT locked probe and owned/locked store; factored full-cluster replacement|PARTIAL_DIRECT: Job12 H18 retained whole-cluster store reference plus Job14 H82 per-probe/store scalar precluster hit/slot comparison and full-miss-specific control|Store use is selected destination, not necessarily payload write; H18 separately checks admission/poststate. Shared index helper, sampling counters, malformed handles and concurrency remain outside.|
|19|src/search.cpp|886-916|23|Quiet legality/check cached at return and consumed by search|PARTIAL_OR_DIRECT: Job10 B1-B4; Job11 S-B1/S-B2/S-B4|Direct per-use piece-array oracle for quiet legality/check/copies on W1 and20games; not generator completeness or all-position proof|
|20|src/search.cpp|944-950|3|Mark illegal tied-evasion slots Move::none instead of deferred legality mask|NONE: NONE|No per-use independent mechanism test identified.|
|21|src/search.cpp|955-964|6|Quiet legality/check cached at return and consumed by search|PARTIAL_OR_DIRECT: Job10 B1-B4; Job11 S-B1/S-B2/S-B4|Direct per-use piece-array oracle for quiet legality/check/copies on W1 and20games; not generator completeness or all-position proof|
|22|src/search.cpp|1007-1039|20|MovePicker storage refactor and copied king-line fields; fallback branch closure|PARTIAL_OR_DIRECT: Job10 B4; Job11 S-B4|Direct oracle covers copied masks at every quiet return; buffer removal and evasion mask lifetime lack dedicated reference|
|23|src/search.cpp|1043-1049|1|MovePicker storage refactor and copied king-line fields; fallback branch closure|PARTIAL_OR_DIRECT: Job10 B4; Job11 S-B4|Direct oracle covers copied masks at every quiet return; buffer removal and evasion mask lifetime lack dedicated reference|
|24|src/search.cpp|1079-1085|2|Lazily produce/invalidate HistRework threat maps and piece-specific reads|NONE: NONE|No per-use independent mechanism test identified.|
|25|src/search.cpp|1121-1173|39|AVX512 16/8-lane highest-score selection and Scored-return wrapper|PARTIAL_DIRECT: Job13 H25: every returned Move+score compared with private-tail plain highest scan; earliest ties; independent local r15d sort transition; class-specific tie control|Path counters show16/8 reach; returned values, not every intermediate swap; shared std::sort, otherarchitectures/options untested.|
|26|src/search.cpp|1202-1212|4|AVX512 16/8-lane highest-score selection and Scored-return wrapper|PARTIAL_DIRECT: Job13 H25: Scored-return and Move wrapper output checked for all call paths; same independent reference and tie control|No separate proof of all internal postselection array permutations.|
|27|src/search.cpp|1230-1332|95|Fused capture generation and capture-history scoring|PARTIAL_DIRECT: Job13 H27: full ordered capture list/scores and seed metadata compared with prior separate generator/scalar scoring; knight-capture-only control|Shared Board generator/attack tables/history data; not absolute chess or history-update correctness.|
|28|src/search.cpp|1340-1563|210|Fused quiet generation and per-piece history/continuation scoring|PARTIAL_DIRECT: Job12 H28 and Job13 retained counter: full ordered quiet list/scalar scores+seed metadata versus prior separate path|H25 laterselection now separately checked, but shared primitives/nondefaultbranches still limited.|
|29|src/search.cpp|1568-1583|13|Per-worker reusable evasion/picker scratch replacing stack-owned lists|NONE: NONE|No per-use independent mechanism test identified.|
|30|src/search.cpp|1635-1658|21|Mark illegal tied-evasion slots Move::none instead of deferred legality mask|NONE: NONE|No per-use independent mechanism test identified.|
|31|src/search.cpp|1687-1711|27|Clear integer history tables with memset and reusable threat readiness|PARTIAL_OR_DIRECT: Job9 ucinewgame command path|Job9 establishes stop-before-clear and observable protocol path, not direct byte-wise old/new history table comparison|
|32|src/search.cpp|1748-1760|6|Dead-material cheap guard and per-search NNUE active snapshots|NONE: NONE|Job7/8 backend transition/eval evidence partly applies to snapshots; no independent per-use dead-material guard proof in requested jobs9-11.|
|33|src/search.cpp|1819-1829|4|Cache material-correction index in stack and invalidate on capture/promotion|NONE: NONE|No per-use independent mechanism test identified.|
|34|src/search.cpp|1831-1838|4|Snapshot v3 backend, prepare once, direct king-square fast accumulator branch|PARTIAL_OR_DIRECT: Job8 shadow per-eval independent full rebuild (prior additional evidence)|Job8 checks every observed v3 result; specific branch counts not separated; unobserved nets/buckets remain uncovered|
|35|src/search.cpp|1867-1881|5|Propagate material correction index across null and snapshot v3 invalidation|NONE: NONE|Job8 shadow covers resulting observed v3 evaluations, not correction-index identity; retain NONE for mixed material-index mechanism|
|36|src/search.cpp|1883-1909|15|Cache material-correction index in stack and invalidate on capture/promotion|NONE: NONE|No per-use independent mechanism test identified.|
|37|src/search.cpp|1965-1976|7|Cache material-correction index in stack and invalidate on capture/promotion|NONE: NONE|No per-use independent mechanism test identified.|
|38|src/search.cpp|2100-2106|2|Lazily produce/invalidate HistRework threat maps and piece-specific reads|NONE: NONE|No per-use independent mechanism test identified.|
|39|src/search.cpp|2121-2127|3|Lazily produce/invalidate HistRework threat maps and piece-specific reads|NONE: NONE|No per-use independent mechanism test identified.|
|40|src/search.cpp|2255-2261|2|Single-worker node-only stop shortcut, and initialize its eligibility|NONE: NONE|Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter|
|41|src/search.cpp|2277-2283|2|Worker TT call sites use lightweight probe type|NONE: NONE|No per-use independent mechanism test identified.|
|42|src/search.cpp|2325-2333|4|Lazily produce/invalidate HistRework threat maps and piece-specific reads|NONE: NONE|No per-use independent mechanism test identified.|
|43|src/search.cpp|2336-2345|2|Pass already-known givescheck and precomputed childkey to make_move|PARTIAL_OR_DIRECT: Job10 B5/B6 counters; Job11 retained B5/B6|Every used known0 compared compute_checkers and supplied key compared incremental shadow on W1/S2; no independent test of unused hint classes|
|44|src/search.cpp|2358-2369|3|Pass already-known givescheck and precomputed childkey to make_move|PARTIAL_OR_DIRECT: Job10 B5/B6 counters; Job11 retained B5/B6|Every used known0 compared compute_checkers and supplied key compared incremental shadow on W1/S2; no independent test of unused hint classes|
|45|src/search.cpp|2407-2413|2|Single-worker node-only stop shortcut, and initialize its eligibility|NONE: NONE|Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter|
|46|src/search.cpp|2437-2443|2|Worker TT call sites use lightweight probe type|NONE: NONE|No per-use independent mechanism test identified.|
|47|src/search.cpp|2679-2686|4|Lazily produce/invalidate HistRework threat maps and piece-specific reads|NONE: NONE|No per-use independent mechanism test identified.|
|48|src/search.cpp|2722-2728|2|Quiet legality/check cached at return and consumed by search|PARTIAL_OR_DIRECT: Job10 B1-B4; Job11 S-B1/S-B2/S-B4|Direct per-use piece-array oracle for quiet legality/check/copies on W1 and20games; not generator completeness or all-position proof|
|49|src/search.cpp|2877-2889|4|Pass already-known givescheck and precomputed childkey to make_move|PARTIAL_OR_DIRECT: Job10 B5/B6 counters; Job11 retained B5/B6|Every used known0 compared compute_checkers and supplied key compared incremental shadow on W1/S2; no independent test of unused hint classes|
|50|src/search.cpp|3138-3151|8|Snapshot backend active state and prepare v3 state at search entry|PARTIAL_OR_DIRECT: Job9 stop-before-option ordering; Job7/8 backend replay (additional)|Source lifetime proof plus transition replay; not all concurrent direct C++ clients|
|51|src/search.cpp|3337-3343|2|Worker TT call sites use lightweight probe type|NONE: NONE|No per-use independent mechanism test identified.|
|52|src/search.cpp|3383-3394|5|Single-worker node-only stop shortcut, and initialize its eligibility|NONE: NONE|Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter|
|53|src/search.cpp|3851-3859|4|Move root board into main Worker when no helpers|PARTIAL_OR_DIRECT: Job9 copy/worker ownership source audit|Source ownership proof; broad tree equality only, not standalone moved-from state assertion|
|54|src/search.cpp|3872-3882|8|Snapshot v3 backend, prepare once, direct king-square fast accumulator branch|PARTIAL_OR_DIRECT: Job8 shadow per-eval independent full rebuild (prior additional evidence)|Job8 checks every observed v3 result; specific branch counts not separated; unobserved nets/buckets remain uncovered|
|55|src/search.cpp|3886-3922|46|Snapshot v3 backend, prepare once, direct king-square fast accumulator branch|PARTIAL_OR_DIRECT: Job8 shadow per-eval independent full rebuild (prior additional evidence)|Job8 checks every observed v3 result; specific branch counts not separated; unobserved nets/buckets remain uncovered|
|56|src/uci.cpp|43-153|109|Replace PositionCache representation and tokenizer/prefix matching with string_views|DIRECT: Job9 PartA26 sequential parser/cache cases plus PartB own whitespace/prefix/malformed cases compare r15d/kF outputs; includes raw/fallback prefix classes. Finite tests, not arbitrary byte/locale proof.|Job9 PartA26 sequential parser/cache cases plus PartB own whitespace/prefix/malformed cases compare r15d/kF outputs; includes raw/fallback prefix classes. Finite tests, not arbitrary byte/locale proof.|
|57|src/uci.cpp|158-220|46|Canonical move append and stack32/heap token collection for go parsing|DIRECT: Job9 PartB includes32/33-token and >32 searchmoves cases, illegal suffix retention and signed/overflow grammar; source path table.|Job9 PartB includes32/33-token and >32 searchmoves cases, illegal suffix retention and signed/overflow grammar; source path table.|
|58|src/uci.cpp|222-239|10|Use string_view take_integer/int reader and token_count|DIRECT: Job9 PartB malformed/missing keyword value and signed overflowing integer cases, outputs matched r15d.|Job9 PartB malformed/missing keyword value and signed overflowing integer cases, outputs matched r15d.|
|59|src/uci.cpp|247-253|2|Clock token view instead of owning string|PARTIAL: Job9 parser boundary/read-through includes same parse_clock_ms call; fixed-depth/node tests do not independently exhaust clock range/timing.|Job9 parser boundary/read-through includes same parse_clock_ms call; fixed-depth/node tests do not independently exhaust clock range/timing.|
|60|src/uci.cpp|258-264|2|Node/softnode count token view|DIRECT: Job9 PartB signed/overflow/zero/repeated limit cases; r15d and kF compared.|Job9 PartB signed/overflow/zero/repeated limit cases; r15d and kF compared.|
|61|src/uci.cpp|308-314|2|searchmoves loop bounds use token_count|DIRECT: Job9 >32-token searchmoves and keyword termination cases matched r15d.|Job9 >32-token searchmoves and keyword termination cases matched r15d.|
|62|src/uci.cpp|318-342|16|Legacy go parser view/count conversion and remove comment|OFF: Entire changed legacy reader under #else FORGE_FIX_GO_PARSE; original macro defaults1 in both builds, no runtime effect here.|Entire changed legacy reader under #else FORGE_FIX_GO_PARSE; original macro defaults1 in both builds, no runtime effect here.|
|63|src/uci.cpp|357-363|2|Legacy searchmoves loop bound conversion|OFF: Inside legacy #else FORGE_FIX_GO_PARSE, not executed in measured builds.|Inside legacy #else FORGE_FIX_GO_PARSE, not executed in measured builds.|
|64|src/uci.cpp|416-434|8|Reuse persistent task and copy Board/three task fields rather than move whole task|PARTIAL: Job9 PartC source concurrency/lifetime audit and repeated UCI command runs; no independent race/future-field completeness proof. Source assignment exactly3 existing fields.|Job9 PartC source concurrency/lifetime audit and repeated UCI command runs; no independent race/future-field completeness proof. Source assignment exactly3 existing fields.|
|65|src/uci.cpp|494-501|5|Top-level command parse uses string_view tokenizer|DIRECT: Job9 PartA/B command whitespace including tabs/VT/FF/CR, perft/search dispatch outputs compared; custom locales not tested.|Job9 PartA/B command whitespace including tabs/VT/FF/CR, perft/search dispatch outputs compared; custom locales not tested.|
|66|src/uci.cpp|577-587|5|Reset new cache fields and localize setoption stringstream|DIRECT: Job9 ucinewgame/position sequences and option-driven setup exercised; Job7 W2 independently observed ucinewgame resets board. Option parser remainder unchanged.|Job9 ucinewgame/position sequences and option-driven setup exercised; Job7 W2 independently observed ucinewgame resets board. Option parser remainder unchanged.|
|67|src/uci.cpp|820-826|2|Dispatch position to new view parser|DIRECT: Job9 all26 sequential cases plus focused14 compare board/perft/search diagnostics; mapping records post-error retained positions.|Job9 all26 sequential cases plus focused14 compare board/perft/search diagnostics; mapping records post-error retained positions.|
|68|src/uci.cpp|830-840|8|Perft command/depth peek via view instead of stream seek|DIRECT: Job9 PartA perft and malformed/whitespace paths; Job10 six perft known answers. Does not prove all possible invalid depth strings.|Job9 PartA perft and malformed/whitespace paths; Job10 six perft known answers. Does not prove all possible invalid depth strings.|
|69|src/uci.cpp|857-863|4|Dispatch go view parser instead of rewinding stream|DIRECT: Job9 depth/node/searchmoves/missing/overflow/>32 token tests compare outputs.|Job9 depth/node/searchmoves/missing/overflow/>32 token tests compare outputs.|
|70|src/uci.cpp|929-938|5|Bench depth gets its own remainder stringstream|PARTIAL: Repeated defaultbench11/13 known gates exercise valid depths; no exhaustive malformedbench argument test. Formula/stream extraction retained.|Repeated defaultbench11/13 known gates exercise valid depths; no exhaustive malformedbench argument test. Formula/stream extraction retained.|
|71|include/forge/b4.hpp|37-62|24|Skip computing lesser-attack masks for absent friendly rooks/queens|NONE: NONE|No per-use independent mechanism test identified.|
|72|include/forge/board.hpp|208-215|3|Declare optional make_move key and check arguments/defaults|DIRECT: Job10 B5/B6 at every actual supplied argument use; ordinary perft callers keep defaults. Corresponds implementationh4.|Job10 B5/B6 at every actual supplied argument use; ordinary perft callers keep defaults. Corresponds implementationh4.|
|73|include/forge/board.hpp|220-231|6|Expose ensure_king_lines refreshing accessor|DIRECT: Job11 S-B4 compares copied masks at every returned quiet, S-B7 restored valid fields; independent piece-array reference reads no cache.|Job11 S-B4 compares copied masks at every returned quiet, S-B7 restored valid fields; independent piece-array reference reads no cache.|
|74|include/forge/board.hpp|249-255|1|Expose const piece-bitboard array view|PARTIAL: Job8 independent fresh-reference output comparison covers reached NNUE borrowers; source accessor returns existing bitboards unchanged, no independent standalone accessor invariant counter.|Job8 independent fresh-reference output comparison covers reached NNUE borrowers; source accessor returns existing bitboards unchanged, no independent standalone accessor invariant counter.|
|75|include/forge/eval.hpp|51-59|3|Add cheap heavy-piece/pawn prefilter for dead material recognition|NONE: No focused counter of prefilter vs full dead_material_score; original eval.cpp516-518 starts with identical rejection condition. Native default dead_material_enabled=false, but helper may have additional search callers.|No focused counter of prefilter vs full dead_material_score; original eval.cpp516-518 starts with identical rejection condition. Native default dead_material_enabled=false, but helper may have additional search callers.|
|76|include/forge/nnue_v3.hpp|173-185|8|Inline king-key orientation/bucket/flip expression|NO_BEHAVIOUR: Equivalent body moved from oldnnue_v3.cpp699-706 (h13); no formula change, valid square/net contract retained.|Equivalent body moved from oldnnue_v3.cpp699-706 (h13); no formula change, valid square/net contract retained.|
|77|include/forge/nnue_v3.hpp|217-227|5|Declare fused one-refresh evaluator|PARTIAL: Declaration for h15; Job8 global v3 shadow outputs, not dedicated fused-branch count.|Declaration for h15; Job8 global v3 shadow outputs, not dedicated fused-branch count.|
|78|include/forge/nnue_v3.hpp|272-293|23|Replay top-ply refresh directly from Board bitboards; reconstruct only older plies|PARTIAL: Job8 all fastv3 outputs checked independently from freshpiecepositions incl selfplay; no separate top/intermediate replay hit counts.|Job8 all fastv3 outputs checked independently from freshpiecepositions incl selfplay; no separate top/intermediate replay hit counts.|
|79|include/forge/search.hpp|17-25|3|Include AVX512 intrinsic declarations|PARTIAL_OR_DIRECT: NO_BEHAVIOR|Header inclusion itself adds no runtime branch|
|80|include/forge/search.hpp|132-149|10|Assert TT SIMD layout and add lightweight WorkerTTProbe type|PARTIAL_OR_DIRECT: NO_BEHAVIOR|Declaration alone no runtime computation; safety of omitted metadata tracked in H18/82/85|
|81|include/forge/search.hpp|206-218|7|Move TT metadata before stripe array|PARTIAL_OR_DIRECT: NO_BEHAVIOR|No logical output change; cache locality/performance can change clocked timing|
|82|include/forge/search.hpp|226-299|66|AVX512 owned TT probe and fast declarations; relocate metadata|PARTIAL_DIRECT: Job14 H82: every exercised owned/locked fast probe and selected store slot vs scalar precluster r15d scan; full Hash1 persistent workload and full-miss-only control|Partial direct lane/slot evidence only. Shared cluster index, no independent sample counters, no concurrency or malformed-handle proof; T1 does not establish locked-thread reach.|
|83|include/forge/search.hpp|306-322|9|Factor unchanged cluster-index arithmetic into helper|PARTIAL_OR_DIRECT: NO_BEHAVIOR|Expression identical algebraically; helper extraction no logical change|
|84|include/forge/search.hpp|533-541|3|Cache material-correction index in stack and invalidate on capture/promotion|NONE: NONE|No per-use independent mechanism test identified.|
|85|include/forge/search.hpp|645-694|50|Lazy threat/cache scratch fields, NNUE snapshots, TT-fast Worker dispatch|NONE: Job14 literal session deterministic fields agree, but requested search31 liveness not shown because duplicate HistRework0 command; exploratory41 not substituted|Remains NONE under required liveness gate. Literal raw final-info byte equality also fails on time/nps only. No universal state/lifecycle proof.|
|86|include/forge/search.hpp|731-745|9|Single-worker node-only stop shortcut, and initialize its eligibility|NONE: NONE|Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter|

## Remaining search-read NONE rows, ranked by changed lines
|Rank|Hunk|File/range|Changedlines|Equality condition|Distinguishing class|
|---:|---:|---|---:|---|---|
|1|85|include/forge/search.hpp:645-694|50|All readiness resets and ownership proofs of related hunks hold; fast handle consumed before epoch mutation|Mixed HistRework recursion, reloaded net, owned/locked TT modes|
|2|71|include/forge/b4.hpp:37-62|24|Only read by_type for actually-present mover; no caller requests absent type|Queen promotion, cached map invalidation, synthetic requests for absent piece mask|
|3|12|src/board.cpp:1536-1564|22|Actual no-enemy-attacker gather must equal first r15d loop gather; factored live mask must exclude captured/origin pieces correctly.|EP/capture x-ray, blocked sliders becoming unblocked, pawn/king/contact-only recaptures; HOIST0 branch not in current build.|
|4|30|src/search.cpp:1635-1658|21|Preserve full pseudo-legal scored list and tie swaps, discard exactly same moves including promotions sharing from/to|Equal-score legal/illegal evasions, underpromotions, TT move amid ties|
|5|3|src/board.cpp:852-872|15|When not in check, an off-king-ray pawn push/capture cannot expose ownking; no enemy geometric slider ray implies zero absolute pins.|Stalemate/nearly stalemated sparse position, pinned pawn, promotion push/capture, occupancy opening diagonal or file.|
|6|36|src/search.cpp:1883-1909|15|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|7|11|src/board.cpp:1516-1534|14|Contact+empty-board enemy slider-ray absence implies no first legal recapture and fullSEE result true.|EP removes blocker, origin vacates x-ray, promotionrecapture at backrank, pinned or defended king recapture.|
|8|29|src/search.cpp:1568-1583|13|Generation finishes copying/scoring before recursion can overwrite shared scratch|Nested evasion search and promotion ties|
|9|86|include/forge/search.hpp:731-745|9|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|10|37|src/search.cpp:1965-1976|7|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|11|32|src/search.cpp:1748-1760|6|Guard supersets all dead-material cases; snapshots stable because option changes stop search|Unusual recognized endings and backend reload/disable transitions|
|12|35|src/search.cpp:1867-1881|5|Null changes no material and backend state prepared before search|Null nodes with material-index valid/invalid and V3 on|
|13|52|src/search.cpp:3383-3394|5|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|14|33|src/search.cpp:1819-1829|4|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|15|42|src/search.cpp:2325-2333|4|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|16|47|src/search.cpp:2679-2686|4|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|17|2|src/board.cpp:834-841|3|Excluded pawn/king attacked squares must always fail full own-king safety even after capture.|King capture onto pawn-defended square, capture of checking pawn, nearby enemyking; illegal synthetic king adjacency outside accepted-board contract.|
|18|20|src/search.cpp:944-950|3|Preserve full pseudo-legal scored list and tie swaps, discard exactly same moves including promotions sharing from/to|Equal-score legal/illegal evasions, underpromotions, TT move amid ties|
|19|39|src/search.cpp:2121-2127|3|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|20|75|include/forge/eval.hpp:51-59|3|Full dead_material_score rejects every position containing pawn/rook/queen before changing score; caller must preserve that same condition.|Enable dead-material option, promotion/last-heavy-piece capture, mixed minor endings; stale piece bitboards or expanded recognition could break prefilter.|
|21|84|include/forge/search.hpp:533-541|3|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|22|17|src/search.cpp:21-27|2|Only overwrites already-consumed prefix; bad_count <= consumed index; preserves bad-capture order|Capture-rich nodes, many losing captures, equal scoring moves|
|23|24|src/search.cpp:1079-1085|2|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|24|38|src/search.cpp:2100-2106|2|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|25|40|src/search.cpp:2255-2261|2|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|26|41|src/search.cpp:2277-2283|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|
|27|45|src/search.cpp:2407-2413|2|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|28|46|src/search.cpp:2437-2443|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|
|29|51|src/search.cpp:3337-3343|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|

## Workload provenance
PC20: Threads1, Hash16, OwnBookfalse, LmrQuietBase93, LmrQuietDivisor205, LmrNoisyBase13, LmrNoisyDivisor333, LmrHistoryDivisor5643, NullMoveBase5, LmpBase8, HistoryPruneMultiplier2220, HistoryBonusQuadratic24, HistoryBonusLinear54, HistoryBonusMax2212, SingularDepth6, IirDepth2, NonPawnCorrectiontrue, CuckooReptrue, HistRework2, TtPruneV2true, CorrHistV2true, MateAlphaGuardtrue. Each W1 search resets ucinewgame/isready. Synthetic v3 hidden768 net checksum30ab43b4ba5db5f3, SHA256 c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7; W1 SHA256 3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521. Net and standalone positions remain local, never uploaded here.
Original r15d stack base6b98f2170a3210e71beed04bbd2553972c253ed7 plus PCr15/carbon2/E1; kF adds finalstack patch SHA2563d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30. Frozen original binaries listed in Step0.

Job14 exception: K3/S3 explicitly set Hash1 after initialPC20; persistent scripts send isready but no ucinewgame between searches. L1 transitions separately documented above. S1 reset perentry and S2 reset pergame remain unchanged.

## Facts
Claim19:43:23 UTC; native cutoff20:33:23 and reportdeadline20:43:23. All native operations completed before cutoff. Clean build correction/gates occurred before prediction. Independent raw reparse and source review supplement harness gates. No normal TT lane/slot discrepancy observed.

## Suspicions
No demonstrated engine bug. The initial count older-class discrepancy was an instrumented build race and was corrected with evidence retained. L1 raw differences are time/nps, not deterministic search differences. Contradictory control wording prevents literal liveness claim. H85 remains a coverage gap, not a proven fault.

## What I did not do
No speed/Elo claim, no PC build/net, no multi-thread test, no arbitrary hash sizes, no standalone position/game dataset publication. No independent hash/index/key computation oracle, no independent generation sample-count proof or malformed handle test. Shared primitives remain limits. Auxiliary skill auditor unavailable and not run; native harness checks/counter gates and independent raw reparse are separate completed verification.

## What I am not sure about
Unreached clusters/positions/session transitions, locked multi-thread reach, foreign/stale TT handles and other compilers/architectures remain outside this evidence. L1c search31 literal control is not live; exploratory41 does not silently replace it. Row85 therefore remains NONE. Zero observed differences is not universal equivalence.

### What this check cannot see
Positions and sessions these scripts do not reach; the PC's net, compiler and build; more than one search thread;
Hash sizes other than 1 and 16.

## Publication
At20:33:20 UTC131/139 queued evidence files fully read back:10648054bytes,max100000. All109 complete raw transcript parts plus manifest, aggregate summaries/classes, updated map and independentQA are remote. Ledger26017a837a6d4d87b041ec55595121a026277408 and missinginventory51e04357d6a9344a9d5a29b1508222be1222c9dd verified. Eight ancillary files remain local: C_count5_clean_build.txt,C_count5_build.txt,C_wrong5_from_job13.patch.txt,C_wrong5_clean_build.txt,C_wrong5_configure.txt,C_wrong5_build.txt,H82_cross_review.txt,H82_design.txt. The first upload timed out in permission review and404confirmed absent; no denial or retry. Others were not attempted before cutoff. Full count/wrong patches and final build manifest separately published; report embeds design/review prose but does not claim their standalone files remote. Six Step0 and sixsession raw logs separately verified. Job total under12MB, eachfileunder100KB. No S2summary/pergame/position datasets uploaded. Local stale checkout status below preserves evidence and is not a claim of source changes on remote.

After report: latest Finn instruction supersedes original30min wait: poll next job every2min for up to ONE HOUR, capped by ten-hour-run end2026-11-19T06:16:10Z. STOP still stops.

## Last command before report commit
```text
git status --short; ls -R forge-combo29/dot/job14
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job10.md
?? forge-combo29/REPORT_dot_job11.md
?? forge-combo29/REPORT_dot_job12.md
?? forge-combo29/REPORT_dot_job13.md
?? forge-combo29/REPORT_dot_job14.md
?? forge-combo29/REPORT_dot_job6.md
?? forge-combo29/REPORT_dot_job7.md
?? forge-combo29/REPORT_dot_job8.md
?? forge-combo29/REPORT_dot_job9.md
?? forge-combo29/dot/job10/
?? forge-combo29/dot/job11/
?? forge-combo29/dot/job12/
?? forge-combo29/dot/job13/
?? forge-combo29/dot/job14/
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
?? forge-combo29/dot/job9/
forge-combo29/dot/job14:
C_count5_build.txt
C_count5_clean_build.txt
C_count5_configure.txt
C_count5_from_job13.patch.txt
C_count5_full.patch.txt
C_wrong5_build.txt
C_wrong5_clean_build.txt
C_wrong5_configure.txt
C_wrong5_from_job13.patch.txt
C_wrong5_full.patch.txt
H82_cross_review.txt
H82_design.txt
K1.classes.txt
K1.progress.txt
K1.raw.txt
K1.rows.txt
K1.summary.txt
K1_preclean.classes.txt
K1_preclean.progress.txt
K1_preclean.raw.txt
K1_preclean.rows.txt
K1_preclean.summary.txt
K3_count.classes.txt
K3_count.raw.txt
K3_count.rows.txt
K3_count.summary.txt
K3_count_preclean.classes.txt
K3_count_preclean.raw.txt
K3_count_preclean.rows.txt
K3_count_preclean.summary.txt
K3_r15d.raw.txt
K3_r15d.rows.txt
K3_r15d.summary.txt
K3_wrong.classes.txt
K3_wrong.raw.txt
K3_wrong.rows.txt
K3_wrong.summary.txt
K3_wrong_preclean.classes.txt
K3_wrong_preclean.raw.txt
K3_wrong_preclean.rows.txt
K3_wrong_preclean.summary.txt
L1_comparison.local.json
L1_design_results.txt
L1_kf.raw.txt
L1_kf.rows.local.json
L1_r15d.raw.txt
L1_r15d.rows.local.json
L1c_exploratory41_kf.raw.txt
L1c_exploratory41_kf.rows.local.json
L1c_exploratory41_r15d.raw.txt
L1c_exploratory41_r15d.rows.local.json
L1c_literal31_kf.raw.txt
L1c_literal31_kf.rows.local.json
L1c_literal31_r15d.raw.txt
L1c_literal31_r15d.rows.local.json
S1.classes.txt
S1.progress.txt
S1.raw.txt
S1.rows.txt
S1.summary.txt
S2.classes.txt
S2.raw.txt
S2.summary.txt
S3_count.classes.txt
S3_count.raw.txt
S3_count.rows.txt
S3_count.summary.txt
S3_r15d.raw.txt
S3_r15d.rows.txt
S3_r15d.summary.txt
build_manifest.txt
clean_rebuild_correction.txt
gate_summary.txt
gate_validation.txt
hunk_map_updated.md
independent_QA.txt
kf_bench_11.raw.txt
kf_bench_13.raw.txt
kf_go_perft_5.raw.txt
map_summary.txt
publication_missing.json.txt
publication_verified.json.txt
r15d_bench_11.raw.txt
r15d_bench_13.raw.txt
r15d_go_perft_5.raw.txt
raw
raw_manifest.json.txt
stamps.txt

forge-combo29/dot/job14/raw:
K1.part001.txt
K1.part002.txt
K1.part003.txt
K1.part004.txt
K1_preclean.part001.txt
K1_preclean.part002.txt
K1_preclean.part003.txt
K1_preclean.part004.txt
K3_count.part001.txt
K3_count.part002.txt
K3_count.part003.txt
K3_count.part004.txt
K3_count_preclean.part001.txt
K3_count_preclean.part002.txt
K3_count_preclean.part003.txt
K3_count_preclean.part004.txt
K3_r15d.part001.txt
K3_r15d.part002.txt
K3_r15d.part003.txt
K3_wrong.part001.txt
K3_wrong.part002.txt
K3_wrong.part003.txt
K3_wrong.part004.txt
K3_wrong_preclean.part001.txt
K3_wrong_preclean.part002.txt
K3_wrong_preclean.part003.txt
K3_wrong_preclean.part004.txt
S1.part001.txt
S1.part002.txt
S1.part003.txt
S1.part004.txt
S1.part005.txt
S1.part006.txt
S1.part007.txt
S1.part008.txt
S1.part009.txt
S1.part010.txt
S1.part011.txt
S1.part012.txt
S1.part013.txt
S1.part014.txt
S1.part015.txt
S1.part016.txt
S1.part017.txt
S1.part018.txt
S1.part019.txt
S1.part020.txt
S2.part001.txt
S2.part002.txt
S2.part003.txt
S2.part004.txt
S2.part005.txt
S2.part006.txt
S2.part007.txt
S2.part008.txt
S2.part009.txt
S2.part010.txt
S2.part011.txt
S2.part012.txt
S2.part013.txt
S2.part014.txt
S2.part015.txt
S2.part016.txt
S2.part017.txt
S2.part018.txt
S2.part019.txt
S2.part020.txt
S2.part021.txt
S2.part022.txt
S2.part023.txt
S2.part024.txt
S2.part025.txt
S2.part026.txt
S2.part027.txt
S2.part028.txt
S2.part029.txt
S2.part030.txt
S2.part031.txt
S3_count.part001.txt
S3_count.part002.txt
S3_count.part003.txt
S3_count.part004.txt
S3_count.part005.txt
S3_count.part006.txt
S3_count.part007.txt
S3_count.part008.txt
S3_count.part009.txt
S3_count.part010.txt
S3_count.part011.txt
S3_count.part012.txt
S3_count.part013.txt
S3_count.part014.txt
S3_count.part015.txt
S3_count.part016.txt
S3_count.part017.txt
S3_count.part018.txt
S3_count.part019.txt
S3_count.part020.txt
S3_r15d.part001.txt
S3_r15d.part002.txt
S3_r15d.part003.txt
S3_r15d.part004.txt
S3_r15d.part005.txt
S3_r15d.part006.txt
S3_r15d.part007.txt
S3_r15d.part008.txt
S3_r15d.part009.txt
S3_r15d.part010.txt
S3_r15d.part011.txt
```
