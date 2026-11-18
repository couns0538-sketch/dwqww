# Dot Job 16

## 1. Step 0: PASS
Unchanged r15d SHA256bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6 and kF SHA256340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea. No options/no loaded net; fresh process per command. Both bench11=312866 nodes,bench13=862329 nodes,go perft5=4865609 nodes. Six complete raw logs committed.

## 2. Part A: scripts, declared divergence and result
Four UCI command-text scripts L2_r15d.uci.txt,L2_kf.uci.txt,L2c_r15d.uci.txt,L2c_kf.uci.txt were committed and fully read back BEFORE running. Comments describe synchronization and are not sent to the engine. L2 pair identical; L2c_r15d identical to baseline. Declaration81ad8e0656645b728d37c541cf58c30eee93af40 precedes prediction7b2c2fc3491ec12f0024beef7ee420ce51c5a1e3 and all runs.
W1 entries61..120,60searches per process,depth9,PC20/net768,T1,initialHash16. Before local searches11,21,31,41,51 respectively: Hash1;ucinewgame;HistRework0;HistRework2 plus net reload/NNUEArchtrue;Hash16. isready before each search. No other reset between them.
First differing physical script line276, before local search41(W1entry101):
```text
L2/L2c-r15d: setoption name HistRework value 2
L2c-kF:     setoption name HistRework value 0
```
Baseline next two commands reload the same net file and enable NNUEArch; control omits both. Control's later physical line numbers therefore shift by2. First differing search go command is baseline282/control280.

Reading: SHOWN LIVE under the newly declared criterion. L2 all60 bestmoves and all60 final-info lines excluding ONLY time/nps agree; hashfull retained. L2c first40 agree and first deterministic difference is41. Prediction L2equal/L2cfirstdiff41 both PASS. This is finite session-level evidence for H85, not independent per-field/per-use proof of every lazy cache or NNUE lifecycle path. Compound HistRework+reload transition does not isolate the two causes.

L2:60searches/program; last-completed-depth info-node sums r15d=932306,kF=932306.
Difference counts: {"bestmove": 0, "exact_final_info": 40, "canonical_except_time_nps": 0, "hashfull": 0}
First differing searches: {"bestmove": null, "exact_final_info": 1, "canonical_except_time_nps": null, "hashfull": null}
First40bestmove/canonicalinfo equal=True.
L2c:60searches/program; last-completed-depth info-node sums r15d=932306,kF=950331.
Difference counts: {"bestmove": 11, "exact_final_info": 44, "canonical_except_time_nps": 20, "hashfull": 18}
First differing searches: {"bestmove": 41, "exact_final_info": 2, "canonical_except_time_nps": 41, "hashfull": 41}
First40bestmove/canonicalinfo equal=True.
Firstbehavioral difference: search41; r15d go-scriptline282; kF go-scriptline280; FEN 4r3/pb6/p1qkpn2/8/2p1R1Q1/7P/1PP2PP1/R5K1 w - - 13 39
r15d info depth 9 seldepth 19 score cp 353 nodes 10770 nps 1795000 hashfull 77 time 6 pv e4e1 f6g4 a1a6 b7a6 g1h1 c6b6 h3g4
r15d bestmove e4e1
kF info depth 9 seldepth 18 score cp 195 nodes 6881 nps 2293666 hashfull 51 time 3 pv g4e6 d6c7 e6c6 b7c6 a1a6 f6e4 g2g4 e8e7 f2f3 e4g3
kF bestmove g4e6
Canonical comparison excludes ONLY time and nps; hashfull retained. All raw lines preserved. Parting command physical line276 beforesearch41, declared before runs. See raw scripts/hashes for exact provenance.

## 3. Part B: literal repair branch; no justified engine patch
### Branch and why
Job16 PartB says ANY Job15 disagreement selects repair. Job15 reported first configured fresh-pair time/nps-only exact-line disagreement; deterministic fields agreed. PartA explicitly excludes timing, but PartB did not state that exclusion, so I did not silently reinterpret its branch or invent a nonexistent Job15 counting copy. Literal repair branch selected.

### Patches and proof status
No engine patch proposed; SHA256 not applicable. No source modifications or repaired binary. Both timing formulas are identical and correctly report independent measured durations. A patch that zeroes/fakes time or NPS would conceal telemetry, not repair an established defect. Consequently no repaired K1/S1 proof is supplied. BranchN C-count7/new-counter gates and prediction are not applicable and were not run.

### Fresh reproduction and minimization
One exact configured first-search pair was enough to reproduce timing-only mismatch: both7372 last-completed-depth nodes and bestmove d8a5, with6ms versus4ms. Complete commands saved in PartB_pair1_r15d.uci.txt and PartB_pair1_kf.uci.txt. No additional configured pairs tried.
Then repeated both smaller variants fresh threepairs each, all raw transcripts and versions retained:
- V2: original firstFEN plus go depth9, no options/net;16956 last-completed-depth nodes per run, rawdiff3/3, deterministicfields/bestmoveequal3/3.
- V3: just go depth9 from default startposition, no options/net;9653nodes per run, rawdiff3/3, deterministicfields/bestmoveequal3/3.
Wait for bestmove before quit. V3 is one search command, the smallest command-count demonstration found; removing it yields no final-info. V2 changes settings, V3 also changes board; they minimize the timing-discrepancy CLASS, not the original7372-node trace. No shortest-byte or always-unequal-timing claim.

### Source cause
kF src/search.cpp3217–3221 and r15d2715–2719 both sample steady_clock elapsed integer milliseconds and calculate elapsed>0 ? nodes*1000/elapsed :0. kF3257–3262/r15d2755–2760 print these measured fields. No counterpart r15d semantic line behaves otherwise. Independent process timing can vary despite identical deterministic outputs; raw exact inequality does not alone establish an engine defect.
A sound fixed-depth comparison can explicitly preserve raw telemetry, validate time/NPS arithmetic and compare the remaining fields. PartA now does exactly the specified exclusion; PartB's literal repair claim is not retroactively called satisfied by normalization.

### Prediction graded
Immutable7b2c2fc3491ec12f0024beef7ee420ce51c5a1e3 before allA/B runs: PartA equal and firstdifference41, bothPASS. PartB has no new counters, so no use-range prediction applicable. Qualitative expectation deterministicfieldsstable/timingmaydiffer observed, not a quantified counter prediction.

### Fresh raw extracts and reopened source evidence
Job16 Part B fresh first-disagreement reproduction. Same original PC20/net768 first-W1 setup; one pair, with up to two additional pairs only if raw final-info coincides. No ucinewgame. All attempts retained; no source changes.
Pair1: exact final-info equal=False; excluding only time/nps equal=True; bestmove equal=True.
r15d info depth 9 seldepth 19 score cp -74 nodes 7372 nps 1228666 hashfull 1 time 6 pv d8a5 d1e1 g7g6 e5g4 f6g4 e2g4 d7f6 g4e6 e7d8 e6c8
r15d bestmove d8a5
kF info depth 9 seldepth 19 score cp -74 nodes 7372 nps 1843000 hashfull 1 time 4 pv d8a5 d1e1 g7g6 e5g4 f6g4 e2g4 d7f6 g4e6 e7d8 e6c8
kF bestmove d8a5
Nodes are last-completed-depth info nodes. This repeats the original configured first-search script, not a new globally minimal script claim. No repair or repaired K1/S1 proof supplied.

Fresh unchanged builds; three repetitions each version. Node count from last completed-depth info.
V2_nooptions_same_position: exact final-info differences 3/3; deterministic final-info equal 3/3; bestmoves equal 3/3; nodes r15d [16956, 16956, 16956], kF [16956, 16956, 16956].
First differing pair, repeat1:
info depth 9 seldepth 19 score cp -7 nodes 16956 nps 1059750 hashfull 4 time 16 pv d7e5 f4e5 b7b5 b2b3 c8b7 a2a4 h7h6 a4b5 a6b5 a1a8
info depth 9 seldepth 19 score cp -7 nodes 16956 nps 1211142 hashfull 4 time 14 pv d7e5 f4e5 b7b5 b2b3 c8b7 a2a4 h7h6 a4b5 a6b5 a1a8
V3_nooptions_startpos: exact final-info differences 3/3; deterministic final-info equal 3/3; bestmoves equal 3/3; nodes r15d [9653, 9653, 9653], kF [9653, 9653, 9653].
First differing pair, repeat1:
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 1206625 hashfull 2 time 8 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 1379000 hashfull 2 time 7 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5

Job16 Part B source audit 2026-11-18T20:47:33.549015+00:00
Read full assignment and reopened unchanged source. The stated Part B ANY-disagreement rule selects the repair branch because Job15 first V1 pair disagreed only on time/nps. Part A now explicitly excludes those fields; that clarification is not written into Part B, so no silent branch reinterpretation is made. No new counters or hypothetical counting copy exist from Job15.
Reopened kF src/search.cpp3215-3223,3255-3263 and r15d2713-2721,2753-2761: both sample duration_cast<milliseconds>(steady_clock::now()-start_).count(); both select nodes from node_override or total_nodes; both use elapsed>0 ? nodes*1000/elapsed :0; both print measured nps/time. This is identical timing semantics, not a counterpart line behaving otherwise. Independent runs may have different sampled durations even at identical fixed-depth search fields. Job15 already demonstrates within-build variation; those are prior observations, not a Job16 experiment.
The raw final-info comparison genuinely fails when timing differs, but that does not establish a semantic engine defect. Preserving truthful telemetry is preferable to a fake deterministic-output patch. No engine patch, repaired binary, or repaired K1/S1 proof is warranted from this finding. A fixed-depth test may explicitly compare other fields and check timing arithmetic separately, while preserving raw output. That is an oracle-scope clarification, not a claimed repair or retroactive literal pass.
Fresh reproduction results are separate artifacts after Step0 release; this source-only preparation performs no native search. A later H85 map update depends exclusively on Part A's declared L2/L2c control succeeding and must retain finite-script/compound-transition limitations.

## Map again
H85 now PARTIAL_SESSION, based ONLY on declared PartA positivecontrol;29→28NONE. All86 original IDs/ranges unchanged. Next ranked uncovered rows H71(24changedlines) and H12(22). This session result does not prove every H85 field or unseen lifecycle transition. No new PartB counter coverage.
# Job16 updated86-hunk coverage map
All86 original IDs/files/ranges retained. Only H85 changes NONE to PARTIAL_SESSION after declared L2/L2c control PASS. NONE29 to28. Partial session evidence is not exhaustive proof.
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
|85|include/forge/search.hpp|645-694|50|Lazy threat/cache scratch fields, NNUE snapshots, TT-fast Worker dispatch|PARTIAL_SESSION: Job16 declared L2/L2c session control: W1 entries61..120; all60 L2 bestmoves/final-info excluding only time/nps equal; L2c first40 equal and first difference41 after declared compound HistRework/reload divergence.|Finite T1 session differential only; compound HistRework2+net reload versus HistRework0 without reload does not isolate every readiness/cache field, net reload, valid TT handle, or concurrent lifecycle. No per-use independent state oracle.|
|86|include/forge/search.hpp|731-745|9|Single-worker node-only stop shortcut, and initialize its eligibility|NONE: NONE|Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter|

## Remaining search-read NONE rows ranked by changed lines
|Rank|Hunk|File/range|Changedlines|Equality condition|Distinguishing class|
|---:|---:|---|---:|---|---|
|1|71|include/forge/b4.hpp:37-62|24|Only read by_type for actually-present mover; no caller requests absent type|Queen promotion, cached map invalidation, synthetic requests for absent piece mask|
|2|12|src/board.cpp:1536-1564|22|Actual no-enemy-attacker gather must equal first r15d loop gather; factored live mask must exclude captured/origin pieces correctly.|EP/capture x-ray, blocked sliders becoming unblocked, pawn/king/contact-only recaptures; HOIST0 branch not in current build.|
|3|30|src/search.cpp:1635-1658|21|Preserve full pseudo-legal scored list and tie swaps, discard exactly same moves including promotions sharing from/to|Equal-score legal/illegal evasions, underpromotions, TT move amid ties|
|4|3|src/board.cpp:852-872|15|When not in check, an off-king-ray pawn push/capture cannot expose ownking; no enemy geometric slider ray implies zero absolute pins.|Stalemate/nearly stalemated sparse position, pinned pawn, promotion push/capture, occupancy opening diagonal or file.|
|5|36|src/search.cpp:1883-1909|15|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|6|11|src/board.cpp:1516-1534|14|Contact+empty-board enemy slider-ray absence implies no first legal recapture and fullSEE result true.|EP removes blocker, origin vacates x-ray, promotionrecapture at backrank, pinned or defended king recapture.|
|7|29|src/search.cpp:1568-1583|13|Generation finishes copying/scoring before recursion can overwrite shared scratch|Nested evasion search and promotion ties|
|8|86|include/forge/search.hpp:731-745|9|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|9|37|src/search.cpp:1965-1976|7|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|10|32|src/search.cpp:1748-1760|6|Guard supersets all dead-material cases; snapshots stable because option changes stop search|Unusual recognized endings and backend reload/disable transitions|
|11|35|src/search.cpp:1867-1881|5|Null changes no material and backend state prepared before search|Null nodes with material-index valid/invalid and V3 on|
|12|52|src/search.cpp:3383-3394|5|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|13|33|src/search.cpp:1819-1829|4|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|14|42|src/search.cpp:2325-2333|4|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|15|47|src/search.cpp:2679-2686|4|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|16|2|src/board.cpp:834-841|3|Excluded pawn/king attacked squares must always fail full own-king safety even after capture.|King capture onto pawn-defended square, capture of checking pawn, nearby enemyking; illegal synthetic king adjacency outside accepted-board contract.|
|17|20|src/search.cpp:944-950|3|Preserve full pseudo-legal scored list and tie swaps, discard exactly same moves including promotions sharing from/to|Equal-score legal/illegal evasions, underpromotions, TT move amid ties|
|18|39|src/search.cpp:2121-2127|3|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|19|75|include/forge/eval.hpp:51-59|3|Full dead_material_score rejects every position containing pawn/rook/queen before changing score; caller must preserve that same condition.|Enable dead-material option, promotion/last-heavy-piece capture, mixed minor endings; stale piece bitboards or expanded recognition could break prefilter.|
|20|84|include/forge/search.hpp:533-541|3|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|21|17|src/search.cpp:21-27|2|Only overwrites already-consumed prefix; bad_count <= consumed index; preserves bad-capture order|Capture-rich nodes, many losing captures, equal scoring moves|
|22|24|src/search.cpp:1079-1085|2|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|23|38|src/search.cpp:2100-2106|2|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|24|40|src/search.cpp:2255-2261|2|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|25|41|src/search.cpp:2277-2283|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|
|26|45|src/search.cpp:2407-2413|2|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|27|46|src/search.cpp:2437-2443|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|
|28|51|src/search.cpp:3337-3343|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|


## Provenance
Original GCC14.2.0/CMake4.4.5/libstdc++.so.6.0.33/glibc2.41 Release C++20,O3,NDEBUG,strictFP,marchx86-64-v4 binaries, hashesabove. PC20:Threads1,Hash16,OwnBookfalse,LmrQuietBase93,LmrQuietDivisor205,LmrNoisyBase13,LmrNoisyDivisor333,LmrHistoryDivisor5643,NullMoveBase5,LmpBase8,HistoryPruneMultiplier2220,HistoryBonusQuadratic24,HistoryBonusLinear54,HistoryBonusMax2212,SingularDepth6,IirDepth2,NonPawnCorrectiontrue,CuckooReptrue,HistRework2,TtPruneV2true,CorrHistV2true,MateAlphaGuardtrue, except declaredsessiontransitions. These PC20/net settings apply to Part A and configured PartB pair, NOT V2/V3: the no-option minimal variants use default Hash32 and no loaded net. Synthetic v3 hidden768 net checksum30ab43b4ba5db5f3, SHA256c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7. W1SHA2563c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521. Net/standalonepositions remainlocal. Every reported search-node sum above explicitly uses last completed-depth info, not independent total softnodes.

## Facts
Claim20:46:14 UTC; nativecutoff21:36:14/reportdeadline21:46:14. Part A scripts and prediction committed before runs; Part B script files record commands actually tried and were saved after their respective runs. Native work finished early. Declared L2control fixes the previous ambiguous31/41 instruction and is live on new W1entries. Literal PartB repeats timing-only variability without a semantic mismatch.

## Suspicions
No new engine bug demonstrated. H85 has finite session evidence now, not a complete cache/lifetime proof. The repeated timing-only repair branch reflects oracle wording rather than an identified incorrect engine calculation.

## What I did not do
No fake engine patch, no repaired-binary gate proof, no new PartB counters, no speed/Elo claim, no PC compiler/net, no multithread; Part A uses only Hash1/16, no standalone dataset/net/binary committed. Auxiliary skill auditor unavailable and not run; independent source/raw QA and native harness gates are separate checks.

## What I am not sure about
Unseen states, timing-managed searches, concurrency and individual contributions of HistRework versus reload remain unisolated. Correct timing fields can coincide or differ across fresh runs. Minimal variants alter configuration/position as disclosed.

### What this check cannot see
Positions and sessions these scripts do not reach; transitions other than the five; the PC's net, compiler and
build; more than one search thread; Hash sizes other than 1 and 16.

The preceding required limitation text is retained verbatim. Scope clarification: Part A tested only Hash1/16, while no-option V2/V3 minimization used default Hash32 without loaded net; those are timing-class demonstrations, not additional session-state coverage.

## Publication
All29 queued evidence files fully read back20:56:21UTC:414401bytes,max84392;18complete rawtranscripts,4PartBscriptversions,prose,map andQA. SixStep0rawlogs, fourPartAscripts+declaration andimmutableprediction separately published/readbackverified before runs. publication_verified.json.txt records the29file batch. No missing evidence/errors/denials; derived per-search localJSON remainslocal. Jobtotalunder700KB, eachfileunder100KB. No standalonepositions/net/game dataset uploaded. Last localcheckoutstatus preserves evidence, not remoteengine source edits.

## FOR FABLE AND OPUS
PartA now shown live as declared. PartB literalANYdisagreement again selected timing-only repair branch; no valid engine repair was warranted. For subsequent uncovered-row work, please make the deterministic-field exclusion explicit in branch rules too. Nextjob wait is latestFinnONEHOUR, capped2026-11-19T06:16:10Z.

## Last command before report commit
```text
git status --short; ls -R forge-combo29/dot/job16
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job10.md
?? forge-combo29/REPORT_dot_job11.md
?? forge-combo29/REPORT_dot_job12.md
?? forge-combo29/REPORT_dot_job13.md
?? forge-combo29/REPORT_dot_job14.md
?? forge-combo29/REPORT_dot_job15.md
?? forge-combo29/REPORT_dot_job16.md
?? forge-combo29/REPORT_dot_job6.md
?? forge-combo29/REPORT_dot_job7.md
?? forge-combo29/REPORT_dot_job8.md
?? forge-combo29/REPORT_dot_job9.md
?? forge-combo29/dot/job10/
?? forge-combo29/dot/job11/
?? forge-combo29/dot/job12/
?? forge-combo29/dot/job13/
?? forge-combo29/dot/job14/
?? forge-combo29/dot/job15/
?? forge-combo29/dot/job16/
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
forge-combo29/dot/job16:
L2_kf.raw.txt
L2_kf.rows.local.json
L2_kf.uci.txt
L2_r15d.raw.txt
L2_r15d.rows.local.json
L2_r15d.uci.txt
L2_results.txt
L2_script_declaration.txt
L2c_kf.raw.txt
L2c_kf.rows.local.json
L2c_kf.uci.txt
L2c_r15d.raw.txt
L2c_r15d.rows.local.json
L2c_r15d.uci.txt
PartB_pair1_kf.raw.txt
PartB_pair1_kf.uci.txt
PartB_pair1_r15d.raw.txt
PartB_pair1_r15d.uci.txt
PartB_reproduction.txt
PartB_source_audit.txt
V2_nooptions_same_position.repeat1.kf.raw.txt
V2_nooptions_same_position.repeat1.r15d.raw.txt
V2_nooptions_same_position.repeat2.kf.raw.txt
V2_nooptions_same_position.repeat2.r15d.raw.txt
V2_nooptions_same_position.repeat3.kf.raw.txt
V2_nooptions_same_position.repeat3.r15d.raw.txt
V2_nooptions_same_position.uci.txt
V3_nooptions_startpos.repeat1.kf.raw.txt
V3_nooptions_startpos.repeat1.r15d.raw.txt
V3_nooptions_startpos.repeat2.kf.raw.txt
V3_nooptions_startpos.repeat2.r15d.raw.txt
V3_nooptions_startpos.repeat3.kf.raw.txt
V3_nooptions_startpos.repeat3.r15d.raw.txt
V3_nooptions_startpos.uci.txt
gate_summary.txt
hunk_map_updated.md
independent_QA.txt
kf_bench_11.raw.txt
kf_bench_13.raw.txt
kf_go_perft_5.raw.txt
map_summary.txt
minimize_results.local.json
minimize_summary.txt
publication_verified.json.txt
r15d_bench_11.raw.txt
r15d_bench_13.raw.txt
r15d_go_perft_5.raw.txt
```
