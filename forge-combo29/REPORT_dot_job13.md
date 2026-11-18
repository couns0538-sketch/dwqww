# Dot Job 13

## 1. Step 0: PASS
Unchanged r15d bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6 and kF 340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea, no options/no loaded net, fresh process per command: both bench 11 = 312866 nodes; bench 13 = 862329 nodes; go perft 5 = 4865609 nodes. Six full raw logs in dot/job13.

## 2. C-count4 patch and build
C_count4_full.patch.txt SHA256 e40d6422b0b3d14b785f68a0f74e0cc1eba5758b43c7a313c81f761cc9aa5d0b; C_wrong4_full.patch.txt SHA256 e2375465f57dbc7b0a7d40ca010bc445a4a3686cdf92bedf5f4f4e697dcd7414. Both apply to original kF scratch source; incremental patches from Job12 also supplied. No repository engine source modified.
C-count4 binary SHA256 f377c80fc7135b173718f54e94ff33b560756cd87b8af62bc3a742b3f8330e77; C-wrong4 f2ad6c29b3cf28d54a5fb218c902f8353414d1066dc0f0d26de0f75de6e3a9c9. GCC14.2.0, CMake4.4.5, libstdc++.so.6.0.33, glibc2.41; C++20 Release O3 NDEBUG, strict FP, march=x86-64-v4. Full flags/configure/build logs in dot/job13/build_manifest.txt and matching logs. Old WRONG/WRONG2/WRONG3 controls disabled.

## 3. K1 and class-specific controls: PASS
Only first 200 W1 entries (197 distinct), depth9, PC20/net768, 4097080 nodes each. Every nodes/bestmove row unchanged against preserved baseline; all ten old counters exactly Job12 K2 uses and zero differences. H27 control adds one to the private reference score ONLY for captures made by an existing knight. H25 control chooses last rather than first maximum ONLY when highest scores tie. Neither changes search-used values.

| Counter | K1 uses | K1 differ | K2 uses | K2 differ |
|---|---:|---:|---:|---:|
| B1 | 2564528 | 0 | 2564528 | 0 |
| B2 | 2689044 | 0 | 2689044 | 0 |
| B5 | 2607489 | 0 | 2607489 | 0 |
| B6 | 3895460 | 0 | 3895460 | 0 |
| S-B1 | 2564528 | 0 | 2564528 | 0 |
| S-B2 | 2689044 | 0 | 2689044 | 0 |
| S-B4 | 2564528 | 0 | 2564528 | 0 |
| S-B7 | 3895323 | 0 | 3895323 | 0 |
| H28 | 341487 | 0 | 341487 | 0 |
| H18 | 2063485 | 0 | 2063485 | 0 |
| H27 | 1124811 | 0 | 1124811 | 129188 |
| H25 | 5483925 | 0 | 5483925 | 923057 |

Both new controls have 0 < differences < uses. First five raw diagnostics (not a standalone position dataset):
```text
info string shortcut disagreement H27 premove_fen r1bq1rk1/1p1nbppp/p3pn2/3pN3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 b - - 0 11 move d7e5
info string shortcut disagreement H27 premove_fen r1bq1rk1/1p2bppp/p3pn2/3pn3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 w - - 0 12 move d2c4
info string shortcut disagreement H25 premove_fen r1bq1rk1/1p2bppp/p3pn2/3pn3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 w - - 0 12 move d4e5
info string shortcut disagreement H25 premove_fen r1bq1rk1/1p2bppp/p3pn2/3pn3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 w - - 0 12 move e2c4
info string shortcut disagreement H25 premove_fen r1bq1rk1/1p1nbppp/p3pn2/3pN3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 b - - 0 11 move a6a5
```

## 4. Prediction graded: all PASS
Immutable prediction commit 35c323ab220abb836a64337c1155ebbd8cd4649d, after 200-entry gates and before full S1/S2. S1 began 19:14:03 UTC; no full 1000-entry new-counter run preceded prediction.
| Run/counter | Predicted uses | Actual uses | Predicted/actual differences |
|---|---:|---:|---:|
| S1 H27 | 3800000–5300000 | 5029379 | 0 / 0 |
| S1 H25 | 18000000–26000000 | 23565361 | 0 / 0 |
| S2 H27 | 1100000–1900000 | 1610870 | 0 / 0 |
| S2 H25 | 6000000–10000000 | 6954922 | 0 / 0 |
Ranges extrapolated the 200-entry K1 and previous workload sizes, not blind to prior workloads, but before these full new-counter workloads.

## 5. S1 and S2: PASS
S1: 1000 W1 entries, 990 distinct positions, depth9, 16543291 nodes; every nodes/bestmove row matches Job7 and all ten old per-row counters match Job12. S2: same first20 distinct W1 starts, 20 games, 1370 legal plies/searches, 5612423 actual nodes, all old per-ply counters and full game moves equal Job12. All games terminal under claim_draw=True before the 200-ply cap. No per-game dataset published.
S2 uses go softnodes2000, full move history per ply, ucinewgame/isready per game. Actual nodes come from softnodes total, not last completed-depth info. Opus's Job12 introductory 4569803 is the sum of last completed-depth info nodes; actual softnodes total was 5612423. These are distinct metrics, not a gate discrepancy.

| Counter | S1 uses | S1 differ | S2 uses | S2 differ |
|---|---:|---:|---:|---:|
| B1 | 9079813 | 0 | 3212417 | 0 |
| B2 | 9638809 | 0 | 3468791 | 0 |
| B5 | 10935512 | 0 | 4071447 | 0 |
| B6 | 15430637 | 0 | 5227491 | 0 |
| S-B1 | 9079813 | 0 | 3212417 | 0 |
| S-B2 | 9638809 | 0 | 3468791 | 0 |
| S-B4 | 9079813 | 0 | 3212417 | 0 |
| S-B7 | 15531178 | 0 | 5255554 | 0 |
| H28 | 1376393 | 0 | 493901 | 0 |
| H18 | 9040060 | 0 | 2638740 | 0 |
| H27 | 5029379 | 0 | 1610870 | 0 |
| H25 | 23565361 | 0 | 6954922 | 0 |

### Reference scope and exercised paths
H25 counter: one use per pick_best_scored call/return, including seeded first pick, SIMD16/8/4/scalar selection, unchanged std::sort transition and already-sorted tail. A private array copy of initialized remaining Scored entries is made before production selection. For initial four selections and sorted tail the reference is a plain ascending-index highest-score scan with strict >, preserving earliest maximum. At the fifth unsorted selection r15d itself uses unstable std::sort: the private reference first performs the identical r15d sort comparator on the copied tail and then scans. It does not use the actual post-sort list as its reference. It validates returned move+score, not a complete equality check of post-selection array permutation. Later per-return checks may detect consequential ordering changes, but no claim of independently proving std::sort implementation.
Wrong4 changes strict > to >= in reference scan only. A differing return thus requires tied maximum scores with distinct Move values; duplicate Move::none tagged evasion slots can share a maximum yet produce no disagreement. Unique maximum returns stay equal. H27 control independently changes knight-capture reference score only. Old WRONG, WRONG2, WRONG3 undefined in both builds. Search-used fields are untouched except unchanged original implementation; references only local arrays/histories read, diagnostic counters/output.
Extra per-search info string h25_paths counts seeded, scan16, scan8, scan4, scalar_tail, sort_transition, sorted_tail. SIMD/scalar bins record calls that traverse each path, not chunk counts, and overlap within a call. An unseeded singleton scan may contribute no scan bin. These bins are source-derived from same branch conditions/remaining lengths and actual build macros, not individual intrinsics performance measurements. x86-64-v4 enables AVX512/AVX2 paths in this build; other architectures remain untested.
H27 cross-review: local r15d generate_pseudo_legal(captures_only=true), captured_piece handles EP; scalar history scores and promotion gain/bonus exactly original formulas. Ordered list, all Move fields, score and seed metadata compared once per capture-generation invocation. Knight-capture control requires original moving piece Knight, not pawn promoting to Knight. No extra make/unmake or prior counter calls. Both full patches dry-run clean, compiler/build manifest stored.

UTC: 2026-11-18 19:12:13 (observed date -u). H27 frozen after apply_patch at observed19:11:44.

H27 source and reference
Read original r15d src/search.cpp1030-1053 and kF capture generation (job12-count scratch1364-1480 before additions). r15d generates a separate capture list, reads moved/victim piece IDs, scores10*(victim value+promotion delta)+capture-history, then applies queen-promotion+20000/underpromotion-5000. Reference uses the same old separate Board generator and reproduces the scalar scoring expression, while actual kF fused generation remains untouched in generate_captures_impl. The wrapper observes once after every capture-generation call, including empty lists and fallback path. Compare count,index0,list_start0,sorted=false, every move and score in order, seed-valid/seed-score/seed-position under earliest strictly-greater rule. A count mismatch detects extra/missing actual moves. Reference list and score/seed variables are local; it does not write picker scratch, search histories, actual moves, or board state. Board::captured_piece independently handles en-passant as pawn instead of reading an empty destination. Quiet promotions remain in the capture-generator list and are scored under the same promotion rules.

Wrong4 control changes only reference score+1 when move.is_capture() and piece_type(board.piece_at(move.from))==Knight. This means captures BY existing knights, not pawn promotions TO knights. It changes no search value. H27 uses count is per generated list, not per move; one or several knight captures in that list produces one differing use. Empty lists, non-knight captures and promotions without a knight capture remain unaffected. Runtime must establish0<differ<uses; source reasoning is not a substitute for that test.

Limitations: Board capture generator, attack tables, captured-piece helper, history tables and piece values are shared existing helpers, so this checks fused-path equivalence to the prior separate algorithm, not independent absolute chess correctness or history-update correctness. No extra old counter calls are introduced directly; the completed dynamic checks verify old counter equality. Buffer capacity and legal-position contracts are inherited. Inactive compile branches and unreached moves remain untested. Nothing here establishes the owner's PC compiler/net behavior, other threads, or unseen positions.

Independent H25 source review
Read new wrapper in scratch src/search.cpp1255-1297, underlying implementation, and original r15d search.cpp960-1009. Reference copies current unconsumed scored entries, reproduces the fifth-pick std::sort transition on private storage, then plain-scans for first maximum. Before transition this matches r15d strict-greater earliest-index tie rule; after transition identical std::sort input/comparator reproduces old tail order. On already-sorted tail first maximum is first entry. Actual function runs only once, and returned move+score are compared. Wrong4 >= scan changes choice only when multiple remaining moves share maximal score. No mismatch found on source review. Reference array capacity256 matches actual scored-list capacity256. Runtime guards and actual SIMD16/8 path counters are necessary before claiming wide-path reach; aggregate H25 uses includes seed, scalar, sorting and sorted-tail paths. Shared std::sort means this does not independently prove standard-library ordering behavior, and returned-value comparison does not compare every internal swap/list mutation at the instant it occurs.

H25 path counts from complete raw transcripts; bins overlap and are not a partition:
```text
K1 h25_paths {"seeded": 1029039, "scan16": 746261, "scan8": 427588, "scan4": 529770, "scalar_tail": 1095655, "sort_transition": 289397, "sorted_tail": 2545512}; bins overlap/notpartition.
K2 h25_paths {"seeded": 1029039, "scan16": 746261, "scan8": 427588, "scan4": 529770, "scalar_tail": 1095655, "sort_transition": 289397, "sorted_tail": 2545512}; bins overlap/notpartition.
S1 h25_paths {"seeded": 4977423, "scan16": 2824781, "scan8": 1738412, "scan4": 2200713, "scalar_tail": 4923074, "sort_transition": 1228744, "sorted_tail": 9934549}; bins overlap/notpartition.
S2 h25_paths {"seeded": 1590361, "scan16": 701317, "scan8": 457745, "scan4": 679791, "scalar_tail": 1391729, "sort_transition": 357185, "sorted_tail": 2838031}; bins overlap/notpartition.
```

### Workload/build provenance
PC20: Threads1, Hash16, OwnBookfalse, LmrQuietBase93, LmrQuietDivisor205, LmrNoisyBase13, LmrNoisyDivisor333, LmrHistoryDivisor5643, NullMoveBase5, LmpBase8, HistoryPruneMultiplier2220, HistoryBonusQuadratic24, HistoryBonusLinear54, HistoryBonusMax2212, SingularDepth6, IirDepth2, NonPawnCorrectiontrue, CuckooReptrue, HistRework2, TtPruneV2true, CorrHistV2true, MateAlphaGuardtrue. Each W1 search resets ucinewgame/isready. Synthetic v3 hidden768 net checksum30ab43b4ba5db5f3, SHA256 c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7; W1 SHA256 3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521. Net and standalone positions remain local, never uploaded here.
Original r15d stack base6b98f2170a3210e71beed04bbd2553972c253ed7 plus PCr15/carbon2/E1; kF adds finalstack patch SHA2563d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30. Frozen original binaries listed in Step0.

## 6. Map again
All86 original hunk IDs/ranges preserved. Exactly H18/H25/H26/H27/H28 change from NONE to PARTIAL_DIRECT: 35 minus5 = 30 NONE. H82 remains NONE: shared replacement checks do not independently cover owned SIMD hit/empty probe. Ranking and complete map follow.
# Job13 updated86-hunk coverage map

Same original diff/ranges asJob12; no hunks added/removed. Rows18,25,26,27,28 updated from NONE to PARTIAL_DIRECT based on Job12/13 references and class-specific controls. NONE count35→30. PARTIAL_DIRECT means direct evidence for specified exercisedfacet, NOT exhaustiveproof. H82 remainsNONE: H18 covers shared replacement only, not ownedAVX512 probe hit/empty-mask output. All original conditions/classes retained. Broadgame/sanitizer claims are not substitutes for direct mechanism comparison; externalhelper results remain Opus-reported.

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
|18|src/search.cpp|525-661|131|Fast TT locked probe and owned/locked store; factored full-cluster replacement|PARTIAL_DIRECT: Job12 H18 and Job13 retained counter: scalar snapshot references for replacement/lockedprobe/owned+lockedstore under valid worker context|No direct H82 owned-AVX512 probe comparison except shared replacement; no sample-generation deltas, stale/foreign handle guard or concurrency proof.|
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
|82|include/forge/search.hpp|226-299|66|AVX512 owned TT probe and fast declarations; relocate metadata|NONE: NONE|H18 observes shared full-cluster replacement only, not this owned AVX512 hit/empty-mask probe; remains NONE for direct returned-entry/slot/cluster reference.|
|83|include/forge/search.hpp|306-322|9|Factor unchanged cluster-index arithmetic into helper|PARTIAL_OR_DIRECT: NO_BEHAVIOR|Expression identical algebraically; helper extraction no logical change|
|84|include/forge/search.hpp|533-541|3|Cache material-correction index in stack and invalidate on capture/promotion|NONE: NONE|No per-use independent mechanism test identified.|
|85|include/forge/search.hpp|645-694|50|Lazy threat/cache scratch fields, NNUE snapshots, TT-fast Worker dispatch|NONE: NONE|No per-use independent mechanism test identified.|
|86|include/forge/search.hpp|731-745|9|Single-worker node-only stop shortcut, and initialize its eligibility|NONE: NONE|Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter|

## Remaining search-read NONE rows, ranked by changed lines
|Rank|Hunk|File/range|Changedlines|Equality condition|Distinguishing class|
|---:|---:|---|---:|---|---|
|1|82|include/forge/search.hpp:226-299|66|Masks identify occupied key lane correctly; preserve earliest hit/empty/full replacement and generation updates|Full collisions, generationwrap, empty slots, AVX512 lane-layout|
|2|85|include/forge/search.hpp:645-694|50|All readiness resets and ownership proofs of related hunks hold; fast handle consumed before epoch mutation|Mixed HistRework recursion, reloaded net, owned/locked TT modes|
|3|71|include/forge/b4.hpp:37-62|24|Only read by_type for actually-present mover; no caller requests absent type|Queen promotion, cached map invalidation, synthetic requests for absent piece mask|
|4|12|src/board.cpp:1536-1564|22|Actual no-enemy-attacker gather must equal first r15d loop gather; factored live mask must exclude captured/origin pieces correctly.|EP/capture x-ray, blocked sliders becoming unblocked, pawn/king/contact-only recaptures; HOIST0 branch not in current build.|
|5|30|src/search.cpp:1635-1658|21|Preserve full pseudo-legal scored list and tie swaps, discard exactly same moves including promotions sharing from/to|Equal-score legal/illegal evasions, underpromotions, TT move amid ties|
|6|3|src/board.cpp:852-872|15|When not in check, an off-king-ray pawn push/capture cannot expose ownking; no enemy geometric slider ray implies zero absolute pins.|Stalemate/nearly stalemated sparse position, pinned pawn, promotion push/capture, occupancy opening diagonal or file.|
|7|36|src/search.cpp:1883-1909|15|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|8|11|src/board.cpp:1516-1534|14|Contact+empty-board enemy slider-ray absence implies no first legal recapture and fullSEE result true.|EP removes blocker, origin vacates x-ray, promotionrecapture at backrank, pinned or defended king recapture.|
|9|29|src/search.cpp:1568-1583|13|Generation finishes copying/scoring before recursion can overwrite shared scratch|Nested evasion search and promotion ties|
|10|86|include/forge/search.hpp:731-745|9|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|11|37|src/search.cpp:1965-1976|7|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|12|32|src/search.cpp:1748-1760|6|Guard supersets all dead-material cases; snapshots stable because option changes stop search|Unusual recognized endings and backend reload/disable transitions|
|13|35|src/search.cpp:1867-1881|5|Null changes no material and backend state prepared before search|Null nodes with material-index valid/invalid and V3 on|
|14|52|src/search.cpp:3383-3394|5|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|15|33|src/search.cpp:1819-1829|4|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|16|42|src/search.cpp:2325-2333|4|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|17|47|src/search.cpp:2679-2686|4|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|18|2|src/board.cpp:834-841|3|Excluded pawn/king attacked squares must always fail full own-king safety even after capture.|King capture onto pawn-defended square, capture of checking pawn, nearby enemyking; illegal synthetic king adjacency outside accepted-board contract.|
|19|20|src/search.cpp:944-950|3|Preserve full pseudo-legal scored list and tie swaps, discard exactly same moves including promotions sharing from/to|Equal-score legal/illegal evasions, underpromotions, TT move amid ties|
|20|39|src/search.cpp:2121-2127|3|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|21|75|include/forge/eval.hpp:51-59|3|Full dead_material_score rejects every position containing pawn/rook/queen before changing score; caller must preserve that same condition.|Enable dead-material option, promotion/last-heavy-piece capture, mixed minor endings; stale piece bitboards or expanded recognition could break prefilter.|
|22|84|include/forge/search.hpp:533-541|3|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|23|17|src/search.cpp:21-27|2|Only overwrites already-consumed prefix; bad_count <= consumed index; preserves bad-capture order|Capture-rich nodes, many losing captures, equal scoring moves|
|24|24|src/search.cpp:1079-1085|2|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|25|38|src/search.cpp:2100-2106|2|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|26|40|src/search.cpp:2255-2261|2|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|27|41|src/search.cpp:2277-2283|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|
|28|45|src/search.cpp:2407-2413|2|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|29|46|src/search.cpp:2437-2443|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|
|30|51|src/search.cpp:3337-3343|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|

## Facts
Claim 19:10:33 UTC, build frozen19:12:55, gates validated19:13:58, full runs completed19:14:33.604413. Minute50 native cutoff20:00:33 and deadline20:10:33. All native work completed before cutoff. Independent reparse confirms counter totals, legal moves, previous rows/per-ply counts and map preservation. No normal-reference differences observed.

## Suspicions
No new observed bug. Thirty NONE rows are gaps, not demonstrated faults. H82 is the largest remaining search-relevant uncovered hunk by changed lines (66), then H85 (50).

## What I did not do
No speed or Elo claim, no PC build/net run, no multi-thread test, no exhaustive positions, no standalone game/position dataset commit. No claim that shared generation/attack tables or std::sort are independently proved. No full remaining-array permutation comparison for H25. The auxiliary skill auditor resource was unavailable; it was not run. Native harness checks/counter gates and independent raw reparse are separate completed checks.

## What I am not sure about
Unreached paths, other architectures and compiler tie/sort behavior remain outside this observation. H18 retains sampling/lifecycle and concurrent/owned-probe gaps specified in map. Zero observed differences do not establish universal equivalence.

### What this check cannot see
Positions that W1 and the 20 games do not reach; the PC's net, compiler and build; more than one search thread.

## Publication
All71 evidence files in publication_verified.json.txt fully read back at19:34:45 UTC:5423353 bytes, max100000. All55 raw parts of K1/K2/S1/S2 included. Ledger commit01f4309ccdcec4c2b7c4910e12eacc5f478f9990 verified. Full patches, six Step0 logs, immutable prediction and complete updated map were already separately published/readback verified. Job total under6MB, each committed file under100KB. S2.summary.txt and standalone positions/move datasets remain local and are not represented as remotely published. No failed or denied publication in Job13. Local stale checkout/untracked evidence below is preserved, not a claim of uncommitted remote source changes.

## Last command before report commit
```text
git status --short; ls -R forge-combo29/dot/job13
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job10.md
?? forge-combo29/REPORT_dot_job11.md
?? forge-combo29/REPORT_dot_job12.md
?? forge-combo29/REPORT_dot_job13.md
?? forge-combo29/REPORT_dot_job6.md
?? forge-combo29/REPORT_dot_job7.md
?? forge-combo29/REPORT_dot_job8.md
?? forge-combo29/REPORT_dot_job9.md
?? forge-combo29/dot/job10/
?? forge-combo29/dot/job11/
?? forge-combo29/dot/job12/
?? forge-combo29/dot/job13/
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
forge-combo29/dot/job13:
C_count4_build.txt
C_count4_configure.txt
C_count4_from_job12.patch.txt
C_count4_full.patch.txt
C_wrong4_build.txt
C_wrong4_configure.txt
C_wrong4_from_job12.patch.txt
C_wrong4_full.patch.txt
H25_design.txt
H27_design_H25_review.txt
K1.progress.txt
K1.raw.txt
K1.rows.txt
K1.summary.txt
K2.progress.txt
K2.raw.txt
K2.rows.txt
K2.summary.txt
S1.progress.txt
S1.raw.txt
S1.rows.txt
S1.summary.txt
S2.raw.txt
S2.summary.txt
build_manifest.txt
gate_summary.txt
gate_validation.txt
hunk_map_updated.md
independent_QA.txt
kf_bench_11.raw.txt
kf_bench_13.raw.txt
kf_go_perft_5.raw.txt
map_summary.txt
publication_verified.json.txt
r15d_bench_11.raw.txt
r15d_bench_13.raw.txt
r15d_go_perft_5.raw.txt
raw
raw_manifest.json.txt
stamps.txt

forge-combo29/dot/job13/raw:
K1.part001.txt
K1.part002.txt
K1.part003.txt
K1.part004.txt
K2.part001.txt
K2.part002.txt
K2.part003.txt
K2.part004.txt
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
```
