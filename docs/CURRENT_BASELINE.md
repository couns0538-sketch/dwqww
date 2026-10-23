# Current baseline

Active follow-on job: `forge/independent-teacher-20261023`, parent27070fe.
[Current compact manifest](../validation/independent-teacher-20261023/manifest.json)
and [sole job report](../validation/independent-teacher-20261023/FINAL_REPORT.md)
are authoritative for this six-hour independent-teacher mission. Old data is not
retrained. The earlier NNUE pipeline below is accepted as complete; its shipped
net remains default and its isolated trial is not promoted. No strength matches.

Active mission: NNUE pipeline verification on `forge/nnue-pipeline-20261023`,
off `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` (Forge6.4.24).
Production search, evaluator and shipped default weights remain unchanged.
The clean frozen **net-only trial** is
`6e9622fd5be18e0155fc3ed5fcf6c4586705cca6`, branch
`forge/nnue-net-20261023-a52efa5f7864`; its sole delta from1ab is
`src/nnue_weights.inc`, SHA256
`a52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7`.
This is not a promoted replacement or an Elo-accepted engine.

Both full-data20-epoch runs actually closed0. One million training positions
comprise985105 legacy and14895 fresh positions; original validation is4149/56
games. The preregistered40-epoch selection froze zero-run epoch3 before public
publication and the once-only independent audit. All checkpoints, data recovery,
failed gates, exact commands and raw results are preserved under
[NNUE evidence](../validation/nnue-pipeline-20261023/).

Independent audit8881 positions/109 represented games: HCE MSE
0.006741170688447828; shipped hybrid0.005970920199524993; candidate hybrid
0.005991080028522929. Candidate is11.127% below HCE (95% whole-game interval
5.858..16.472%) but0.338% worse than shipped; improvement interval
-5.783..+4.286% includes zero. **No improvement over shipped is demonstrated.**
Retain shipped default. No reselection or retraining using this audit.
No games or Elo claims; user QA owns the separate1000-game strength gate.

Chosen-net native and Windows parity each pass2048/2048 exact integer scores,
zero feature mismatches. Original C++ loader roundtrip preserves all394756 binary
bytes and98689 quantized parameters. Windows Zen5 trial passes all14 original
checks under Wine; first/repeated new-net bench378596. The delivered EXE hash is
`2adc0429d238208ae9ae1a7788d6c570d9eb649b58c737bd8358d6004703518e`.
[Windows trial ZIP](../releases/forge-6.4.24-nnue-a52efa5f7864-trial-windows-zen5.zip),
13008348 bytes, SHA256
`276598f6ea45eae76cea7016052e00c37e54ccf5c709c48448c1e3aadbf5c3ca`.
Wine qualification is not physical Windows/Ryzen testing or measured speed.

Original Linux Release and ASan/UBSan each passed13/14, failing only an
evaluation-dependent depth8 null-pruning coverage assertion. Raw failures remain
preserved; no sanitizer diagnostic occurred. Test-only repair `f4a1ed6` uses a
controlled real search window and passes against old/new actual cores; disabling
null pruning in a private negative-control object makes the assertion fail.
Production search is unchanged. Fresh corrected-harness qualification passed
14/14 Release plus14/14 ASan/UBSan, owner10660 actual exit0. Its source explicitly
combines clean6e engine with only f4's exact test file. Release engine/core remain
byte-identical to the original failed-harness production artifacts. First genuine
new-net Linux bench348974 matches the repeat; this is not a speed measurement.
Default shipped build after f4 passes14/14 and unchanged bench292545; engine/core
are bit-identical to the immutable baseline. See
[qualification status](../validation/nnue-pipeline-20261023/QUALIFICATION_STATUS.md).
Previous paused work remains preserved remotely at5b9b132 on its original branch.

Accepted integration `forge/6.4-hourly-20261019` is now
`5101c2529d386b7c3a04ba9156a69ee34df6bb43` (remote fast-forward verified
2026-10-20 20:44:42UTC). It adds the existing one-line OwnBook repair af19413 and
its unchanged native regression to356e863, preserving the TT and timed-only clock
repairs. Acceptance is for the finite book contract; no accepted equal-time Elo gain.
[Integration receipt](../validation/accepted-ownbook-integration-20261020/INTEGRATION.json).

Newest isolated code is **Forge 6.4.24**, frozen source
`7db08eac6ead99d641834c56ccec06a06600586a`, branch
`forge/see-proof-reuse-20261021`. It reuses GoodCaptures SEE>=0 at two search
consumers, with no new state and a nonpositive-threshold guard. Existing28 mirrored
exchange oracles add504 threshold-bound assertions. Exactly4 source paths changed,
73 unchanged/77 total; source review passed. Parent23 observer showed exactsearch
parity and13387 repeated queries/344945 (3.88% opportunity), plus1877582actualSEE
checks; this is not a speed measurement. The first full native24 chain passed
42 CTests (14 Release/14 ASan+UBSan/14 default unsuppressed TSan), eight active UCI
checks and 56 exact parent cold/warm searches. SEE504/TT12/PV56 pass per profile;
independent2593checks and root644originals/17parentinputs/77Git/262evidence checks
pass. First Linux signature292545 and the NNUE object match parent23.
[Native root proof](../validation/see-proof-reuse-candidate-20261021/root-verification/NATIVE.json).
Windows24 first strict Zen5 build,13Wine checks and1870artifact checks passed;
first Windows signature334752 matches parent23. ZIP17077385B SHA256
`0db112fab29653eb43ac74924fb08a4a956bbf5085555f1a166a64d83fc392db`.
Root Windows byte verification passed10428checks (287evidence/323outside/597parent/
77Git/271raw); actual public GitHub download matches the ZIP hash.
[Windows root proof](../validation/see-proof-reuse-candidate-20261021/root-verification/WINDOWS.json),
[Windows24 download](https://raw.githubusercontent.com/couns0538-sketch/dwqww/7def48b9eabdc60ef52718052d9e79fa2ab8bc23/releases/forge-6.4.24-candidate-windows-zen5.zip). This is Wine testing,
not physical Ryzen execution. The first actual one-process/five-command24 capture
passed, reusing genuine23 originals without rerunning23; all362inputs unchanged.
Calibrated performance and equal-time Elo remain unmeasured for24.
[Experiment](../validation/see-proof-reuse-candidate-20261021/EXPERIMENT.md).
Keep24 isolated; finite correctness does not accept its unaccepted search lineage.

Parent isolated policy trial **Forge 6.4.23** is source
`1d3ed25bea2c8b781f7ee5a178af0f66061b3984`, branch
`forge/tt-refresh-20261021`. It refreshes occupied old TT generations under the
existing synchronization. Four new real-table regression groups preserve all eight
older groups; the expected old-policy contrast against unchanged22 passed.
All77 source inputs are pinned, with73 unchanged and exactly four delta paths.
First native validation passed42CTest (14Release/14ASan/14defaultTSan),12TTgroups
and56PVassertions each, plus8activeUCIchecks. Independent1185checks/0fail and root
644originals/17parentsingles/77Git/138evidence rehash passed. Single firstbench
captured292545nodes; the compiled NNUE object is bit-identical22. Windows23 passed13Winechecks/TT12/PV56 and1827artifactchecks; root rehashed259raw
originals,604parentfiles,74sourcefiles and275finalrecords. ZIP
`releases/forge-6.4.23-candidate-windows-zen5.zip` SHA
`c3ae058154624a2c91ff32e89d78cdb222cb02d166664cddcbd7f2d4bfa17b50`.
All23strength evidence remains pending. This changes replacement, shallow admission and
hashfull and is not a demonstrated correctness fix, speedup or Elo gain.
[Trial and next gate](../validation/tt-refresh-20261021/EXPERIMENT.md).
Its complete qualification archive now passed one actual fresh scratch recovery:
2222originals/2241payloads/219recordeddirs, combined203969966B SHA
`2855b301c0adf184ec1ee92ff53aa1dcef4c0886303c913c8a3ff7686392cdbd`,
four Git-safe parts. Independent14809archive/4704recovery checks PASS; rootrehash
all2222originals/2241restoredpayloads and77actualGit-source blobs PASS. This archive
excludes active match/launch/latestdocs metadata and contains qualification only.
[Recovery instructions](../validation/tt-refresh-20261021/archive-complete/ARCHIVE-COMPLETION.md),
[root verification](../validation/tt-refresh-20261021/root-verification/ARCHIVE.json).


The separate23-versus22 strength attempt is now actually launched. Fixedpayload
`3e938ffbe71a97f181d2cdffa0226247bba9939c` passed finalindependentreview,
rootfresh504byte-mode/317proof/154Git-source checks and five HTTP200 public
readbacks. Soletrigger `forge/hosted-tt-refresh-strength-20261021-031253` pushed
03:12:53UTC. Actual [run39537333958](https://github.com/couns0538-sketch/dwqww/actions/runs/39537333958)
source linkage verified03:13:23UTC. Hostedbuildstep reported success03:15:26;
combinedreadiness/play observedrunning03:17:02UTC. Games/Elo UNKNOWN; original
hosted14+14suite proofs and match results still require audit.
Four separate timedA/A pairs precede serial512pair logistic0/+10SPRT at1+0.01,
T1Hash32/OwnBookfalse/seed20261101. No retry/resume/retrigger/pooling. Preserve
[launch](../validation/hosted-tt-refresh-strength-20261021/publication-attempt1/LAUNCH.json)
and audit resultbranch `results/tt-refresh-strength-39537333958-1` on completion.


Parent Windows-qualified isolated candidate **Forge 6.4.22**, source
`ff2e269c6058be84456e3b98344826d17b0056eb`, is on
`forge/singular-pv-metadata-20261021`; published clearance checkpoint
`1bccee28457d8e587be5b768437f199e180ae3c6`.
The two-line search change saves the caller's `tt_pv` before same-frame singular
verification and restores it before the abort check. It preserves the accepted
network, all evaluation changes and all 73 unchanged parent source inputs.
The actual parent21 diagnostic reproduces 25 flag losses in 716 natural singular
calls. The isolated repaired diagnostic passes four probe cases and 618 natural
singular calls without flag loss. Its 292545-node benchmark changes search work;
this is neither an NPS measurement nor Elo evidence. The diagnostic-free permanent
regression has 56 assertions and reproduces exactly two failures on the original
parent21 core, including aborted verification. All original RED/GREEN logs,
source hashes and expected parent failures remain preserved.
[Investigation](../validation/pv-metadata-20261021/RED-RESULT.md).

The first full frozen22 native chain passed: Release14, ASan/UBSan14,
default unsuppressed TSan14 and eight active UCI concurrency checks. The permanent
PV regression passes all56assertions in each profile, including aborted verification.
One canonical benchmark produced292545nodes. Independent audit1161/1161PASS;
root independently rehashed all644source/build originals,17consumed parent21
originals,77actualGit source inputs and123closed evidence files. The compiled NNUE
object remains bit-identical21. All profile attempts were1; no diagnostic or live
owned process remained. No exact parentsearch parity was required because this fix
intentionally changes search. Source gate SHA256
`4510f8908b628429c0e88115d7c9f3ed9ae7d9981b53ac4ff7cd6729ea6dd413`.
[Root native proof](../validation/pv-metadata-20261021/root-verification/NATIVE.json)
SHA256 `73be33c8ae94838a582ae8705e903c8d994619fbc05f798bfc1952efed7e5b62`.
Windows22 first strictLLVM-MinGW Zen5Release j1build11PEs, thirteen Winechecks,
PV56/0 and independent1779artifactchecks PASS. Root rehashed266raw originals,
74frozen sources,11builtPEs,543unchangedparentfiles and23release members/22checksums;
all282closed final records also rehashed. Actual first Windows signature334752 is
frozen; it was unknown before capture and implies no speed/Elo result.
[RootWindowsproof](../validation/pv-metadata-20261021/root-verification/WINDOWS.json)
SHA8c266b37; [Windows22 Zen5ZIP](../releases/forge-6.4.22-candidate-windows-zen5.zip),
16965395bytes, SHA256
`328706574973ca49ef185cc1fbfdf321b6dfac78c52a22db0e087553a1ca1205`.
This is Winequalification, not nativeRyzen execution. Two auxiliaryread-only
checkerfailures are retained: GNU-only archive-name parsing, then inappropriate
wholeCOFFobjectidentity. Root demonstrated allsixnonsearchobjects differonlyin
standardCOFF timestampbytes4..7; wholeWindowsNNUEobjectidentity is not claimed.
The initial rootproof's descriptiveWINDOWS21literal was corrected with oldproof,
writer and outputs retained; no engine/build/runtime was repeated.

The single22-versus21 equal-time test is complete and independently audited.
Original result `fd20551497f670aa11133ce4727ee0a1c5a1ba56`, run39528641493:
1024 normal games/512 pairs, W221/D573/L230, penta[27,120,220,125,20].
Native finalLLR-1.62 agrees with independent/root-1.617959894461137, inside
±log19. Naturalcap is INCONCLUSIVE: neitherH0norH1 and no accepted gain.
Native descriptiveElo-3.05±13.84 includeszero. Separate timedA/A4pairs/8normal
operationalgames passed and is not pooled. All1032games/137807plies legal;
all1012frozeninputs/449proofs/537buildpaths/525sourceGitblobs/475payloadGitblobs
verified; faultscan clean. Exact originalZIP65131331B SHA
`98bab142a8492f1f176d3f474f6be17b18346eb565baff6f8516183d64b1394a`.
The ZIP serializer loses executable modes (0600): original live checks and normal
processes are preserved; the data-only archive adapter does not invent original
mode receipts. [Independent audit](../validation/hosted-pv-metadata-strength-20261021/final-audit/REPORT.md),
[root byte/source/LLR verification](../validation/hosted-pv-metadata-strength-20261021/root-result-review/ROOT.json).
No replay, retry, resume or pooling. Retain22 as a finite-qualified correctness
repair; this match does not prove a positive Elo gain for it or descendants.

Previous finite-qualified **Forge6.4.21**, source
`2e151d019bc58dff2ab4e76e99ef99516af8d222`, replaces scalar king-to-own-pawn
distance scans with three exact radius queries. First native39 CTests,
8active TSan checks,56exact parent20 cold/warm searches and2421independent
checks pass. Root rehashed604whole source/build originals and76Git inputs.
Windows12Wine checks and1615independent artifact checks pass; no native Ryzen test.
[Windows21 Zen5candidate](../releases/forge-6.4.21-candidate-windows-zen5.zip),
SHA256 `e2af16d497f5c1560d413d601c3af50e364c3dfa30e3a17d49936812ac712227`,
was actually downloaded from public GitHub and hash-verified.
The single frozen performance run
[39522912590](https://github.com/couns0538-sketch/dwqww/actions/runs/39522912590),
payload `1f492e72158df9314b86bdea7c7ed4aa56fa32e0`, started00:42:14UTC.
Hosted baseline12/candidate13 build-tests and the single experiment completed.
Independent188process/940row/15AA/31AB audit PASS: CPUthroughput+1.7267%
(95%CI+1.4192..+2.0236%), wall+1.7212%(+1.4078..+2.0223%). Rootverified all232
consumed inputs and240actualGitblobs; NNUEobjects identical. Original result
`e0ca5ba962c9972761d045db0cc68c285d7efe8d`, 4380093-byte ZIP/1273payloads retained.
This is hostedLinux whole-process throughput, not Elo or nativeRyzen performance.
[Independent21audit](../validation/hosted-nearest-pawn-performance-20261021/final-audit/REPORT.md).
Do not retrigger, rescue or combine this with separate19/20percentageclaims.
[Monitor](../validation/hosted-nearest-pawn-performance-20261021/live-monitor/LATEST-OBSERVATION.json).

Existing repository-local skills are reused and improved when helpful. The cloud
skills catalog is currently empty; skill-creator/global installation is unavailable.
No optional plugin or GrokChess work blocks native Forge development.

Latest correctness-qualified and measured-workload candidate **Forge6.4.20**, source
`fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e`, branch
`forge/pawn-span-fill-20261020`, replaces a per-enemy-pawn outpost-span traversal
with an unsigned8/16/32 directional fill of the existing attack mask. Prototype
version19 passed12Release CTests,37320mask checks and95public cached/uncached/full
trace positions (61465integers identical). Original first fixture and one relocated
link-dependency-path failure are preserved; final label-only fixture passes.
Frozen20 differs from final prototype only in CMake/UCI version strings.
**Frozen20 first Release12/12, ASan/UBSan12/12 and defaultTSan12/12 PASS,**
including37320pawn+347runtime checks in each profile,8activeUCI and56cold/warm
parent19search comparisons. Bench321912; compiled NNUE object byte-identical19.
Independent2363check audit passes; root rehashed242evidence files,564whole-tree
originals,9consumed parent originals and75actualGit source blobs. Windows72source
export/five-filedelta/483parentpreservation pass. First Windows9PEbuild,
11Wine checks and1538independent artifact checks PASS; rootbyteverified225raw
originals,72sourcefiles,483parentfiles,9builtPE and21distributionmembers.
[Windows20 Zen5 ZIP](../releases/forge-6.4.20-candidate-windows-zen5.zip), SHA256
`92cf639dad35d5f44d6ef492eab1a927606aaaf609eec447a41f05775420e63c`.
This is Wine validation, not native Ryzen execution. Two actual19/20five-command
producer captures pass and178inputs remain unchanged. Outer toolreturnunknown is
retained, normalchildresultsexplicit; no repeats. **Verified20vs19 hosted throughput gain:**
CPU+1.0393% (95%wholeblockCI+0.5660..+1.5047%); wall+1.0375%
(+0.5611..+1.5074%). All188processes/940canonicalrows,15AA/31AB and finalintegrity
pass. Rootchecked178frozeninputs/211actualGitblobs; bothNNUEobjectsidentical.
Originalresultf563ef0/run39516786979, frozenpayload5651d28. This is thishostedLinux
wholeprocessworkload only; noElo/nativeRyzen or cumulative19+20claim.
[Independent20performanceaudit](../validation/hosted-pawn-span-performance-20261020/final-audit/REPORT.md).
Full20archive1889originals/1937payloads is verified, with ONE actualscratch
restoration and6089independentrecoverychecks PASS (9912archivechecks).
[Archiveproof](../validation/pawn-span-fill-20261020/root-verification/ARCHIVE.json).
Bothparts andcombined113855291bytes were actually streamed from publicGitHub
at7aed6c9 and verified; all4GETs200/67transportchecksPASS.
[Publicreadback](../validation/pawn-span-fill-20261020/root-verification/ARCHIVE-PUBLICATION.json).
[Root Windows proof](../validation/pawn-span-fill-20261020/root-verification/WINDOWS.json).
[Source freeze](../validation/pawn-span-fill-native-20261020/ROOT-FROZEN-SOURCE-GATES.json).
[Public trace evidence](../validation/pawn-span-fill-20261020/independent-review/PUBLIC-DIFFERENTIAL.md).
Accepted5101unchanged. Nearest-pawn21source is now frozen and independently published as described above.
The original prototypeversion20records remain unchanged and honestly labeled.
[Prototype21](../validation/nearest-pawn-distance-20261020/BASELINE.json).
Earlier qualified19 result below remains separate.

New isolated performance candidate **Forge6.4.19** is frozen at
`61f598056572dfade6994af8ad2e38817cd28aa3`, branch
`forge/lazy-runtime-psqt-20261020`, remotely verified. It reuses classical PSQT
and unclamped phase alongside existing lazy NNUE dirty-state replay, privately per
Worker. Board, NNUE/weights and public evaluator/tuner contracts are preserved.
**First-attempt Release11/11, ASan/UBSan11/11, default unsuppressed TSan11/11,
347runtime assertions in each profile, and8active TSan UCI checks PASS.**
56cold/warm searches match18 exactly (including NNUE-off), excluding only time/NPS;
bench321912. Independent native audit2298/2298 PASS after one saved checker-key
correction; all engine gates passed first attempt. Root rehashed251evidence files,
524live source/build originals and6single originals. The NNUE compiled object is
byte-identical to18, preserving the existing strict floating-kernel validation.
Windows19 first build, all10Wine checks,1184independent artifact checks PASS;
347runtime assertions,18947legal comparisons, exact352313. Root byte-verified all
205raw payloads,71sources,219unchanged parent files and8actual built PEs.
[Native proof](../validation/lazy-runtime-psqt-20261020/root-verification/NATIVE.json).
[Windows proof](../validation/lazy-runtime-psqt-20261020/root-verification/WINDOWS.json).
[Windows19 Zen5 ZIP](../releases/forge-6.4.19-candidate-windows-zen5.zip), SHA256
`f0ec03308098bf8e675647f091b3b1afeb74d2632d9c972883e5907cfcb23d85`.
**Verified hosted whole-process throughput gain versus18:** CPU+1.6084%
(95%block-bootstrap interval+1.2336..+1.9498%); wall+1.5990%
(+1.2217..+1.9459%). One frozen run39510219605 passed15same-binary A/A blocks,
31A/B blocks, all188processes/940canonical rows and every final integrity gate.
Independent calculation agrees within1e-12. Root compared all160consumed byte
records and200actual Git blobs, including both complete73/74source exports;
both hosted compiled NNUE objects are bit-identical. Keep this optimization as a
qualified Linux workload improvement. **No Elo gain, nativeWindows/Ryzen result or
Stockfish superiority is established; accepted integration remains5101.**
[Independent performance audit](../validation/hosted-runtime-psqt-performance-20261020/final-audit/REPORT.md).
[Root Git/input audit](../validation/hosted-runtime-psqt-performance-20261020/ROOT-INPUT-AUDIT.json).
Original result commit0124dbd075b252552a27264996b72cf2ef800598; frozen launch
payload5e50d99a93a381a881b4f1813dce462a3e4106bf. No retries or pooled outcomes.
Complete19checkpoint is independently verified:1762originals/1774payloads,
112207796bytes, combinedSHA256
`d90110e326c6d24c3045c8601ed4dd37ba7b9fbfc35c1bffcabddab6cf733f31`.
Both published parts were downloaded and hash verified. File/directory modes are
recorded; generic0600ZIP modes require explicit restoration in a NEW empty scratch
destination. Actual extraction/chmod recovery was not run.
[Archive proof](../validation/lazy-runtime-psqt-20261020/archive-complete/ROOT-VERIFY.json).
[Published part verification](../validation/lazy-runtime-psqt-20261020/archive-complete/REMOTE-PARTS-VERIFY.json).
[Prototype history](../validation/lazy-runtime-psqt-20261020/REPORT.md).

Latest isolated finite-tested candidate is **Forge6.4.18**, source
`fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b`, branch
`forge/correction-history-residual-20261020`. It changes one correction-history
update from EMA toward an already-corrected residual to residual increments under
unchanged guards, weights and clamps. It preserves all17work and accepted5101.
**First-attempt Release10/10, ASan/UBSan10/10, default TSan10/10 and8active UCI
transitions PASS. Nine Wine checks and1064independent artifact checks PASS.**
[Native proofs](../validation/correction-history-native-20261020/ROOT-NATIVE-PROOFS.json).
[Windows proofs](../validation/correction-history-windows-20261020/ROOT-WINDOWS-PROOFS.json).
Complete checkpoint:1,434live originals and1,446archive payloads independently
byte verified, including full native/prototype/Windows source and build trees.
Two parts, combinedSHA256
`fc000c6fc58b38c023d636880e82bf191b297fc8b7ea529d9c14153c8fbe5868`.
[Archive receipt](../validation/correction-history-native-20261020/archive-complete/ROOT-VERIFY.json).
All earlier failed attempts and directly published raw files remain retained.


[Windows Zen5 candidate ZIP](../releases/forge-6.4.18-candidate-windows-zen5.zip),
SHA256 `286a913f8bb6366d28020ef83bce5235809d1d991d41023609f0ea6446284ebc`.
Actual native/Windows bench11signatures321912/352313 are reproducibility checks;
no calibrated NPS difference, Elo gain or native Windows/Ryzen result follows.
The actual-method fixed6cp target learns6cp versus old3/4cp, while the larger64cp
reachable envelope and retention of noisy/aliased feedback are explicit risks.
This is an **unaccepted search ablation**, not a demonstrated bug repair.
[Experiment](../validation/correction-history-residual-20261020/RESULTS.md).

Fresh18vs17 strength preparation has closed the independently identified proof
rehash and mandatory-provenance gaps. The original disabled phase2 is preserved
at `be2033884a2cd82c5c9bd8d4b56dc2ca6ed72acd`;96 offline tests passed there.
Root binds335 exact finite proof files and verifies24 package/workflow entries.
After enabling the restricted first-attempt-only push workflow,94 applicable
offline tests and9 actual missing-gate controls pass. Two historical draft-state
assertions remain unchanged and are replaced by explicit READY/negative checks.
Final enabled-metadata review PASS; payload `1203e13cfd80451d7194c7fba2f775de71dc9604`
was published and one trigger push remotely verified at21:39:20UTC. Run
[39502109381](https://github.com/couns0538-sketch/dwqww/actions/runs/39502109381)
has passed the hosted source-build/test step; combined readiness/SPRT step is
running at00:02:19UTC on2026-10-21. Public metadata does not expose games or prove a particular
readiness subgate. Frozen0/+10,.05errors,equal10+0.1,256paired openings; no observed
game statistics or Elo result. Do not trigger/retry/resume this experiment.
Historical17binary/source47proofs remain genuinely labeled47; all72build inputs
equal baselineb590byte-for-byte. The hosted attempt must build actualb590 and
pass all9baseline CTests before games; candidate must pass all10.

Previous isolated finite-correctness-tested engine is **Forge6.4.17**, source
`47f0560221d986e41a309853e1295c557fcf5bf6`, on
`forge/promotion-see-20261020`. It preserves prior accepted work, residual NNUE
and its weights, and repairs promotion-recapture SEE before threshold shortcuts.
First-attempt Release9/9, ASan/UBSan9/9, TSan9/9 and8active UCI TSan checks PASS.
The actual qsearch witness changes SKIP_SEE to a searched legal Qxb8 capture;
324legal oracle cases and30actual search-margin answers pass. These are correctness
results, not Elo or a general startup/clock-reliability claim.
[Native proofs](../validation/promotion-see-20261020/native/ROOT-NATIVE-PROOFS.json).

[Windows Zen5 candidate ZIP](../releases/forge-6.4.17-candidate-windows-zen5.zip)
SHA256 `9c532d5394b58f8654e316de99b4a5771149e75327c31586ae179814212e85f9`.
Eight Wine checks passed;1211artifact checks passed after one README case-comparison
checker repair, with the original failed checker/logs retained and binary unchanged.
Linux/Windows bench11signatures385781/382424 are reproducibility checks.
No calibrated NPS difference or native Windows/Ryzen result is established.
Complete source/build/raw/qsearch/Windows evidence is verified and split-archived in
[archive-complete](../validation/promotion-see-20261020/archive-complete/).

**The one hosted17vs14 attempt failed in the harness before any games.**
Run[39492317400](https://github.com/couns0538-sketch/dwqww/actions/runs/39492317400),
results commit `0e292d6193918fa71a06b99798808ecb60e5807a`.
Both frozen engine builds and their CTests passed; baseline gross A/A passed.
The candidate emitted the correct `info string bench depth 11 nodes 385781 ...`,
but the readiness parser expected prefixless `bench ...`. Its mock GOOD fixture
shared that error. The original failed attempt and frozen package remain unchanged.
All75original payloads and40frozen inputs have been independently verified.
Candidate returncode/group-empty facts were not separately saved before the parser
raised, so full candidate readiness is not independently proved. **Games0; W/L/D0/0/0;
no Elo estimate, confidence interval, NPS comparison or H0/H1 decision.**
[Independent audit](../validation/hosted-promotion-see-strength-20261020/final-audit/REPORT.md).
That17attempt has not been retried or resumed. The independent18vs17run above
uses a different hypothesis and fresh opening cohort, with no pooling.

The accepted-lineage OwnBook bypass was reproduced on356e863. Exactexisting
repair af1941375111717f415a46d9ce0224c329034466 and child5101c252 passed both
Release4/4 suites and candidateASan/UBSan4/4; unchanged original book tests
reproduced the parent leak and suppressed it in both candidate profiles.
The independent807check audit and root76payload/binary-byte review passed.
Evidence was published at67aa4fed2a4f0d9d46d395e7815420001028e3fb before the
non-forced fast-forward. Current17lineage merges5101at3105720 with every production
byte unchanged; source47f0560 and its failed frozen attempt remain immutable.
Historical CI success metadata was verified, but authenticated original artifacts
could not be retrieved; the fresh local originals are separate evidence.

Both user handoffs are manifest/byte verified (145shutdown +28clock-replay payloads).
The original108.696ms response,84.647ms last-info discrepancy and0.049ms final gap
were independently recomputed; they do not locate the historical time-forfeit cause.
No new clock patch follows. Forge is the priority; GrokChess port is deferred.
[Handoff reviews](../validation/handoffs-20261020-1916-2120/HANDOFF.md).

Preserve prior failures:16original TSan batch8/9 initial UCI deadline,14original
60s barebench timeout, and12vs11 baseline time forfeit in startedgame85. Later
successful bounded diagnostics did not reproduce or explain those anomalies.
Earlier valid capped647vs644 (320games,W114/D101/L105) and6411vs649
(2048games,W427/D1194/L427) remain separate/inconclusive. Never pool them.
Details and next work are in[ledger](EXPERIMENT_LEDGER.md) and
[next experiments](NEXT_EXPERIMENTS.md); historical records remain in Git.

2026-10-21 01:54UTC checkpoint (actual root receipt time; prior checkpoint label corrected): actual parent22 TT investigation completed9table checks and12legal cold/warm root comparisons with exact response parity. 58683probes/6461old hits/3366eligible old cutoffs without stores;0tracked later victims, so replacement benefit unproven. Unapplied refresh policy retained; independent review/test preparation underway. Existing SIMD skill extended and validated27checks plus independent actual-object application; repo-local only, no skill-creator/global installation available. Environment configuration draft9 readback verified with unchanged install/network/secrets/runtime; requires user publication, no activation performed. Both hosted strength jobs observed running01:53UTC, games/Elo still unknown.

2026-10-21T02:28:43.330218+00:00 — Completed18vs17 actualequal10+0.1 result is VALID NATURALCAP/INCONCLUSIVE, notH0/H1:512games256pairs W92/D341/L79, penta[4,51,138,54,9], nativeLLR0.53/rootMLE0.533210492135936, descriptive+8.82±16.65 includeszero. SeparateAA fixed10000nodes/tc=inf4pairs8gamesdeterministic; neverpool. Independentall520games/74698legalplies,335proofs/784finalinput/517publicGitblobs/423buildpathsverified; rootrehash504payloads+784inputs+335proofs+517Git+auditmanifest exit0. Immutableoriginalresulta265945b62d955db454b1d0b9afc346ac3f3998b has72579119BZIPsplit2, SHAcbb517a2099b96f11dd4925e7e29d10a3f32b827b00233fc551dce389b9cb0d5. RawZIP0600transportmodegapexplicit; no numericoriginalpostrunmodesinvented/no livegate relaxed. Candidate18 retainedpromisingbutUNACCEPTED; descendants19..23 do notinheritacceptedElo. Exactnext18strengthtask isafreshlargerpreregisteredmatch, neverresume/poolthiscap; current23trialfirst.
