# Dot Job18

## 1. Step0 PASS
Unchanged r15d SHA256bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6 and kF340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea, no options/net,freshprocess percommand: both bench11=312866nodes,bench13=862329nodes,go perft5=4865609nodes. Complete sixrawtranscripts bundled in step0_complete.raw.txt, verified commita1d7de9ad3d34864333cc87df2887bba101a0bcc.

## 2. BranchN and scope after interrupted Job17
Job17 partialreport4aa26eeccaeff10bb1923451d6fb9564b14014fa says no countedruns or finishedbinary, no observedcounter/search disagreement. This is not proof its unfinished draft was correct. Job18otherwise branch applies. H71/H12 were TAKEN in Job17 but unfinished and stillNONE; following literal next-not-taken rule selects H30(21changedlines) and H3(15), not a claim H71/H12 are covered. Newest VALIDATED countingbase is Job14 C-count5 with13counters, not unbuiltJob17 count8. No unsupported draft carried into native evidence.

## 3. Patches, build identity and limits
C_count9_full.patch.txt SHA25675b614076d068b4229ae77f76e6b4d657e390769aa6169a8527ab767b4f0092e; C_wrong9_full.patch.txt SHAb392205cf97ea2f3c974a021a2f9d278e4f734dd6cccd40ddce136909ef25079. Full patches against originalkF; incremental fromvalidatedJob14 also supplied. Fullpatchcommits2ecdddee88a331af66da976b8789474cea656010 and487ab642840adaf3d8f6e9b64d4438c7ae3b0a24 readbackverified.
Finalcount9 binary SHAb8d31d23d4675237fd46b98500867ec2169eaee1aad0adf895335212592e6245; wrong9 SHAf5a02ceae8a82d3e27b3b13cd9911c40db48b6df1247f7d89b2ee442815efb21. Both clean-first builds completed22:16:28UTC after ALLsourceedits frozen; no edits duringcompile. Originalengine repository sourceuntouched. GCC14.2.0,CMake4.4.5,libstdc++.so.6.0.33,glibc2.41; C++20Release,O3,NDEBUG,strictFP,marchx86-64-v4. Completeflags/logs in build_manifest andmatchinglogs. OnlyWRONG9 enabledincontrol; oldfaultmacros off.

### H30 generation-unit reference
H30 counter unit: one comparison per tied-evasion fallback generation, not each later consumed move. Before any build/run, an ambiguous coordination phrase briefly caused a per-return diagnostic draft; this was reverted to the generation unit matching the committed prediction. No per-return build/test occurred.
At generate_evasions's tie fallback, the untagged pseudo-generated moves and their existing scores are copied locally before production tags illegal slots Move::none. The production scored array remains unchanged. Two private simulations reproduce r15d's first four strict-earliest-maximum swaps followed by score-only std::sort: actual private tagged array skips None/TT, old private untagged array skips TT then uses deferred legal-from/to mask. Compare complete resulting legal Move+score sequences and their lengths. Includes all future sequence entries even if real search later cuts off. No calls to instrumented pick_best/H25 and no extra generator or history scorer calls, so existing13 hooks are not incremented by the reference.
Class white_generation/black_generation partitions uses; illegal_source and promotion_source overlap, indicating any such pseudo slot in that fallback. Wrong9 modifies first private reference output to Move::none only White-to-move tied generations; Black unaffected. Tied legal evasions imply at least two non-TT legalmoves, so first private output exists for valid inputs. Wrong class is a position class, not every use. Runtime must establish some/notall differences.
Scope: validates early-tag versus old deferred-filter equivalence in the full selected-output sequence. Shares legal generator, pseudo generator, scoring, from/to legality masks and std::sort primitive; it is not independent chess-law proof, scoring proof, actual per-return sequence observation, or independent std::sort implementation proof. Existing H25 separately covers actual selection return semantics on reached calls. Promotion equality retains r15d's from/to mask semantics; no stronger promotion-identity legality proof claimed. Counter local arrays add stack/time but do not alter search-used arrays, state, scores or board. Only T1/workload reach can be claimed after gates.

### H3 predicate reference
H3 diagnostic design frozen 2026-11-18T22:15:04Z, before counted runs.
Opened original r15d src/board.cpp845-896 and kF851-911, and FINAL Job14 count5 board.hpp/board.cpp instrumentation. One H3 use per public Board::has_legal_move call, not per candidate move or per successful witness. Actual kF body remains textually unchanged inside a bool-returning lambda and executes once. Reference is the exact original r15d has_legal_move body cloned as diagnostic member h3_has_legal_move_reference, invoked on a private Board copy captured before actual evaluation. Its fallback is_legal can refresh that copy's mutable king cache but cannot alter the real search Board. Reference uses no make/unmake or existing counted hooks, so no suppression machinery is needed. Copy allocation/time overhead is diagnostic only; no speed claim.
Four pre-call classes partition uses: 0 in_check; 1 safe_pawn_witness (not in check, at least one pawn off every own-king rook/bishop empty-board ray can single-push to an empty square or capture enemy occupancy); 2 no_ray_shortcut (not in check, no safe-pawn witness, king-lines cache invalid and no enemy rook/queen/bishop geometric ray toward king, with FORGE_SPD_KING_LINES enabled); 3 other (including valid-cache normal fallback). Class2 requires invalid cache so it measures actual reach of the new no-ray zero-pins shortcut rather than merely board eligibility. Class1 corresponds exactly to the early true return. Classes are not the number of pawn moves.
Wrong9 flips only the local reference boolean for class1. Class1 actual is true; intended wrong reference is false. This changes no search-return value, Board, history, cache or real output. Some-but-not-all difference condition must be established by native gate, not assumed. Diagnostics pass real pre-move Board and Move::none (0000), since this predicate has no selected candidate move to print.
Reference shares existing Board fields, attack primitives, pawn helpers, pseudo generator, legality implementation and pre-existing valid pinned-cache input. Therefore it isolates equivalence of the H3 optimized predicate versus the previous algorithm on reached inputs, not an independent absolute chess-law oracle or stale-cache proof. Cache-invalid no-ray branch uses r15d single_blockers reference. Full fallback also shares other unchanged legality/generation helpers. One-thread/observed net/build/positions only. Tests may fail to reach a class; class totals must be reported honestly.
Only src/board.cpp and include/forge/board.hpp changed in isolated scratch. Patch /tmp/forge-dot-job18-H3.patch.txt SHA256 d2994528c41a225dbfa488281fe83fd922e5ce10e2d63cd8f2adbadc1e6450b1,4775bytes; clean dry-run against FINAL Job14 count5 source succeeded. No build or counted run performed by this step.

## 4. Known answers and controls
K1 count9 first200W1entries/197distinct,depth9,PC20/net768,Hash16/reset each:4097080last-completed-depth nodes. All200bestmoves and ALLlast-info fields excepttime/nps agree withvalidatedJob14baseline, includinghashfull; all13oldper-rowcounts unchanged.
K3 count9 samefirst200,Hash1,oneprocess,isreadybeforeeach,noucinewgamebetween:3351324last-completed-depth nodes, rows matched priorunchangedr15d/validatedbaseline. Old13counts retained. K2 wrong9 first200resetHash16:4097080nodes, unchangednormaloutputs/old13. H30wrongreference changes only White-to-move tied generations; H3wrongreference toggles only safe-pawn-witness class. Both differ atsomeusesandfewerthanall.

| Counter | K1 uses/differ | K3 uses/differ | K2 wrong uses/differ |
|---|---:|---:|---:|
| B1 | 2564528/0 | 2041466/0 | 2564528/0 |
| B2 | 2689044/0 | 2156087/0 | 2689044/0 |
| B5 | 2607489/0 | 2326016/0 | 2607489/0 |
| B6 | 3895460/0 | 3170149/0 | 3895460/0 |
| S-B1 | 2564528/0 | 2041466/0 | 2564528/0 |
| S-B2 | 2689044/0 | 2156087/0 | 2689044/0 |
| S-B4 | 2564528/0 | 2041466/0 | 2564528/0 |
| S-B7 | 3895323/0 | 3174994/0 | 3895323/0 |
| H28 | 341487/0 | 259781/0 | 341487/0 |
| H18 | 2063485/0 | 3178604/0 | 2063485/0 |
| H27 | 1124811/0 | 934797/0 | 1124811/0 |
| H25 | 5483925/0 | 4227826/0 | 5483925/0 |
| H82 | 5760791/0 | 4542519/0 | 5760791/0 |
| H30 | 72224/0 | 2500/0 | 72224/39728 |
| H3 | 2916851/0 | 2495149/0 | 2916851/1412026 |

### Classes
H30 white/black generation partitions uses; illegal_source/promotion_source overlap, not extra uses. H3 checked/safe_pawn_witness/no_enemy_ray/other partitions uses; no_enemy_ray requires invalidkingcache tocount actualshortcutreach.
| Run | H30 White | Black | Illegal source | Promotion source | H3 checked | Safe pawn | No enemy ray | Other |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| K1 | 39728 | 32496 | 72112 | 1334 | 84827 | 1412026 | 1357622 | 62376 |
| K3_count | 1206 | 1294 | 2500 | 22 | 94161 | 1365762 | 978921 | 56305 |
| K2 | 39728 | 32496 | 72112 | 1334 | 84827 | 1412026 | 1357622 | 62376 |
| S1 | 193812 | 154055 | 347231 | 7769 | 84827 | 7514424 | 5108238 | 371069 |
| S2 | 8402 | 8254 | 16628 | 512 | 0 | 3364492 | 1273681 | 84751 |

Controldifferences exactly39728Whitegenerations of72224H30uses and1412026safe-pawnwitnesses of2916851H3uses. Firstfiveglobaldiagnosticcap is consumed byH3;H30hasnonzero aggregate/classproof but no printed sample beforecap. 0000means predicate has noselectedmove, not playednullmove.
Firstfive control samples are in alreadyverified K2raw. No position-containing transcript excerpts are reuploaded here while the laterraw-publication scope denial remains unresolved.

## 5. Prediction graded
Immutableprediction47e0ce43220b3f3a88ded9967d424bce4a47b3dc committed/readback before ANYcountedrun, includinggates. Allfourranges andzerodifference predictionsPASS. These were deliberately broadsource/workloadranges, not precise calibrated forecasts or pilots.
| Workload/counter | Predicted uses | Actual uses | Predicted/actual differ |
|---|---:|---:|---:|
| S1H30 | 1000–2000000 | 347867 | 0/0 |
| S2H30 | 100–1000000 | 16656 | 0/0 |
| S1H3 | 100000–20000000 | 13078558 | 0/0 |
| S2H3 | 30000–8000000 | 4722924 | 0/0 |

## 6. S1/S2 counter-by-counter
S1:1000entries/990distinct,depth9,16543291last-completed-depth nodes; everybestmove/canonicalfinalinfo matchesbaseline, all13oldcounts preserved. S2:same20distinctstarts/same1370legalplies,5612423actualsoftnodes total (not4569803last-depthinfosum); allmoves/old13perplyretained. All15normalcounterszerodifferences.
| Counter | S1uses/differ | S2uses/differ |
|---|---:|---:|
| B1 | 9079813/0 | 3212417/0 |
| B2 | 9638809/0 | 3468791/0 |
| B5 | 10935512/0 | 4071447/0 |
| B6 | 15430637/0 | 5227491/0 |
| S-B1 | 9079813/0 | 3212417/0 |
| S-B2 | 9638809/0 | 3468791/0 |
| S-B4 | 9079813/0 | 3212417/0 |
| S-B7 | 15531178/0 | 5255554/0 |
| H28 | 1376393/0 | 493901/0 |
| H18 | 9040060/0 | 2638740/0 |
| H27 | 5029379/0 | 1610870/0 |
| H25 | 23565361/0 | 6954922/0 |
| H82 | 25127532/0 | 8190621/0 |
| H30 | 347867/0 | 16656/0 |
| H3 | 13078558/0 | 4722924/0 |

## 7. Map again
# Job18 updated86-hunk coverage map

All original IDs/ranges retained. Only H30/H3 NONE to PARTIAL_DIRECT; NONE28 to26. InterruptedJob17H71/H12 remainNONE, not silentlycovered. H85priorPARTIAL_SESSION unchanged. Generation-level H30 projectedequivalence is not perreturnobservation.

|ID|File|kF range|Changedlines|Change|Coverage/evidence|Limit|
|---:|---|---|---:|---|---|---|
|1|src/board.cpp|2-8|1|Add assert header|NO_BEHAVIOUR: Header only; runtime assertions disabled by NDEBUG in original Release build.|Header only; runtime assertions disabled by NDEBUG in original Release build.|
|2|src/board.cpp|834-841|3|Mask king destinations attacked by enemy pawns/king before expensive safety test|NONE: Job10 B7/perft exercises move generation but no per-use independent early-mask counter; no inspected external report isolates this hunk.|Job10 B7/perft exercises move generation but no per-use independent early-mask counter; no inspected external report isolates this hunk.|
|3|src/board.cpp|852-872|15|has_legal_move fast safe-pawn witness and no-ray pin shortcut|PARTIAL_DIRECT: Job18 H3: everyhas_legal_move result compared with oldr15d body on privateBoardcopy; safe-pawn-witness-only boolflip control live; classcounts include cache-invalid no-enemy-ray branch|Shares boardrepresentation, attack/primitives and validcachedkingline inputs. Copy protects actualmutablecache but is not independentcachecorrectness proof; finiteposition/T1reach only.|
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
|30|src/search.cpp|1635-1658|21|Mark illegal tied-evasion slots Move::none instead of deferred legality mask|PARTIAL_DIRECT: Job18 H30: each tied-evasion fallback generation compares projected full tag-then-selection output against old untagged selection/deferred-legality-filter output; White-only fault control live|Projected fullsequence using shared private scalarselection and std::sort, not observation of every lateractualnext() return. Shared generators/scoring/from-to legality masks; H25 separately validates reached actual selection. No absolutechess/promotionidentity proof.|
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
|3|36|src/search.cpp:1883-1909|15|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|4|11|src/board.cpp:1516-1534|14|Contact+empty-board enemy slider-ray absence implies no first legal recapture and fullSEE result true.|EP removes blocker, origin vacates x-ray, promotionrecapture at backrank, pinned or defended king recapture.|
|5|29|src/search.cpp:1568-1583|13|Generation finishes copying/scoring before recursion can overwrite shared scratch|Nested evasion search and promotion ties|
|6|86|include/forge/search.hpp:731-745|9|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|7|37|src/search.cpp:1965-1976|7|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|8|32|src/search.cpp:1748-1760|6|Guard supersets all dead-material cases; snapshots stable because option changes stop search|Unusual recognized endings and backend reload/disable transitions|
|9|35|src/search.cpp:1867-1881|5|Null changes no material and backend state prepared before search|Null nodes with material-index valid/invalid and V3 on|
|10|52|src/search.cpp:3383-3394|5|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|11|33|src/search.cpp:1819-1829|4|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|12|42|src/search.cpp:2325-2333|4|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|13|47|src/search.cpp:2679-2686|4|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|14|2|src/board.cpp:834-841|3|Excluded pawn/king attacked squares must always fail full own-king safety even after capture.|King capture onto pawn-defended square, capture of checking pawn, nearby enemyking; illegal synthetic king adjacency outside accepted-board contract.|
|15|20|src/search.cpp:944-950|3|Preserve full pseudo-legal scored list and tie swaps, discard exactly same moves including promotions sharing from/to|Equal-score legal/illegal evasions, underpromotions, TT move amid ties|
|16|39|src/search.cpp:2121-2127|3|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|17|75|include/forge/eval.hpp:51-59|3|Full dead_material_score rejects every position containing pawn/rook/queen before changing score; caller must preserve that same condition.|Enable dead-material option, promotion/last-heavy-piece capture, mixed minor endings; stale piece bitboards or expanded recognition could break prefilter.|
|18|84|include/forge/search.hpp:533-541|3|Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16|Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100|
|19|17|src/search.cpp:21-27|2|Only overwrites already-consumed prefix; bad_count <= consumed index; preserves bad-capture order|Capture-rich nodes, many losing captures, equal scoring moves|
|20|24|src/search.cpp:1079-1085|2|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|21|38|src/search.cpp:2100-2106|2|Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact|Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present|
|22|40|src/search.cpp:2255-2261|2|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|23|41|src/search.cpp:2277-2283|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|
|24|45|src/search.cpp:2407-2413|2|No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger|Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes|
|25|46|src/search.cpp:2437-2443|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|
|26|51|src/search.cpp:3337-3343|2|Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe|TT collisions, resize/clear boundaries, stale slot interactions|


## Provenance
PC20:Threads1,Hash16,OwnBookfalse,LmrQuietBase93,LmrQuietDivisor205,LmrNoisyBase13,LmrNoisyDivisor333,LmrHistoryDivisor5643,NullMoveBase5,LmpBase8,HistoryPruneMultiplier2220,HistoryBonusQuadratic24,HistoryBonusLinear54,HistoryBonusMax2212,SingularDepth6,IirDepth2,NonPawnCorrectiontrue,CuckooReptrue,HistRework2,TtPruneV2true,CorrHistV2true,MateAlphaGuardtrue. K3explicitlyHash1persistent. W1runs ucinewgame/isreadyeach; S2resetpergame,fullmovehistoryperply,softnodes2000,stopgameoverclaim_draw=True or200plycap.
Syntheticv3hidden768 net checksum30ab43b4ba5db5f3,SHA256c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7;W1SHA2563c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521. Standalonenet/positionsremainlocal. Originalr15dbase6b98f2170a3210e71beed04bbd2553972c253ed7 plusPCr15/carbon2/E1; kFfinalstackpatchSHA3d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30. Buildsettings/hashesabove bind allnumbers.

## Facts
Claim22:12:55UTC,nativecutoff23:02:55,reportdeadline23:12:55. Allnativefinished22:18:37.040568UTC. Step0 used unchangedoriginalbinaries; countedgates/controls andfullruns completedafterfrozenbuilds, predictionbeforecountedgates. No newnormaldisagreement. Referencesreadonly anddiagnostic; old13exactcounts/trees provide regressioncheck, notuniversalequivalence.

## Suspicions
No newenginebug demonstrated. H30 shares selection/generation/scoringprimitives and projects outputs ratherthanobserving eachlateractualreturn. H3 shares existingprimitives/validcacheinput; no stale-cacheproof. Finiteevidence mustnotbeextendedtounseenfields/positions.

## What I did not do
No resumedJob17experiments, no completedH71/H12counterclaim, no speed/Elo test, no newPC/net/compiler ormultithreadtest, no standaloneposition/game dataset orbinary/net upload. No independentstdsort/legalgenerator oracle. Auxiliaryskillauditor unavailable/notrun; independentraw/sourceQA andnativegates separate.

## What I am not sure about
Unreached positions/options, clockedsearches, concurrency andsharedprimitive failures remainoutside. Counterzero onlysupports reached semanticfacets. H30firstfiveFENsamples notprintedbecauseglobalcap consumedbyH3; aggregatecontrolstilllive.

### What this check cannot see
Positions these scripts do not reach; the PC's net, compiler and build; more than one search thread; Hash sizes
other than 1 and 16.

## Publication
Partial publication:31files verified, exact inventory publication_verified.json.txt. K1/K2/K3 complete raw and onlyS1parts001–003 verified; all remaining S1/S2 raw remainlocal. raw/S1.part004.txt was safety-denied as a position dataset conflicting with original no-data constraint;404confirmed. No retry, repackaging or alternate route. Direct userexception requested but not received at reporttime. Safe-only prose/build/aggregate publication then reached13additionalfiles before a separate approvalreview error 'agent runtime is shutting down'; that attemptedwrite explicitlynotexecuted, no retryloop. Total67plannedfiles notverified, listed in publication_missing.json.txt (55rawparts plus12ancillaryitems). Rawmanifest describes complete LOCALtranscripts, not proof everypart isremote.
All native experiments and independent local QA completed, but complete public raw evidence for S1/S2 is NOT available. Full-run counts above are localverifiedresults with this explicit public-evidence gap; the requested every-number-backed-by-committedraw standard cannot be fully satisfied without authorization. No claim all artifacts are remote. Report includes safe code-coverage/prose conclusions, not the deniedposition transcripts. Existing fullpatches andStep0bundle separatelyverified. No sourcechanges/PR/datasetworkaround.

## Last command before report commit
```text
git status --short; ls -R forge-combo29/dot/job18
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job10.md
?? forge-combo29/REPORT_dot_job11.md
?? forge-combo29/REPORT_dot_job12.md
?? forge-combo29/REPORT_dot_job13.md
?? forge-combo29/REPORT_dot_job14.md
?? forge-combo29/REPORT_dot_job15.md
?? forge-combo29/REPORT_dot_job16.md
?? forge-combo29/REPORT_dot_job17.md
?? forge-combo29/REPORT_dot_job18.md
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
?? forge-combo29/dot/job17/
?? forge-combo29/dot/job18/
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
forge-combo29/dot/job18:
C_count9_build.txt
C_count9_configure.txt
C_count9_from_job14.patch.txt
C_count9_full.patch.txt
C_wrong9_build.txt
C_wrong9_configure.txt
C_wrong9_from_job14.patch.txt
C_wrong9_full.patch.txt
H30_cross_review.txt
H30_design.txt
H3_design.txt
H3_from_job14.patch.txt
K1.classes.txt
K1.progress.txt
K1.raw.txt
K1.rows.txt
K1.summary.txt
K2.classes.txt
K2.progress.txt
K2.raw.txt
K2.rows.txt
K2.summary.txt
K3_count.classes.txt
K3_count.raw.txt
K3_count.rows.txt
K3_count.summary.txt
S1.classes.txt
S1.progress.txt
S1.raw.txt
S1.rows.txt
S1.summary.txt
S2.classes.txt
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
publication_blocked.txt
publication_missing.json.txt
publication_verified.json.txt
r15d_bench_11.raw.txt
r15d_bench_13.raw.txt
r15d_go_perft_5.raw.txt
raw
raw_manifest.json.txt
step0_complete.raw.txt

forge-combo29/dot/job18/raw:
K1.part001.txt
K1.part002.txt
K1.part003.txt
K1.part004.txt
K1.part005.txt
K2.part001.txt
K2.part002.txt
K2.part003.txt
K2.part004.txt
K2.part005.txt
K3_count.part001.txt
K3_count.part002.txt
K3_count.part003.txt
K3_count.part004.txt
K3_count.part005.txt
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
S1.part021.txt
S1.part022.txt
S1.part023.txt
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
S2.part032.txt
S2.part033.txt
S2.part034.txt
S2.part035.txt
```
