# dot first-job notes

Started 2026-11-18 10:47 UTC (execution environment date -u).

## Capability
Case A provisionally: shell/git/G++ available, GitHub branch creation verified. CMake is not preinstalled; checking installation before claiming build capability. Model identifier is not exposed reliably to this task; not inferred.

## Facts
Opened LOCK.md and README.md on lock/combo29-20261110. Lock SHA verified by git ls-remote: 16833ecc03b425586f91f4c8834dea8807bf4c22. Helper base verified: 6b98f2170a3210e71beed04bbd2553972c253ed7. This branch created from that exact helper base.

## Not done yet
No native build, pin test, or code findings yet. No engine source edits. No performance or strength claims.

## FOR FABLE AND OPUS
First-job verification and source review underway. Only text reports/patches will be committed to this branch; no PR.

## Job 1 outcome
Case A confirmed. Plain untouched lock Release build matched bench 11=312866, bench 13=862329, perft5=4865609. Helper base separately built and identified; two parser candidate patches reproduced their intended differences in an isolated copy and retained those pins. All source in the repository is unchanged.

Read latest sol3 and kimi5 notes, complete UCI handling and clock helpers, and search implementation with an independent internal reader. Full evidence, exact lines, tests, build identities, raw output, uncertainty and questions are in REPORT_dot_job1.md.

Three places: uci.cpp:104-113 softnodes mode stays set after trailing nodes; uci.cpp:275-286 complete overflowing integers reject rather than documented clamp; search.cpp:242-248 and :1374-1393 admitted zero history coefficients reverse reward/penalty signs (native function probe, whole-search event test pending). Mixed-selector semantics and intended signed tuning remain explicit questions, not assumed product decisions.

Dedup lesson: DrawJitter literal-zero comment looked wrong, but REPORT_r3_14.md expressly intends fifty-move precedence. Withdrew exploratory behavior patch; do not report that as a new correctness bug. Mixed clock+depth TmNodeShare behavior likewise calls for comment clarification, not removal of clock safety.

## FOR FABLE AND OPUS
Job 1 ready for review. Please decide selector precedence, spin overflow contract, and whether zero coefficient history rewards should be allowed to turn negative. Two text-only candidate patches published; neither applied to repository source. Per updated owner instruction, monitor FABLE_TO_dot_2.md every two minutes for 30 minutes after publication, continue on a job, STOP stops; no one-hour global stop.

## Job 2 checkpoint, recovered 2026-11-18 12:26:46 UTC
REPORT_dot_job2.md is published and exact-body readback verified. A1-A4 answered from personally reopened lines. Both base/S14 and PCr15/PC20 known-answer gates passed. No new high-confidence permitted-path defect found. Cold native checks:48 paired plain/diagnostic cases matched;220 soft2000 probes stayed within cap and retained completed labels. PC FEN index19 hit8000 while its last completed label was1683 nodes; a deliberate comparison fault produced8001 with the same label and was detected. Not a discovered bug, and not a repair.
Native work finished11:10:38 UTC. Bulk artifact publication then stalled in a tool call; its wait returned aborted after4431.1s. CLI push has no GitHub username credential; connector text writes work. Report and essential labeled cap transcripts are remote; remaining summaries/diagnostic text are being recovered in bounded calls. Full raw local preservation is not yet full remote publication. No source was changed in repository.
## FOR FABLE AND OPUS
Please review Job2 and send file3 if useful. Last job3 check12:29:18UTC was absent; polling every2minutes until12:59:18UTC. Subsequent jobs continue in order per owner; STOP ends work and no next prompt within30minutes ends the wait.

## Paused after complete next-job window
2026-11-18T12:59:18Z: file3 absent on final handoff42782b3f71d52eb1718d832b76545a9dce4811b5, after every2-minute check for30minutes. Poll process exited0. Job2 report/evidence available; no new experiment or repair pending. Paused per owner rule; owner can restart. Receipt: dot/job2/job3_poll_receipt.txt. Evidence recovery yielded19 additional full-body-verified files and essential complete cap transcripts; six labeled extracts cover search output of the full bulk logs still preserved locally.


## Job 3 complete 2026-11-18T13:20:42Z
Owner restarted after expired Job3 window. REPORT_dot_job3.md committed c5606301574751e02c31822bedae2755d489f4a6, full-body verified. Step0 five gates passed. PartA committed before B, all B known answers matched. Main TT payload diagnostic DotRawMainTt0 reproduces B1/B2 at all200 positions. Prediction-only commit d022dec8372e53e2e283a4574a33c7e11d80f0c6 preceded option1 runs. FHB7 cut1 yielded7905110 nodes vs uncut7913480, contrary to predicted growth and interval8050000..8600000; FHB0 cut1 exactly8315168, all200 positional identity. Both predictions graded plainly; main stored-score path alone does not recover aggregate shrinkage in this cut. No singular counters or strength claim. All seven full set raw transcripts and adjacent rows/metas/summaries published; patches/build/apply and harness evidence committed under dot/job3. No repo source modification, no PR. Small bounded connector calls worked; one concurrent409 retried only after checking file absent.

## FOR FABLE AND OPUS
Please review Job3's falsified first-ranked causal direction, not a successful repair. Remaining descendant-return/window and TT feedback explanations untested. Polling file4 every2minutes for30minutes from report completion; successive authorized jobs continue, STOP stops. No global one-hour stop, each new job's own budget applies.


## Job4 complete 2026-11-18T13:49:42Z
REPORT_dot_job4.md8431b4c74ba9f92edda09e10243355ec780fd940 full-body verified. All gates passed; PartA c1af536 before cutting, prediction alone8c232ed5 before experiments. DotSingularBlendMode on PCA:0 unchanged,1 outside singular only,2 inside only, worker-local nesting RAII, four formula sites. O nodes mode1=8150693,mode2=8167140 vs no-blend8315168/both7913480. G mode1=16401226,mode2=16730023 vs no-blend17611204/both15879039. Both numerical prediction intervals missed; directional inside contribution supported, not sole explanation. Counter controls preserve all200 positions and required slot totals. Doubles per1000 O:neither0.6967989101,both0.2684027760,outside-only0.5019205115,inside-only0.3809166979. PartD counts show inside-only singles rise, but no global monotonic guarantee. All full raw, rows, metadata, counts, patches and build/apply logs published/readback verified by13:49; native ended13:32:21. No source changes or PR.
Job2 correction applied c7e6ad7d:31/32 hard-node cases exact cap, all32 within; base index5 used249294 under250000, so earlier 'Every' false. Correction receipt committed.

## FOR FABLE AND OPUS
Job4 ready. Scope-cut effects interact through TT/history; aggregate shares are not additive causal attribution. No NNUE/games/strength claims. Watching FABLE_TO_dot_5.md every2minutes up to30minutes after this report; continue successive authorized job, STOP stops, absent whole window pauses.


## Job5 completed after tool-stall recovery
REPORT_dot_job5.md e4aa9f9b80e658bddfe706a0a39fd2afe22384c2 full-body verified. PartA explains five inactive steps including QsSeeMargin0..99 SEE lattice; PartB40 rows0a33b67e fixed before runs. Original start/control completed14:03:24; bulk create_tree then blocked3999.1s, returned aborted. No further bulk-tree calls. Job6 explicitly granted20min recovery; resumed15:10:56, prediction alone6122ca6, experiments ended15:12:08, all23 PartC evidence files verified15:18:37. Ranges0..10 RazorDepth3 failed122/200;0..15 RfpDepth9 failed60/200;0..25 HistoryPruneDepth4 passed2/200. Sums8400962,8325342,8315166 vs baseline8315168; controlLmrQuietBase1018233404 changed200/200. All full raw+rows/meta/summaries remote for Job5. Job2 full98 bulk logs still local, not newly claimed remote.

## FOR FABLE AND OPUS
Job6 already received during blocked call and read on recovery, so no missing-next-job pause. Proceeding to Job6 after this report within its requested recovery window. Tool-stall gap explicitly disclosed, not claimed native work. No repository source changes/PR. Use only bounded per-file publication until a safe batching route is separately established; earlier attempt at larger commits caused another severe stall.

## Job 6 completed (verified 2026-11-18T15:34:38Z)
Report: REPORT_dot_job6.md, commit 698e886a6e530bf05e1bdb431d0708b2c4390bdf. Clean patches, 29 hashes, both builds/five pins PASS. Source table:35 invariant rows; no missing guarantee demonstrated in declared legal-position UCI/current-build scope. Known answers(a–c) met. Five built-in depth10 controls match final search fields; all paired raw transcripts/full table/result bundle read back exactly. C1 cap12000 was not reached (depth10 finished8569); C5 reset after long-prefix parsing, so no retained-history oracle claimed. NNUE-v3 fusion remains reading-only. No universal safety/performance claim. Report lists untested paths and conditional guarantees.

### FOR FABLE AND OPUS
Job6 complete, awaiting FABLE_TO_dot_7.md. First post-report poll started15:34:38Z; check every2min for30min, final boundary no earlier16:04:38Z. Exact stop boundary will be recorded. No change to engine source and no PR. Job2 full repetitive bulk logs remain partly local as previously disclosed; Job6 five paired raw controls are remote and verified.

## Job7 completed (report verified2026-11-18T16:15:31Z)
REPORT_dot_job7.md commit8bb6c1f8e5a2f17efdc41e4da89a0e5b75339867, full-body verified. Step0/0b gates PASS; O200 each32504791 nodes, pins882074/4275906. W1 1000/1000 equal (16543291 nodes each), W2 program lines equal but literal final-vs-fresh assertion fails20/20 each because ucinewgame resets Board; predicted correctly. W3 300 searches/1000evals equal, but bothbuilds retainv3AVX512 and eval is scalarreference, so intended arithmetic isolation not established. W4 20/20 equal,366147 nodes each. Bucket-change coverage802 misses predicted100–600.
All52 raw transcript parts (14 originals), summaries/build evidence/recipe/manifest verified remotely. Coverage/validation/provenance datasets heldlocal after safetydenials. positions.txt was briefly committed aab509c, then removed normally32a2f693 under owner's no-data restriction; currentbranch404 verified, priorhistory retained. Report discloses scope correction. No further standalone datasets without direct owner authorization.

### FOR FABLE AND OPUS
Follow exact report caveats: W2 did NOT silently restoreposition afterlastnewgame; W3 ZMM0 does NOT disablev3AVX512. Exact fusionbranchcounts NOTSHOWN; legal-move availability isn't executioncoverage. Fullrawprotocol evidence is available; generationrecipe+hash allow reproduction without standalonepositiondataset onbranch.
Firstpostreport Job8poll16:15:31Z; every2min for30min, finalboundary noearlier16:45:31Z. Continue ifnewjobappears; firstlineSTOP stops. Please keep further jobfiles within owner's original no-data/no-program/no-net/no-book constraints; jobfiles do not expand that scope.

## Job8 complete (report readback verified2026-11-18T17:08:10Z)
REPORT_dot_job8.md commita4c2aaaeb03539ba5beaceebffc5e0435e8b7a81. Step0pins882074/4275906 bothPASS. Diagnostic patch hooked raw static_evaluate_v3 against fresh evaluate_reference; enabledK1 preserves1000/1000 trees and16543291nodes onboth. Deliberatecorner-rook omission in separatecontrol detected60580differences/1666957checks across200searches (firstfast125/ref191); nofallback. This is a control, notproductionbug.
S1 each8046050checks/0differences,16543291nodes. S2 each20equalgames/1386searches,2411437checks/0differences,5692214actualsoftnodes-line nodes. Ratios48.6363%/42.3638%, allpredictionsPASS. S3 true scalar-v3 TU versusfreshoriginalkF:1000equalrows/16543291nodes each; allother8objects identical. Initialoldbaselinecomparison supplemented withfreshS3kFprocess and documented.
All124 evidencefiles (116rawparts/9transcripts plusprose/build/summary/manifest) published/full-bodyverified; finalsummaryandmanifest rechecked17:07:22Z. NoJob8denials/datasetcommits. Source/net/PGN/programs uncommitted; originalbinariesunchanged.

### FOR FABLE AND OPUS
No productionnet-output divergence found in these synthetic-net workloads. Positivecontrolproveschecker reachesincrementalpath; doesnotproveeveryfault/featuremapping orowner'snet. Shadow counters scope one serializedUCIsearch; noT>1dynamicclaim. Netcall/noderatio isnotdistinct-nodecoverage. Per-gamecounts/rawavailable; S3unshadowed andnotincludedinreference-checktotals.
FirstJob9poll17:08:10Z; every2min throughfinalboundary noearlier17:38:10Z. Continueifnextjobappears; firstlineSTOPstops. Originalowner no-data/no-net/no-book/no-program/no-PGNconstraints remain; onlypatches/logs/reports/prose committed.

## Job 9 complete (2026-11-18T17:19:59Z)
Report commit428f9d8221d3316729edd0267fdb355c4de45ed0 full-body verified. Default/no-net unchanged r15d and kF Step0 allpass. PartA26 ordered cases: identical789 engine lines; PartB14additional sequential cases after replay: identical1050 lines, including32/33/43-go-token boundaries. Prediction0differences passes. All10raw transcripts remote/full-body verified. Worker ownership/synchronization audit found no changed-path defect; static reasoning not race-detector proof. Supplied second PartA counts include aggregate nodes line (not literally per-move counts); every inclusive count/node/error matches. Auxiliary record auditor unavailable; not run. No standalone datasets, sources, binaries, nets committed. Next poll Job10 every2min through17:49:59Z, fresh final boundary required.

### FOR FABLE AND OPUS
Please clarify PartA count label; otherwise no failed behavioral gate. Job8 W1 correction acknowledged:1000entries/990distinct positions, duplicate S2starts1/14. Awaiting next authorized job.

## Job10 complete (2026-11-18T17:56:47Z)
Report30b12be6fe1d289bbc3c68f0919e41ebf0ff1666 fullyreadbackverified. Step0/perft6positions allpass. C-count/S1 finalhash17964d27:1000W1entries/990distinct,16543291nodes,everybaseline nodes/bestmoveequal;B1/B2/B5/B6all0diff. C-wrong ef782168:200entries/197distinct,4097080nodes,4392B1diffs,unchangedtree. S2first20DISTINCTstarts:20games1370legalplies5612423actualnodes,allfour0diff. Allpredictionrangespass. OptionalB8SEEcounter notimplemented/sourceonly;BoardAPIsharesKingLines,notindependentoccupancyoracle. Finalpatches10c265e/ad4382e.62additionalfilesfullyverified incl51rawparts/fourtranscripts,plus8gate/perftlogs. No bulk-tree, no source/data/net/binarycommits. Publicationledger d16aa38. AwaitJob11 every2min through18:26:47Z, freshfinalcheckrequired.

### FOR FABLE AND OPUS
No confirmedshortcutdefect found under statedinputs. Nativeworkfinished17:36:56;remainingtimewas bounded evidencepublication. Main remainingcoverage: optionalSEEreference,sharedhelperoracle,PCnet/build,threads>1.

## Job 11 complete (2026-11-18T18:30:19Z)
Report db71c69bcb7233c21ce64a5b8da96134c962c483 full-body verified. All Step0/tree/same-uses/control gates pass. C-count2 hash73be1f9d: S1 1000entries/990distinct,16543291nodes; all new S-B1/S-B2/S-B4/S-B7 differences0. S-B7 uses15531178. C-wrong2 b63143c3 has4392S-B1differences, unchanged tree, oldB1normal. S2 all20 Job10 games exactly equal,1370legalplies5612423actualnodes; S-B7 uses5255554, allnew differences0. Independent piece-array references read no cache; grep and source QA committed. All old uses match Job10 per row/per ply. Predictions pass, knowingly gate-informed. All76 additional artifacts verified5,770,031bytes,max100,000; total job below6.1MB. Short preapproval cancellation resolved after destination404 and root no-cancel confirmation; no duplicate write or lost evidence. Publicationledger bc9cb2a. Await Job12 every2min through19:00:19Z, fresh final boundary.

### FOR FABLE AND OPUS
Job10 cache-reference limitation closed for requested counters within sampled workload; no new production finding. Oracle still assumes generated pseudo-legal inputs; S-B7 valid-restoration only. No strength/speed/Threads>1 claim.

## Job 12 complete (2026-11-18T19:07:30Z)
Report2b79831f7603584a6c7d94bafd1f2853ec5b95e1 fully readback verified. Complete86-hunk map ac1b7f9:9changedfiles,1281added/292removed,35pre-counter NONE facets with explicit direct-runtime-gap definition and retained partial/source evidence. Exactdiff122872bytes SHA256c2accc5e40bced1bf635395c663a5355a9a8ea8c709a98ab5357f29594cd5465. Selected largestH28quiet210lines andH18TT131. C-count3hash0139a556: S1nodes16543291, allold8uses preserved, H28uses1376393/H18uses9040060,0diff. S2same20games1370searches5612423actualnodes, H28uses493901/H18uses2638740,0diff. Bothwrongcontrolsfire341487/2063485 with unchangedtree. Allpredictionspass. H18lifecycle/sample-count/ownedprobe andH28laterselector/sharedprimitive gaps remainexplicit. All62rawparts+otherpermitted artifacts78files verified6090510bytes. OptionalS2.summary.txt heldlocal underno-dataset restriction, no retry/repackaging; optionalper-gametable removed fromreport, requestedaggregates published. Jobtotalbelow6.7MB. AwaitJob13every2min through19:37:30Z, freshfinalboundary.

### FOR FABLE AND OPUS
Fullmap prioritized and complete; two gaps now have conditional direct evidence, not proof of everybranch. Heldsummarydoesnotremove rawS2evidence, whichiscomplete. No new production defect orsource repair.

## Job13 verified 2026-11-18T19:36:22Z
Report1a88fa1e5ae2ec5cf9f80af9fa1d43a0470b0342 full-body verified. All71 evidence files (5423353bytes,max100000) verified,55rawparts; no standalone datasets. First200 class-controls: H27 129188/1124811 differ; H25 923057/5483925 differ, strictly partial. Full S1 nodes16543291 H27uses5029379 H25uses23565361,0diff; S2 1370searches actualnodes5612423 H27uses1610870 H25uses6954922,0diff; all10oldcounters unchanged. Four prediction ranges passed; prediction preceded full runs. Updated86hunkmap30NONE, down5; H82 staysNONE. Full build/settings/limits in report; no universal proof or speedclaim.
### FOR FABLE AND OPUS
Job14 initially absent after fresh fetch at19:36:22UTC. Polling every2min to20:06:22UTC (fresh boundary check). S2 node metric: lastcompleted-depth4569803 vsactualsoftnodes5612423, explained in report. Largest remainingNONE H82(66lines), H85(50).

## Job14 report verified 2026-11-18T20:34:51Z
Report716d7be2e95df64c0aa88aaa45242a35fbda5867 full-body verified. All109rawparts complete,131/139 queued evidencefiles10648054bytes;8ancillaryfiles local listed in report/inventory. Native finished19:51:55. Final count5 clean SHA14e0a5935fcde67fae88fb300c4428be2bd915ca4492cd708ddbf9619d766779 after preprediction stale-header build correction; prior evidence retained. K3all200 rowsmatchr15d3351324lastdepthnodes; wrongH82diff2596221/4542519onlyfullmiss. S1/S2/S3H82uses25127532/8190621/22568423,0diff; S3all1000rowsmatch15051338lastdepthnodes. Allpredictionspass. Map29NONE;H82partialdirect,H85NONE because literal31livenessnotshown. L1deterministicfieldsagree;exacttime/npslinesdiffer. Exploratory41distinct,notreplacementcontrol.
### FOR FABLE AND OPUS
Latest Finn instruction supersedes30min: successive jobs for10hours ending2026-11-19T06:16:10Z; wait nextjob up toONEHOUR aftercompletion. CurrentJob15boundary21:34:51UTC, poll2min, STOPstops. Job14report details requested31vsliteralreload41 contradiction. Eightmissing ancillaryfiles are honestlylocal,allnumericraw evidence remote.

## Job15 verified 2026-11-18T20:45:31Z
Reportf41361f57b29a3fb1bcb99b954f05959c613e9e5 full-body verified. LiteralBranchR selected byANYdisagreement rule: Job14L1time/nps-only exactline mismatch. FreshV1originalfirstsearch3pairs rawdiff2/3; reducedsamepositionnooptionsV2fivepairsdiff4/5; generalizedstartposonecommandV3fivepairsdiff4/5. Allremainingfields/bestmoves agree within eachconfiguration; lastdepthnodes7372/16956/9653. All26rawtranscripts+3versions+prose33files91522bytes verified, no missing. Source timingformulas identical; no justifiable semantic enginepatch, no fabricatedrepairproof. Mapunchanged29NONE.
### FOR FABLE AND OPUS
Please clarify deterministic-field oracle rather than exact independent-process time/nps equality; report keepsliteral failure honest. Job16onehourboundary21:45:31UTC; overallend2026-11-19T06:16:10Z. Continue nextassignment whenpresent.

## Job16 verified 2026-11-18T20:57:24Z
Report68a859dcc2eb349ee73da7bd98f41dcf03e1c920 full-body verified. DeclaredPartA L2all60canonicalinfo+bestmovesequal932306lastdepthnodes each; L2cfirst40equal,firstdiff41,r15d932306/kF950331,controlshownlive. Scripts/declaration committedbeforeprediction7b2c2fc...beforeallruns. H85PARTIAL_SESSION,NONE29→28; nextH71(24lines),H12(22). LiteralPartBtiming-onlyrepairbranchreproduced;identicalformulas,nofakeenginepatch orrepairproof. All29queuedfiles414401bytes verifiedplusseparateStep0/scripts/prediction;nomissing.
### FOR FABLE AND OPUS
Clarify deterministic-field exclusion in future ANYdisagreement branchrules toavoidtiming-onlyrepairloop. PartAnewcriterionworksandcontrolpasses. Job17onehourboundary21:57:24UTC; overallend2026-11-19T06:16:10Z.

## Job17 interrupted; partialreport verified22:12:40UTC
Report4aa26eeccaeff10bb1923451d6fb9564b14014fa embeds allsixStep0rawlogs andpartialbuildlog. Step0PASS; count8build stopped90%21:04UTC,nobinary,nocountedruns. Prediction existedbutungraded; H71/H12remainNONE. Reportlateafterinterruption, no claimofproductiveelapsedwork. Toolpublicationcancelled;firstfile404confirmed,rawsnowembeddedinreport. Draftsretainedlocal, noreset/reruns.
## Job18 claimed22:12:55UTC
Claim183655ded5d6c5d699d6a132228354f72b470e01. Literalnextnot-takenrowsH30/H3; excludeJob17takenbutunfinishedH71/H12withoutmarkingcovered. NewestVALIDATEDbasecount5Job14, notunbuiltcount8. Cutoff23:02:55/report23:12:55. Overallend2026-11-19T06:16:10Z.

## Job18 report verified2026-11-18T22:33:07Z, publicrawgap explicit
Report62c1df27560a2eff60406c4f19da56f106d523b6 full-bodyverified. Nativefinished22:18:37. Count9b8d31d23d4675237fd46b98500867ec2169eaee1aad0adf895335212592e6245,wrong9f5a02ceae8a82d3e27b3b13cd9911c40db48b6df1247f7d89b2ee442815efb21. K1/K3allcanonicalfields+old13preserved; controlsH30White39728/72224,H3safe1412026/2916851. S1H30347867,H313078558;S2H3016656,H34722924,zeroall15; allbroadpredictionspass. MapH30/H3partial,NONE26;unfinishedH71/H12stillNONE.
Publication31filesverified1673860bytes plusseparatefullpatches/Step0;67plannedfilesnotverified. AllK1/K2/K3rawcomplete,S1onlyparts1..3; remainingS1/S2local. Safetydenialraw/S1.part004asdataset/no-data conflict,404confirmed; no retry/repackaging. Finnexceptionrequestednotyetreceived. Safe-onlymetadata laterapprovalruntime-shutting-down(notexecuted) stoppedworker;report/inventoriespublishedsafely. Fullrunpublicraw standardnotmet, reporthonestlocal-vsremote. No equivalentroute.
### FOR FABLE AND OPUS
Job19checknow, onehourboundary23:33:07UTC. Overallstop2026-11-19T06:16:10Z. RawbackfillrequiresdirectFinnexception; do not treat jobfileasoverrideoforiginalno-data rule.

## Job19 verified2026-11-18T22:45:26Z
Report5d150fd3dc1b55698d112bcb94650225c8331489 fullbodyverified. H71/H12 rebuilt onvalidatedJob18, notunfinished17. Count10ee0ac8cf22acbf9783cb7de055821e7bdd4ebb59de63959136b3d4ff880f3631;wrong101ab7580cd342109f1f459a3c0a1c21a1ff2165dbbcdaabb9468cc588846dbe76. Allold15/canonicalfieldsretained, all17normalzero. ControlsH71rookonly196600/793153,H12knight217222/3682465. S1H713242450/H1215696603;S2H71963902/H124672211,0diff. PredictionbeforeANYcountedrun/allrangespass. MapH71/H12partial,NONE24;H11relatedSEEcoverageacknowledgedconservativecategoryheld. Native22:37:57. All23SAFEfiles95278bytes verified plusStep0/fullpatches/prediction. PositionrawNOTattemptedwhilepriorauthorizationdenialunresolved,fullpublicrawgapexplicit. No newdenials/errors.
### FOR FABLE AND OPUS
Job20checkingnow,onehourboundary23:45:26UTC. Overallend2026-11-19T06:16:10Z. DirectFinnexceptionstillneededforposition-containingrawpublication; no jobtextoverride.

## Job20 verified2026-11-18T23:01:35Z
Report5b9b39f8564bb3b5ef7f59eb294dda8ec086c300 fullbodyverified. H36/H11 onvalidatedcount10, count11SHA62c238af3da0268855c9b797bf3bee33ad5c5fcfe0a8dacbb694ed2772dc3b08. Allold17 perrow/perply and canonicalfieldsretained;all19normalzero. H36controls1325782/2770783,H11333182/1478385. S1H3612729823/H115415037;S2H364294439/H111776857,0differences. Predictionspass,H11forecast explicitlyinformedpriorH12. MapNONE22; H36consumedindexchecknotallproducerproof,nostackunreached; H11sharesH12reference.26safe files219684bytesverified plusStep0/claim/prediction/report/ledger. Nativecomplete22:53:07.474524UTC. No countedraw or replacementCOUNTS attempted: ownerauthorizationunresolved, externalrecountstandardnotmet.
### FOR FABLE AND OPUS
CheckingJob21now, onehourboundary2026-11-19T00:01:35Z;overallend06:16:10Z. Directownerexceptionstillrequired for blockeddata or replacementrecords. Source patches/aggregateprosecontinuepermitted.

## Job21 verified2026-11-18T23:15:25Z
Report12e8ac475debbc92c158e634b1ce0dcf859bd645 fullbodyverified. H29/H86 onvalidated20, count12c43134cb20db987d000062fdf34a52f702a387c403c2f7892610f1937dc18b1d. Allold19 perrow/perply/canonical preserved, all21normalzero. H29control344889/517908,H86odd2048493/4097080. S1H292168649/H8616543291;S2H29476930/H865612621,0diff. S2H86uses=5612423continuednodes+198stoppedcallsbeforeincrement;fastdirect5606260/fallback6361. K2faultcontrolordinaryonly. MapH29/H86partial,NONE20. Native23:08:46.674355UTC;26safefiles242523bytes verified plusclaim/prediction/report/ledger. Step0sixPASSlocal,but bundlecreate no successmetadata,404confirmed,errornotretained,causeunknown,no retry. Countedraw/COUNTSnotattempted, publicrecountgapexplicit.
### FOR FABLE AND OPUS
CheckingJob22now,onehourboundary2026-11-19T00:15:25Z; overallstop06:16:10Z. Directownerexceptionstillpendingforblockeddata/replacementrecords.
