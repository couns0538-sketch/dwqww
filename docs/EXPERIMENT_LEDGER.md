# Experiment ledger

The authoritative [machine ledger](../validation/EXPERIMENTS.json) contains 106 records, preserving all 83 earlier IDs, exact inputs, hashes, settings, failures and evidence links. This is the concise reading index as of 2026-10-20.

| Experiment | Observed result | Acceptance scope |
| --- | --- | --- |
| Historical accepted `9108d012` | TT index/signature independence repair | Preserved reference, superseded by current accepted clock repair |
| Current accepted `356e863` | Timed-only admission-clock repair `294cf1b`, preserving TT repair and untimed/ponder behavior | Native correctness/admission-delay checks; no accepted Elo gain |
| AVX2, clock/stalemate, underpromotions | Arithmetic and regression checks passed on their recorded sources | Correctness/kernel evidence; timed VM attempts invalid |
| 6.4.1 versus original ZIP | 178 normal games, W/D/L 66/44/68; paired GLR −3.02565, H0 accepted for [0,+20] | Fixed 10,000 nodes/move only; no accepted gain or equal-clock inference |
| 6.4.3 coherent TT | Actual parent race reproduced; corrected Release/ASan suites and 38 full-engine TSan searches passed | Finite correctness; first faulty stress fixture retained |
| 6.4.4 score context | Forward/reverse regressions repaired; seven current parent assertions fail, candidate assertions pass | Release/ASan/TSan, ordinary behavior parity and Wine correctness passed |
| Same-binary speed A/A | 72 sessions/216 searches; one-thread wall ratios 0.6566–1.4704; identical work reported 339–1730 ms | Whole-engine overhead inconclusive; full A/B stopped |
| Windows artifacts/readiness | 6.4.4 five Wine checks passed; original 6.4.2 bundle remains immutable; a separate 6.4.8 bundle is now audited | No native Windows, physical Ryzen or Elo result |
| 6.4.5 legal witness | Parent and actual `82cd2c2` each passed18,947 oracle/state checks; Release8/8, ASan8/8 and exact parent parity passed | Seven Wine checks passed; kernel AA failed, speed/Elo inconclusive |

Original failures remain available, including timed forfeits, opening-representation rejection, the null-move stress fixture, incomplete manifest inventory, copied audit/launch metadata and incorrect package wording. No invalid games, separate candidates or microbenchmark ratios are pooled into cumulative Elo.

Immutable archives: [TT correctness](../validation/tt-coherence-20261019/complete-linux-correctness-checkpoint.zip), [speed A/A and independent audit](../validation/tt-coherence-20261019/speed-aa-calibration.zip), [rule-50 investigation](../validation/rule50-context-20261019/investigation-before-integration.zip), and [6.4.4 Linux validation](../validation/rule50-context-20261019/linux-validation-checkpoint.zip). See [current references](CURRENT_BASELINE.md) and [next experiments](NEXT_EXPERIMENTS.md).

6.4.5 original [kernel records](../validation/legal-witness-20261019/kernel-attempt1.zip) retain all60 blocks, failed calibration and descriptive ratios; they are not an accepted speed result.

6.4.6 qsearch pure-query deferral (`4e15dea`): Release8/8, ASan8/8, exact cold/warm parent parity and7Wine checks passed.419798/351063 signatures unchanged; no measured NPS/Elo. [Evidence](../validation/qsearch-query-20261019/STATUS.md).

6.4.7 lazy masks (`2c0c7ef`): Release8/8, ASan8/8, exact parent parity,60,138 byte-identical actual picker rows,7Wine checks and independent artifact audit passed. NPS remains unmeasured; hosted Elo attempt is inconclusive (see final result below). [Raw evidence](../validation/lazy-movepicker-20261019/STATUS.md).

Historical checkpoint before completion: run 39325939081 had started and build/tests had succeeded. Its then-running status is superseded by the audited final result below. No second workflow attempt was launched.

6.4.8 root effort (`7125b337`): actual mixed-bucket parent reproduction; stable full-Move repair passed28actual-iteration oracles, Release8/8,ASan8/8,untimedparentparity and7Winechecks+52/52audit.601ratherthan1355forc3d5; no actualtimed-stop/Elo evidence. [Original data](../validation/root-effort-20261019/STATUS.md).

Hosted647final:147normalrecords(W/D/L62/43/42),73completepairs+oneorphan;16mincap,noH0/H1. Native144game snapshot+43.66±28.69 is promising/descriptive; wholeattemptinconclusive. FullPGNunchanged+59Gitblobs+auditedlikelihood/openings+21066legalreplayedplies saved. Native648offlinebundle is verified43/43, gamespending. [Result audit](../validation/hosted-strength-20261019/independent-result-audit.md).

6.4.9 external-book control (`4edda780`): actual parent RED and five-transition candidate GREEN; Release9/9,ASan/UBSan9/9,exact parent parity. Eight Wine checks and independent artifact audit pass. No NPS/Elo claim. [Evidence](../validation/ownbook-control-20261019/STATUS.md).

Fresh 647-versus-644 confirmation was preregistered and pushed once at `f1b44cc`: [0,+10] SPRT, 160 natural pairs, disjoint openings, retained actual binaries/UCI exchanges/final rehash. Completed320normalgames/160pairs:W114D101L105, pentanomial[1,30,96,25,8], independentLLR0.4574291989231206, no boundary: capped inconclusive. All2794offlinechecks passed, including42454legalplies and full raw exchanges. Descriptive+9.77Elo has approximate paired95%interval[−10.47,+30.09]; no accepted gain. The prior147-game attempt is never pooled. [Final audit](../validation/hosted-confirmation-20261019/final-audit/REPORT.md).

6.4.10 NNUE fusion (`36f5b2f`): Release9/9, exact4.1MB update/21.2MB NNUE streams, six cold/warm parent search cases passed. ASan9/9+ASanstream,8Winechecks+bothWindowsstreams and independent audit pass; SSEstream matches too. Independent-host primaryAAfailed; noAB/kernel. NoNPS/Elogain.

Hosted NNUE performance39334266771: allsource/build checks passed, but twelve same-binary primaryAAprocesses failed the strict3%gate (maximum wallratio1.04843). No A/B or kernel comparison ran. Final frozenhashes pass; originalsource/executables/results preserved on the immutable results branch. No retry or speed claim.

6.4.11 capturefusion (`c5cbf97a`): Release9/9,ASan9/9+instrumentedexactupdate, bothactualcoreNNUEstreamsparent/crossplatformexact, sixcold/warmparity,8Winechecks+independentartifact/codegenaudit pass. Signatures419798/351063. FirstincompleteASanexportconfigurefailedandretained; completeattempt2passed. NoNPS/Elogain. [Evidence](../validation/nnue-capture-fusion-20261019/HYPOTHESIS.md).

Historical integration2fc649e contained three tools/evidence commits, engine source9108, preserved by merge3cabc1b. Current accepted356e863 adds timed-only clock repair294cf1b; source is no longer unchanged9108. OlderTTtagtimeout andtruncateddiagnosticrawlogremainunresolved, noEloacceptance; exactblockedarchivepublicationholdretained. ItsweakerhistoricalmatchhelperisnotusedbynewstrictSPRT.

Actual NNUE output reuse counter: 1,417 exact-input repeats in 275,743 calls (0.5139%); all21processes/searchparity/counterrepeat pass. No outputcacheimplemented; rejectedasnextpriority, notameasuredspeedresult. [Evidence](../validation/nnue-output-cache-20261019/REPORT.md).

Combined6.4.11-versus6.4.9 run39348571407 completed validly:2048normalgames/1024pairs,W427D1194L427,pentanomial[25,190,591,196,22],nativeLLR−0.76/independent−0.7565242360831034. Natural cap, no boundary: inconclusive; no accepted gain or equivalence. Final independent audit passed99payloads/41inputs, source/build provenance, fresh openings,284195legalplies and complete1.1GBrawlog. Results `eb1c1b7ff3b5769609cf3dd5290e29cde0912763`, ref `results/nnue-strength-39348571407-1`. [Final audit](../validation/nnue-strength-20261019/final-audit/AUDIT.md).

Original confirmation push failed on its152.78MB log against GitHub100MB (original log584/587). Recovery1 `39349372297` retrieved/uploaded original bytes but failed nested inventory ordering (Path versus relative POSIX strings), not a payload mismatch. Corrected suite17/17 passed; frozen archive helper unchanged. Recovery2 `39350375158` succeeded:99recoverypayloads/85originalZIPfiles verified, results `61aabe2cd23e8171c625f1cc1d7e798d0faacc28`, ref `results/confirmation-recovery-39332822379-39350375158-1`. Failed attempts retained; no match rerun.

Rejected6.4.12 all-stripes prototype `a5d2fcb5b3270c50b96bcc1b2ebd3bc42db5f2fc`:Release9/9 and exact parity passed, but default TSan hit64-held-lock capacity on acquisition65. Source/failure retained; no disabled detector or transferred acceptance.

Revised6.4.12 gated source `8865666cc0ab4961cd507bae40ff6ce44e9319df`:Release9/9,ASan/UBSan9/9,TSan9/9;7actualAPIgroups/profile,8activeUCITSanedges,8Winechecks+independentartifactaudit pass. Six parent cold/warm cases exact;419798Linux/351063Windows signatures unchanged. Mutex operations706157→8204 are not NPS/Elo. Shared/default/SMP stay synchronized; foreign calls block; lifecycle requires all accessors quiescent. Full1427-file evidence archive is verified in two parts. [Evidence](../validation/single-thread-tt-20261020/STATUS.md).

Fresh6.4.12-versus6.4.11 package reviewed/ready, **not launched at this checkpoint**:0/+5SPRT,1024freshpairs,equal2+0.02,serialThreads1/Hash32/OwnBookfalse. All30proofhashes/23packageentries and root-ready check pass; root will record actual launch ID. A separate regression/follow-up must reconcile accepted timed-only clock contract294cf1b with frozen886 untimed/ponder reporting; timed admission is already accounted for. Keep frozenstrengthsource unchanged. No NPS/Elo or Windows/Ryzen/Stockfish inference.

6.4.13 clock reconciliation (`cecf0b9`): all27CTest suites,21origin+21TTAPI groups,
8active-UCI TSan edges, exact parent parity and8Wine/872artifact checks passed.
No NPS/Elo or hosted-forfeit remedy proven. Actual GNU-wrap observation failure
was retained and corrected with verified ELF interposition. Source and full
proofs: validation/upstream-clock-reconcile-20261020/.

The once-launched TT run39403471059 failed on a baseline time forfeit in started
game85. Original84records/42pairs remain invalid for acceptance;126-checkaudit
and full legal replay pass, original resultsffc598ad. Do not retry or change gates.
Actual extension-path trace found5038child counter mismatches; isolated proposal
clears all seven classes at unchanged419798nodes. Production patch is next;
shallow eligibility was already unchanged, so no decision/Elo gain established.

6.4.14 (`21538ec`) applies the independently reviewed extension-path repair.
Release/ASan/TSan each9CTest+7actualTTAPI,8activeUCI,8Wine and914artifactchecks pass.
Actual normaltrace5038counter mismatches->0; synthetic inherited6 old8/new7.
One originalbarebench60-second timeout remains unexplained despite three later
normal syscall diagnostics. No NPS/Elo acceptance; candidate stays isolated.
[Proof](../validation/double-extension-path-20261020/STATUS-6414.md).

The baseline-forfeit causal replay completed once: one cold search and the original
50-search warm history. Final responses were 24.888 ms cold and 32.140 ms warm,
versus the original hosted 108.696 ms with 63 ms remaining. All frozen inputs and
51 legal bestmoves checked. Ten warm moves differed from the historical run;
the original stall did not recur and its cause remains unresolved. This is
diagnostic evidence, with zero games and no strength or reliability acceptance.
[Original capture and phase analysis](../validation/time-forfeit-causal-20261020/REPORT.md).

6.4.15 pin-aware SEE (`8d303e4`) passed all 27 native CTest suites, eight active
UCI TSan transitions, eight Wine checks and 929 artifact checks. Its actual API
prototype corrected eight errors across 302
legal cases with no candidate oracle mismatch. The permanent 46-case mirrored
tests produced 16 expected failing assertions against frozen parent21538ec.
Independent review found no patch-specific blocker; hot-path overhead and the
inherited recapture-promotion limitation remain explicit. Ten additional targeted
controls correct nine more baseline errors; two promotion limitations are retained
as known failures. Linux/Windows bench signatures are 385792/382424, with no
NPS/Elo acceptance. Source, binaries, commands and raw logs are retained.
[Experiment](../validation/pin-aware-see-20261020/HYPOTHESIS.md).

6.4.16 (`553caef`) applies the equivalent dynamic SEE mask. All 316 API outputs
and eight actual benchmark-position scores/moves/PVs match15 exactly,385792
nodes. Occupied slider queries742109 are replaced by474626 empty-board lookups
and49015 path classifications; no speed claim. Release9/ASan9 and8Wine/1151
artifact checks pass. TSan8/9 passed, with OwnBook's initial UCI handshake deadline
before any search; cause unresolved. A separate once-run timestamped pair passed the parent
handshake and candidate5OwnBook transitions; the timeout was not reproduced.
The original8/9batch remains FAILED.
The unlaunched15strength package/pool
is preserved, and a separate fresh16versus14 package is pending final gates.
[Source and counter proof](../validation/pin-see-filter-cost-20261020/README.md).


Promotion-recapture SEE investigation on16 reproduced six exchange-value errors
and44wrong threshold answers across10legal cases, including both false-negative
and false-positive see_ge(0) pairs. A guarded outside-production gain-stack
prototype matches all324legal oracle cases/30adjacent brackets and preserves
314ordinary API rows byte-for-byte. No production17/full tests/Elo claim yet.
[Evidence](../validation/see-recapture-promotion-20261020/SUMMARY.json).

Installed Stockfish19 advertises UCI_Elo1320..3190. Exact3200 is unsupported;
3190 is the nearest supported limited-strength target. Zero target games run;
Forge's absolute rating and a200Elo gap remain unestablished.


Applied6.4.17 promotion-recapture SEE source47f0560 is isolated/pushed. Permanent
parent16tests produce16expected assertion failures; reviewed repair passes.
Complete Release9/9PASS including perft/UCI; compiled core equals prototype
d772f89980edb0e9f7fd5da99ef5c7bdb402aa8319082907b2bf31180359bd12.
Thirty actual-margin API answers pass at-40/-150/-450 versus10parentwrong;
bench11signature385781nodes. Raw uncalibrated1016ms/379705NPS is not a speed
comparison. ASan/TSan and Windows gates pending, zero games/Elo claims.
[Source and tests](../validation/promotion-see-20261020/HYPOTHESIS.md).


6.4.17frozen native validation completed on firstattempts: Release9/9,
ASan/UBSan9/9, TSan9/9 and8activeUCI transitions PASS; exact17sources/binaries
verified unchanged. Full27tests include perft/UCI/ponder/OwnBook. Separate
Windows17eightWine checks PASS, observed382424benchsignature frozen before
packaging. Artifact audit and full-search witness pending. Source16failedbatch
staysFAILED and unlaunched16strengthpoolreserved. No speed/Elo accepted.


6.4.17 hosted strength attempt39492317400 is **FAILED IN HARNESS BEFORE GAMES**.
Frozen source47f0560 versus14source21538ec; trigger payload352b6ff. Both complete
Release builds/CTest passed and baseline grossAA passed. Real candidate output
`info string bench depth 11 nodes 385781 time 222 nps 1737752` was rejected by
an anchored prefixless parser; the mock GOOD fixture repeated that false assumption.
Independent audit verifies75original payloads,40frozen inputs and both72-file
source inventories/provenance. Original results0e292d6193918fa71a06b99798808ecb60e5807a,
archive08e9ffaa5f62652d9ab56959acd5588ea2b63384950a06971648c1fe27e5d1d2.
The candidate returncode/group-empty facts were not separately archived before the
parser raised; do not claim complete candidate readiness. W/L/D0/0/0, no Elo/CI,
no speed comparison or native SPRT decision. No retry/resume/gate relaxation.
Future-only offline parser/process-fact repair is separate from this frozen failure.
[Audit](../validation/hosted-promotion-see-strength-20261020/final-audit/REPORT.md).


Accepted OwnBook repair integration completed2026-10-20 20:44:42UTC: remote
forge/6.4-hourly-20261019 fast-forwarded356e863→5101c252 without force after raw
evidence publication67aa4fe. Only production difference is the existing one-line
OwnBook condition; unchanged156line regression accompanies it. Baseline/candidate
Release4/4 each and candidateASan/UBSan4/4 passed; original book script verifies
15checks including leak reproduction and suppression. Independent807check audit
and root76payload/livebinary/core/config review passed. Candidate17lineage merge
3105720 preserves all production bytes47f0560. Acceptance is specific correctness,
not NPS/Elo. [Receipt](../validation/accepted-ownbook-integration-20261020/INTEGRATION.json).


Future-only harness repair validated outside the frozen17package: captured-byte
parser RED5/15→GREEN15/15; original process-evidence suite RED5/5→GREEN5/5 with
actual benign Python subprocesses. Review-time pre-hash overwrite regression is
retained. Root independently verifies117original payloads and15parser methods.
Extended the existing strength-validation repository skill with canonical captures
and pre-verdict/post-cleanup process facts; fresh3case application, YAML and3links
pass. No duplicate or cloud installation claimed. Failed17exit/group remains
UNKNOWN and attempt staysFAILED. [Evidence](../validation/chess-bench-parser-repair-20261020/REPORT.md).


6.4.18 independent correction-history ablation sourcefc51e43 is implemented on a
new isolated branch fromb5908f0 (17engine47+accepted5101 preserved). Exactly one
search arithmetic assignment changes: EMA toward already-corrected residual becomes
residual increment with unchanged guards/weights/clamps. Exact-core Release and
ASan/UBSan54/54 each for both variants (216PASS); original intentionally differs
17/54 under the new behavior contract. Fixed6cp target oldone/twotables3/4cp versus
increment6cp. Combined reachable range expands15→64cp in saturation fixture;
retained disparities/stale material feedback are explicit risks, not a knownbug.
Initial missing-cmake-PATH attempt preserved; exact tool path attempt2 completed
in~5minutes under external600s monitor (executed runner had no subprocess timeout).
Full permanent54check regression is registered as10thCTest; finaltestguard avoids
out-of-range slot access on fixture discovery failure. Astra production review has
no remaining implementation blocker; root69payload/source/216check review PASS.
Fullnative/Windows/strength results remain pending. [Evidence](../validation/correction-history-residual-20261020/RESULTS.md).


6.4.18 fc51e43 first full Release10/10 and ASan/UBSan10/10 PASS. Exactpermanent
testobject linked with frozen17core produces17/54 expectedbehavior differences,
while candidate54/54 passes. Root independently verified both10CTest transcripts,
source/testbeforeafter equality and16live executable/core hashes. One barebench11
signature321912nodes,1738ms/185219NPS; timing is uncalibrated, no speed ratio or
strength result. TSan is running; Windows and all match gates remain pending.
[Native evidence](../validation/correction-history-native-20261020/ROOT-RELEASE-ASAN-PROOFS.json).


6.4.18fc51e43 finite validation is complete: firstattemptRelease10/ASanUBSan10/
defaultTSan10,8activeUCI,9Wine and1064artifact checks PASS. Root independently
rehashes113native records/484live source-build files and196Windows records,
compares19ZIPpayloads toexpanded bytes and verifies183originalraws. FinalWindows
ZIP286a913f8bb6366d28020ef83bce5235809d1d991d41023609f0ea6446284ebc,
native/Windows bench321912/352313. No NPS/Elo acceptance or nativeWindows/Ryzen
proof. RootZIPchecker initially used Path.with_suffix on a versioned folder and
failed before ZIP verdict; exactpath corrected, original candidate/audit unchanged.
Fresh strength draft remains BLOCKED on two independently identified provenance/
final-rehash harness gaps; no18launch or games. All72baselineb590build inputs equal
genuinelybuilt47source; no binaries relabeled and futureactualb590CI9CTest required.


6.4.18 complete checkpoint independently verified:1,434live originals unchanged
before/copy/after,1,446payloads,123,154,486B split67,108,864+56,045,622B.
CombinedSHAfc000c6fc58b38c023d636880e82bf191b297fc8b7ea529d9c14153c8fbe5868;
manifest3000a9c26a427104eed73a51da6a344e49e76ae23b58450823df4a542a1028d4.
Full native3builds/source, both prototypeattempts, Windows fullbuild/source/capture,
release ZIP/expanded bytes and all current finite proof records retained. Root
reassembled/hashchecked everypayload and comparedall1,434live bytes. Trustedarchiver
unchanged; no ignores/untracking/deletions. Mutable futurestrength package excluded.
Candidate WindowsZIP and native/Windows proof publicbyte-readbackPASS atdaa09e7.
[Archive](../validation/correction-history-native-20261020/archive-complete/ROOT-VERIFY.json).

18vs17 phase2 collector/review closure: original blocked package preserved at
be2033884a2cd82c5c9bd8d4b56dc2ca6ed72acd. Required source/build evidence, final
proof rehash, executable-mode copying/preflight and450s/480s cleanup headroom
are repaired without changing engine code.96/96 original offline tests PASS;
independent16/16 PASS. Exact source review proves one arithmetic line plus
version/test metadata, NNUE unchanged. Root rehashes/binds335 actual finite
proofs;24 package/workflow hashes PASS. Enabled-only-final review pending,
94 applicable offline tests PASS23.282s and9missing-gate controls rejected;
2 historical actual-DRAFT assertions remain preserved and are replaced by
explicit READY/negative controls. No18 engine execution or match by preparation;
no games, NPS ratio, Elo estimate or source acceptance. One new attempt only,
serial10+0.1 SPRT0/+10,.05errors,4AA+256SPRT pairs; prior anomalies remain open.
[Ready checks](../validation/hosted-correction-history-strength-20261020/ROOT-READY-METADATA.json).

18vs17 final enabled review PASS (24inventory/335proofs). Frozen payload1203e13c
was pushed to the existing isolated branch with remoteSHA and public raw workflow/
protocol/inventory byte readback PASS. Exactly one new trigger branch
forge/hosted-correction-history-strength-20261020-213918 was created and verified.
Run39502109381/job118901918661 links the exact payload; source-build/test step
SUCCESS and combined readiness/SPRT step in progress at21:41:47UTC. No original
game evidence or count is exposed by that metadata; W/L/D and Elo remain unknown.
Do not retry/resume/pool. Baseline b590 and candidate fc51 source pins unchanged.
[Launch](../validation/hosted-correction-history-strength-20261020/publication-attempt1/LAUNCH.json).

19 runtime-PSQT candidate frozen61f598056572dfade6994af8ad2e38817cd28aa3 on
forge/lazy-runtime-psqt-20261020. One exact-behavior optimization: Worker-private
PSQT/unclampedphase replay along unchanged NNUE dirty-state path; root refresh
uses current parameters. Public evaluator, trace, Board, network and float order
preserved. Prototype parent344/227missing-cache-state RED has no failed eval
oracle assertions; source was hash-verified reconstructed after execution and
is explicitly not an atomic before/after capture. Initial344 and refined347
GREEN fixtures differ; all original fixtures/logs/cores/exes remain retained.
Both prototype11CTest batches passed; final typed refresh removes a new GCC
inference warning, with inherited TT warnings preserved. Source review/addendum
has no blocker. Final frozen19 Release11/11 and347/347 runtime checks PASS;
56cold/warm searches (7positions xNNUEon/off xparent/candidate xcold/warm)
match every logical row, PV/ponder legality passes, hashes unchanged. Bench321912.
ASan/TSan/8active/Windows pending; speed/Elo unmeasured. No accepted branch change.
[19 evidence](../validation/lazy-runtime-psqt-native-20261020/RELEASE-RECEIPT.json).

Existing strength skill extended with mandatory source/build proof sets, final
rehash coverage, execute-mode preservation and internal/outer timeout headroom.
Frontmatter/five links and fresh four-case application pass; project-local files
are available. Cloud/executor skill catalogs are empty and skill-creator is not
exposed; no cloud/global installation claimed. Original18failed parser remains
failed; no skill-based Elo or causal efficiency gain claimed.
[Skill validation](../validation/strength-skill-provenance-20261020/SKILL-APPLIED.json).

19completed qualification (2026-10-20T22:24UTC): first Release11/ASanUBSan11/TSan11,
347actual-Worker runtime assertions each,8active TSan UCI,56exact parent cold/warm
searches PASS. Bench321912. Native independent audit first failed only on its own
wrong snapshot-key lookup; unchanged originals and corrected read-only audit2298/2298
PASS. All failed checker evidence retained. Root rehashed251evidence+524whole-tree+
6single originals. NNUE compiled object is bit-identical to18.
Windows19 first build8PE+10Wine checks+1184audit PASS; bench352313. ZIP13,577,092B,
SHAf0ec03308098bf8e675647f091b3b1afeb74d2632d9c972883e5907cfcb23d85.
Rootverified205rawpayloads+manifest,71sources,219parentfiles,20distributionmembers
and19checksums. Root checker first incorrectly expected205rawZIPmembers rather than
205payloadsPLUSmanifest; saved/corrected checker PASS without engine rerun. No speed
orElo claim. Separate disabled performance packet in review; full19archive being built.
[Root proofs](../validation/lazy-runtime-psqt-20261020/root-verification/).

18vs17 single run39502109381 stillrunning at22:23:32UTC after hosted build/testPASS.
Gamecounts/WLD/Elo unavailable from public metadata; no retry/resume or pooling.

19complete recoverable archive published at5e50d99:1762live originals/1774payloads,
112207796B combinedSHA d90110e326c6d24c3045c8601ed4dd37ba7b9fbfc35c1bffcabddab6cf733f31.
Root independently reassembled parts, rehashed all payloads and compared all live
original bytes/modes. Both rawGitHub part downloads match. ZIPexternal0600modes
require embedded mode restoration; scratch recovery itself was not executed.

19speed attempt launched ONCE at22:43:53UTC, observed run39510219605/job118929090351
on exact5e50d99payload. Preregistered whole-process fivebench11samples,15AA/31AB
blocks, CPU+wall calibration and95%block-bootstrap gates. All31proofs/21package
entries and seven unchanged execution files reviewed;49READYchecks PASS in4.671s.
Original disabledpacketd9c4071 and failedcombined45check/60swrapper retained; only
syntheticfixtureIO changed, actualbenchmarkdeadlines unchanged. No actual speed,
NPS or Elo result available atlaunch. [Protocol](../.github/hosted-runtime-psqt-performance/protocol.json).

Existing strength skill extended for persistence-failure cleanup and affinity
restoration, reusing the skill instead of creating a duplicate. Frontmatter/sixlinks,
fresh seven-criterion application and root20-record rehash pass. No causal efficiency
or Elo claim. [Skill evidence](../validation/strength-skill-cleanup-20261020/REPORT.md).

19qualified workload speed result: actualrun39510219605/result0124dbd completed.
All188processes/940rows,15AA/31ABblocks,21package/31proof/160frozeninputs PASS.
Independent stdlib whole-block bootstrap: CPUratio1.0160844162440468,
95%CI[1.0123361440981815,1.019498290677596]; wallratio1.0159896183154886,
CI[1.0122172959743965,1.0194589268676844]. Keep+1.6%workloadthroughput gain;
minimumAAblocks near.95boundary are retained. Original1237payload/4169887BZIP
SHA8971727a40556de34edd201123af8211cef15b341d9b0b352baa936de24bfcdf.
Rootalso compared200actual frozen Git blobs; both hosted NNUEobjects identical.
No Elo/nativeRyzen/Windows/Stockfish claim. Accepted5101unchanged;18SPRT running.
[Audit](../validation/hosted-runtime-psqt-performance-20261020/final-audit/REPORT.md).

20pawn-span-fill sourcefc2391870b3bf2cd4d8fc20c7406ea6439c69c5e frozen/published.
Old span loop replaced by exact unsignedforwardfill8/16/32 using existing pawn
attack mask. Source19baseline61f5980. Prototypefirst12Release/37320maskchecks PASS;
final wording-onlyfixture compiled/directpassed against unchanged actualcore.
One relocated link dependency-output path failed and is retained; corrected path
links same object/core, no engine/sourcefault claim. Original table lookup shares
its generator; independent oracles are oldpassedmaskloop and explicitrankwalk.
Publiccached/hot/uncached/fulltrace95positions/61465integers match19; two normal
compiles/two probes, allinputs unchanged. Frozen20onlychangesversionmetadata from
finalprototype75. Native36/8active/56parity chain started after root sourcegate and
explicit clearance; allresults pending. Windows+performance20are gated/disabled.
[Prototype](../validation/pawn-span-fill-20261020/CHECKPOINT.json).
