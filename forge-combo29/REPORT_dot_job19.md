# Dot Job19

## 1. Step0 PASS
Unchanged r15d SHA256bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6 and kF340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea, nooptions/net,freshprocesspercommand: bothbench11=312866nodes,bench13=862329nodes,go perft5=4865609nodes. Six complete outputs withoutposition-inputcommands bundled in step0_complete.raw.txt, verifiedbe4cf4cde2ca6641b12084900c2f6794a00c01f3.

## 2. BranchN, newest validated base
Job18reported no normalcounter/search disagreement and allold15values/strictcanonicalfields preserved. Its raw-publication block is an evidence-sharing gap, not a measured engine disagreement. Job19explicitly returnsH71/H12, unfinishedinJob17. Their drafts were reopened/reimplemented on FINALVALIDATEDJob18count9, not copied as an unbuiltcount8tree. Old15counters retained.
IMPORTANT: native/localQA results below are complete, but position-containingrawpublication remains blocked by originalno-data scope denial pendingdirectFinnexception. No newjob/repackaging retry. Public raw evidence standard is notfullymet; gap is explicit below.

## 3. Patches/builds
C_count10_full.patch.txt SHA256f388d6803cf87f6414d3d17e6e3ff8dd56e7d926c78fde4c89538e4ab4f2e614; C_wrong10_full.patch.txt SHAbff228d6dd55fe94c06c4b72302a1006e3783e8d50cdc9279a4013d5f2f3d56e. Fullpatches againstoriginalkF; incrementalfromJob18alsoprovided. Verifiedfullpatchcommitsd8a179a5b8363f27597cb8fc8e23ae4186b66bc0 and06ab07eab7b3f5dc0316eb93560798bc52a4c09b.
Count10binary SHAee0ac8cf22acbf9783cb7de055821e7bdd4ebb59de63959136b3d4ff880f3631; wrong10 SHA1ab7580cd342109f1f459a3c0a1c21a1ff2165dbbcdaabb9468cc588846dbe76. Both clean-first frozen-source builds completed22:35:48UTC, noheadereditsduringcompile. GCC14.2.0,CMake4.4.5,libstdc++.so.6.0.33,glibc2.41,C++20Release,O3,NDEBUG,strictFP,marchx86-64-v4; flags/logs inbuildmanifest. Oldfaultmacrosdisabled; WRONG10onlycontrol. No repositoryengine sourcechange.

### H71 scope
H71 design frozen2026-11-18T22:35:04Z, before counted runs.
Reopened original r15d include/forge/b4.hpp37-57 and FINAL Job18 count9 b4.hpp. Old r15d computes pawn,minor,rook attack unions unconditionally. kF skips higher-piece masks when no friendly piece of the consuming type exists. Counter runs once per lesser_threats call, independently recomputing old unconditional masks in local variables using the same board/attack primitives. It compares pawn/knight/bishop masks always, king/NoPiece zero slots always, rook mask only when friendly rook exists, queen mask only when friendly queen exists. Absent heavy-piece fields are intentionally omitted and not claimed bitwise equal; semantic comparison is restricted to fields consumed for existing movers. This does not prove arbitrary future callers never read an absent-type field or absolute attack-table correctness.
Classes partition all calls:0 neither friendly rook nor queen;1 rook-only;2 queen-only;3 both. Wrong10 flips bit0 of the local rook reference mask ONLY in class1. That bit change always changes the compared full rook bitboard in that class, even if no actual move happens to touch square0. No real returned mask, board, cache or history is changed. Local queen reference was computed before fault but is not compared in rook-only class. Native control must show class1 is some-but-not-all calls; source inspection is not a replacement for that gate.
Reference uses read-only pieces/occupied, pawn/knight/bishop/rook attack helpers and local pop_lsb variables. No make/unmake, search hook, recursive instrumented lesser_threats call or old counter is invoked. One use is a map construction, not a move or node. Diagnostics carry current Board and no selected candidate move (0000). Counts do not establish every mask bit influences observed move ordering.
Draft17 was unbuilt and not accepted as evidence; this isolated b4-only patch was freshly applied to FINAL validated Job18 source and reopened against original r15d. Integrator owns common record_h71(bool,int,const Board&), clean build and fullpatch generation. No counted native run or source compile performed in this step.
Patch /tmp/forge-dot-job19-H71.patch.txt SHA2561e3c475b0e4d88fc4f415fe1e4e3ddb32881556e724d72cd0fbf92592817e9a0.

### H12 scope
H12 one use per public Board::see_ge(move,threshold) invocation. Actual newestvalidatedkF body executes once inside lambda, with diagnostic path tags at existing earlyouts/loop. A separate diagnostic member clones originalr15d see_ge body exactly, except membername; called on same constBoard afteractual. It uses local occupancy/attack bitboards/gains and unchanged read-only helpers, not make/unmake, cache-refresh or existing countedhooks. promotion_recapture_exchange inspected: local gain/bitboards only. Actualreturn remainsunchanged; references do not update search state/counters except H12 diagnostics. No suppression mechanism needed. Old15 per-row counter gates required.
Classes moving_knight/other_mover partition calls by original piece at move.from. Wrong10 flips only reference bool for movingKnight class, independent of actual answer; othermovers untouched. Every suchcall mustdiffer ifnormalreferencecorrect, but classmustbe reachedsome/notall atnativegate.
Second partition prefix_return/ray_empty/actual_empty/exchange_loop records actualcode exit/reach. prefix_return includes castle, promotion-recapture specialpath and initialmaterial-threshold shortcuts before taggedH11/H12raytests (and any active earlierprefixreturn). ray_empty is geometriccontact+rayabsence; actual_empty is occupancy-aware slidercontactabsence; exchange_loop marks generalexchangephase even if zero furtheriterations. These are path classes, not move counts or iteration totals. Exactcompiled macro branches retained.
Reference compares observable bool for entire SEE, not separately every intermediate attacker bitboard. It therefore supplies output-equivalence evidence forH12, with actual_empty/loop counts showing reach, but does not independently verify all chess-law rules. Shared Boardrepresentation, valueconstants, attackhelpers, king/occupancy primitives and rarepromotion helper limitindependence. OtherSEE-related maprows not automatically upgraded. Diagnostics globalfirst5cap may be consumedbyothernewcounter; aggregate/classcontrol proof remainsdistinct from printedexamples.
PriorJob17draft prepared thisreference but neverfinishedbuild/test. Job19 reapplies only inspected reference/wrapper/plumbing on FINALvalidatedJob18count9 base. Bothsources frozen beforeclean-first builds; no headereditsduringcompile. No countedrun performedbythis preparation.

Readonly H12 cross-review observed2026-11-18T22:36 UTC. No source changes or counted runs.
Reopened finalized Job19 counting src/board.cpp1601-1923 and original r15d see_ge. Diagnostic see_ge_r15d_reference body is byte-identical to original body:6951bytes,SHA2565521b10303d30bfca8e0e8e45e2869279aebe0e34d267a431aee8b6943b307f1. Actual optimized see_ge body executes once inside a bool-returning lambda; reference runs afterward, returns only diagnostic value. Both use const Board data and local occupancy/attacker/gain arrays. Inspected promotion_recapture_exchange and attackers helpers: no Board make/unmake, mutable king-line refresh, recursion into public see_ge or existing counted hook; therefore reference does not add old counters or mutate actual state. Same shared helpers/tables do mean this is algorithm-equivalence evidence, not an independent absolute SEE oracle.
H12 counts every public see_ge call, including prefix returns unrelated to H12's shortcut. Path partition:prefix_return (castle,promotion-recature special,immediate material threshold outcomes), ray_empty (no enemy contact/geometric slider ray), actual_empty (no actual first attacker after occupancy rays), exchange_loop (enters original exchange recurrence). In current FORGE_SDK_SEE_HOIST=1 build these stages identify actual branch reach; inactive HOIST0 extra pawn earlyfalse would remain defaultpath0 and is not separately covered. The movingKnight/otherMover partition is separate and overlaps these path bins.
Wrong10 flips only local reference boolean when original moving piece is Knight; no actual return, state or class changes. This applies across paths for that class and should produce some-but-not-all differences only if both mover classes reached; native control must prove it. H12 covers the complete old/new SEE result, including H11 earlyout as an observed side effect, but named row coverage and finite-path limits must be explicit. No change to unrelated map rows is automatically implied by this review.
H71 full returned masks are compared only for present-friendly heavy-piece types; intentionally omitted absent fields excluded. Class1 local rook-mask fault is isolated. Commoncounter hooks count read-only diagnostics; old15 per-row gate and no-search-tree-change checks remain required, not replaced by this source review.

## 4. Known answers and live controls
K1first200W1entries/197distinct,depth9,PC20/net768,Hash16/reset:4097080last-completed-depth nodes. K3first200,Hash1persistentoneprocess/nointer-searchucinewgame:3351324last-completed-depth nodes. K2wrong10first200reset:4097080nodes. Everybestmove and everylast-infofield exceptONLYtime/nps agreeswithvalidatedbaseline, includinghashfull/PV; old15per-rowcountsunchanged.
H71wrongreference toggleslocalRookmaskbitonlyrook-present/queen-absentclass;196600/793153differences. H12wrongreference flipsboolonlymovingKnight;217222/3682465differences. Bothstrictlysomeandfewerthanall; actualsearchreturns/stateunchanged. Counter/classproofs complete locally. Globalfirstfive diagnostics consumedbyH12; rawsamples keptlocal ratherthanreuploadedagainstdenial.
| Counter | K1uses/differ | K3uses/differ | K2wronguses/differ |
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
| H30 | 72224/0 | 2500/0 | 72224/0 |
| H3 | 2916851/0 | 2495149/0 | 2916851/0 |
| H71 | 793153/0 | 557278/0 | 793153/196600 |
| H12 | 3682465/0 | 2935979/0 | 3682465/217222 |

### H71 material classes (partition uses)
| Run | Neither | Rook only | Queen only | Both |
|---|---:|---:|---:|---:|
| K1 | 303900 | 196600 | 199855 | 92798 |
| K3_count | 163711 | 180374 | 119244 | 93949 |
| K2 | 303900 | 196600 | 199855 | 92798 |
| S1 | 1124232 | 871349 | 650838 | 596031 |
| S2 | 384400 | 279024 | 172071 | 128407 |

### H12 classes
MovingKnight/other partitions allcalls. Prefix/ray_empty/actual_empty/exchange_loop independentlypartition samecalls; do notsumthetwo partitions together. Paths are actualcompiled-code reach, notiterationcounts.
| Run | Knight | Other mover | Prefix | Ray empty | Actual empty | Exchange loop |
|---|---:|---:|---:|---:|---:|---:|
| K1 | 217222 | 3465243 | 928645 | 1478385 | 67526 | 1207909 |
| K3_count | 225651 | 2710328 | 871997 | 989641 | 68340 | 1006001 |
| K2 | 217222 | 3465243 | 928645 | 1478385 | 67526 | 1207909 |
| S1 | 1219735 | 14476868 | 4503265 | 5415037 | 402408 | 5375893 |
| S2 | 269306 | 4402905 | 1431846 | 1776857 | 103733 | 1359775 |

## 5. Prediction graded: allPASS
Immutable2639f6c98962c03ad956ea97d1e3d9b1ba52a75c committed/readback beforeANYcountedrun, includinggates. NoJob17newcountermeasurements existed. Broadsource/workloadforecasts, notprecisecalibration.
| Run/counter | Predicteduses | Actualuses | Predicted/actualdiffer |
|---|---:|---:|---:|
| S1H71 | 500000–5000000 | 3242450 | 0/0 |
| S2H71 | 100000–2000000 | 963902 | 0/0 |
| S1H12 | 2000000–40000000 | 15696603 | 0/0 |
| S2H12 | 500000–15000000 | 4672211 | 0/0 |

## 6. S1/S2 results
S1:1000entries/990distinct,depth9,16543291last-depthnodes; allcanonicaloutputs/old15counts unchanged. S2:same20distinctstarts,1370legalplies/searches,5612423actualsoftnodes total (last-depthsum4569803 is a differentmetric); fullmovehistory/old15perply/canonicalfinalfields unchanged. All17normalcounterszerodifferences. These are localverifiedexperimentalresults; rawtranscripts notpublishedwhileauthorizationblocked.
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
| H71 | 3242450/0 | 963902/0 |
| H12 | 15696603/0 | 4672211/0 |

## 7. Map again
# Job19 updated 86-hunk coverage map

Only H71/H12 coverage categories changed from NONE to PARTIAL_DIRECT; NONE 26 to 24. All original IDs/ranges and other coverage claims retained from Job18. H11 category is not upgraded; its evidence/limit text now acknowledges related whole-SEE and ray_empty coverage. No raw positions or position rows appear here.

|ID|File|kF range|Changed lines|Change|Coverage/evidence|Limit|
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
|11|src/board.cpp|1516-1534|14|SEE contact/ray-empty early success before full exchange loop|NONE: Job19 H12 whole-SEE reference also compares H11 ray_empty-path returns; ray_empty class records actual branch reach (S1 5415037). Related output coverage now exists. Category conservatively retained pending H11-specific assessment/control, not absence of a SEE reference.|Related whole-SEE output checks share attack and geometry primitives. No H11-isolated faulty-reference control or independent ray/attack oracle; finite input-class reach not separately established. NONE here is the retained targeted-map category, not a claim this path went unchecked.|
|12|src/board.cpp|1536-1564|22|SEE actual-ray-empty early success and factored attacker gather; off-branch pawn refutation|PARTIAL_DIRECT: Job19 H12: every see_ge Boolean result compared with exact old r15d reference body; Knight-only reference-Boolean flip control live. Mover and path partitions measured.|Whole-SEE output equivalence, not every intermediate attacker mask or exchange step. Shared representation, values, attack helpers and promotion-recapture helper; prefix returns include unrelated paths. H11 is not automatically upgraded by this evidence; finite T1 reach only.|
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
|71|include/forge/b4.hpp|37-62|24|Skip computing lesser-attack masks for absent friendly rooks/queens|PARTIAL_DIRECT: Job19 H71: one diagnostic per lesser_threats construction; old unconditional r15d masks compared with optimized masks; rook-only reference-minor XOR control live.|Pawn/minor/zero-king masks compared always; rook/queen masks only if own piece of that type exists. Omitted absent-heavy masks intentionally not compared. Shared board/attack primitives, finite T1 reach; not independent attack legality proof.|
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


## Provenance
PC20:Threads1,Hash16,OwnBookfalse,LmrQuietBase93,LmrQuietDivisor205,LmrNoisyBase13,LmrNoisyDivisor333,LmrHistoryDivisor5643,NullMoveBase5,LmpBase8,HistoryPruneMultiplier2220,HistoryBonusQuadratic24,HistoryBonusLinear54,HistoryBonusMax2212,SingularDepth6,IirDepth2,NonPawnCorrectiontrue,CuckooReptrue,HistRework2,TtPruneV2true,CorrHistV2true,MateAlphaGuardtrue. K3explicitHash1persistent. W1resetucinewgame/isreadyeach;S2resetpergame/fullhistoryperply/go softnodes2000,game_over(claim_draw=True)or200plycap.
Syntheticv3hidden768 checksum30ab43b4ba5db5f3,netSHA256c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7;W1SHA2563c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521. Standalonenet/positionsremainlocal. Originalr15dbase6b98f2170a3210e71beed04bbd2553972c253ed7 plusPCr15/carbon2/E1;kFfinalstackpatchSHA3d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30.

## Facts
Claim22:34:02UTC,nativecutoff23:24:02,reportdeadline23:34:02. Allnativefinished22:37:57.040294UTC. Step0unchangedbinaries beforecount10freeze; countedgates/controls/fullruns afterfreeze andprediction. No observednormaldisagreement. Source/rawQA complete locally; safeprose/patch/aggregate publication only.

## Suspicions
No enginebug demonstrated. H71intentionalabsentheavy maskdifferences are notcomparedbecause currentcallersreadpresentpiecetypes; futurecaller-invariant changes couldmatter. H12fullbooleanreference sharesprimitives and doesnot proveallchessrules/intermediatebitboards. Broadpredictionhits are notstrongcalibrationevidence.

## What I did not do
No position-containingrawretry, no alternatepackage to evade denial, no standalonegame/positiondataset/net/binaryupload. No PC/net/compiler replication, no multithread/clockedperformance/Elo claim. No repairedengine required. Globaldiagnosticcap notexpandedafterresults. Auxiliaryskillauditor unavailable/notrun; nativegates andindependentlocalQA separate.

## What I am not sure about
Unseenpositions/options, stale/sharedprimitivefaults, absenttypefuturecallers andotherplatformsremainoutside. Zeroobserveddifference isfiniteevidence, notuniversalproof. Externalreviewer cannotfullyrecompute countswithoutblockedraw; reportdoesnotclaimotherwise.

### What this check cannot see
Positions these scripts do not reach; the PC's net, compiler and build; more than one search thread; Hash sizes
other than 1 and 16.

## Publication
All23safe-onlyfiles fullyreadbackverified22:43:25UTC,95278bytes, latestQA/mapincluded; ledger publication_verified.json.txt records exactfiles. Fullsourcepatches, prediction andStep0bundle separatelyverified. No missing intendedSAFEartifacts ornewdenials. Complete countedrawpublication was deliberately notattempted, not silentlycompleted. Position-containing raw K1/K2/K3/S1/S2, localrowtables/pergame summaries andsampleFENs were NOTsubmitted. PriorJob18rawsafetydenial remainsinforcependingdirectFinnexception, notoverriddenbyOpusjobtext. Allcomplete localraw retained. Safeaggregateprose/patches/buildlogs are distinguishable from fullpublicrawproof. Requested every-number-backed-by-committedraw cannot befullymet undercurrentauthorization.

## Last command before report commit
```text
git status --short; ls -R forge-combo29/dot/job19
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
?? forge-combo29/REPORT_dot_job19.md
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
?? forge-combo29/dot/job19/
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
forge-combo29/dot/job19:
C_count10_build.txt
C_count10_configure.txt
C_count10_from_job18.patch.txt
C_count10_full.patch.txt
C_wrong10_build.txt
C_wrong10_configure.txt
C_wrong10_from_job18.patch.txt
C_wrong10_full.patch.txt
H12_cross_review.txt
H12_design.txt
H71_design.txt
H71_from_job18.patch.txt
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
publication_verified.json.txt
r15d_bench_11.raw.txt
r15d_bench_13.raw.txt
r15d_go_perft_5.raw.txt
step0_complete.raw.txt
```
