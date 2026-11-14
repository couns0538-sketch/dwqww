# Finalization readiness review — 17:13:55 UTC snapshot

Cloud-only, read-only review of the live state/report and exact source objects. Scheduled end remains **2026-11-14 19:11:32 UTC**. The state and report snapshots, plus exact read commands/output, are retained beside this note. The reviewed soak HEAD was `03afad5500de0776006dc8f24656a812d90b8820`. These are snapshot findings, not final match totals or claims about private work underway.

## Failed checks: preserve as failures

- **Part 2C is complete but its required equality gate FAILED.** 100,000 eligible comparisons include 99,958 roots below halfmove80 and42 higher-clock roots. Eight required low-clock cases fail and reproduce in10/10 additional fresh pairs each: eight node-count differences, three score differences, four PV differences, no bestmove difference. The31 high-clock differences are separate observations. Faults084–091 and the counterfactual investigation preserve the failed expectation; attribution does not turn it into a pass.
- **Four unchanged t16 fixture comparisons FAILED:** options/clamp in release and ASan, due to stale advertised-option expectations. Each repeats10/10; all40 engine invocations exit normally without another output difference or sanitizer diagnostic. This is a fixture mismatch, not an engine crash or permission to rewrite expectations.
- **Baseline endgame misses are real recorded failures of that test criterion:** unchanged lock has298/2,400 mate-score misses; merged has0/2,400. The55 original-t12 KRK criterion flags overlap those misses and identify slower winning moves beyond depth14, not55 lost mates. All4,800 moves were legal under Forge's checker; the KRK oracle found no loss of forced mate or reported-bound violation. KQK/KBBK have no independent mate oracle. Do not summarize this whole comparison as zero faults or91 distinct engine bugs: the91 numbered files comprise82 endgame groups, eight equality cases and one fixture record.

## Incomplete attempts: later coverage does not erase them

- Original full ASan KRK40×10 attempt:440-second timeout, no completed coverage.
- Isolated full ASan KRK40×10 retry:435-second timeout, no completed coverage. The two later completed40×5 invocations supply400 T2 trials on the same40 roots plus200 T1 reference checks; together with the initial reduced retry, completed KRK sanitizer executions are300 T1 and440 T2. Both full-invocation timeouts remain incomplete.
- TSan E5 timed out without SUMMARY. It contributes zero accepted games/searches; same-condition5r1 completed7games/1,026searches. The original timeout is not a proven crash, race or deadlock.
- Partial2A/2C units retain raw evidence and were resumed. Completed aggregate coverage does not make the interrupted attempts successful. Partial cleanup diagnostics remain outside completed-unit denominators.

The current test matrix has six nonzero records: four fixture diffs and two KRK timeouts. The TSan E5 timeout is separately represented in the runtime/attempt evidence. No additional engine assertion failure or sanitizer finding was found hidden in these reviewed records. The matched Part2 runtime audit reports no ASan/UBSan diagnostics or TSan warning blocks in the retained completed batches, with E5 explicitly classified as a timeout.

## Not done or not claimed at this snapshot

| Item | Accepted evidence now | Remaining distinction |
| --- | --- | --- |
| Default fastchess mode | Complete4,000games/2,000pairs; candidate W-L-D1094–1177–1729; audited0 crash/illegal/disconnect/stall/abort events or markers | Counts only, no strength conclusion. |
| ContHist4PlyRead mode | 2,400 completed games; candidate673–666–1,061; batch7 active and excluded | Still running at snapshot; do not import its partial games. |
| NonPawnCorrection mode | No completed counts recorded | Not run/completed yet at snapshot. |
| LmrDeeperShallower mode | No completed counts recorded | Not run/completed yet at snapshot. |
| Part4 | Four uninstrumented searches, one instrumented search, one independently assessed known KRK root | Private tracer work and optional broader sampled audit have no accepted results in this snapshot. No universal mate-bound proof or production fix is claimed. |
| Eight-hour final reporting/publication | Current live report exists | Final totals, audit timestamp, deadline status and final documentation publication still need closure. |

Part2D/E/F/G and the split KRK coverage are recorded complete; this does not make Part2C pass. D has1,131games/131,115searches; E56games/8,297searches; F1,102ASan games/126,532searches plus14enabled-optionTSan games/1,886searches. The first D batch lacks a full per-search trace (194games/27,831searches self-reported with driver checks); later trace coverage cannot retroactively supply it. Legal-move checks use Forge's Board implementation, and self-play score checks are range checks rather than independent evaluation/mate proofs. Prepared optional D9/D10 and E8 repeats were not run; do not label them failed or silently count them. A recorded checkpoint interval of12min35.713sec exceeded the requested10-minute cadence and remains a procedural limitation.

## Source audit result

No src/include changes exist between pinned merged source `f27b1971e459581ad4c85b7015f6af83bbfd4af6` and reviewed HEAD, or between HEAD and the working tree. Git diff exit0 in both cases; working tree clean at the initial read. Exact Git tree IDs match:

- `forge-combo29/src`: `9c4cb86ab9bea8c401c3b5dca64f2c63161e936a`.
- `forge-combo29/include`: `b011f3d213a8973c57b85d6a9cafca71aab754d9`.

All three required input commits are ancestors of f27b197. Static comparison to the inputs confirms t12's multiworker bare-king definition at search.cpp1258–1265; its razoring/RFP/null guards at1270/1276/1281 remain inside t23's mate_moves==0 and clock+depth<100 outer guard1267–1268. Shallow pruning1393–1394 ANDs the t23 conditions with !bare_king_mode. LMR1480–1482 uses the **child** halfmove clock plus new_depth and also requires !bare_king_mode. The t23 near50 TT move/PV/cutoff guards remain at1069–1078 and1217–1230. No r3 candidate changes are present.

ContHist4PlyRead, NonPawnCorrection and LmrDeeperShallower still initialize false at search.cpp77–79 and advertise defaultfalse at uci.cpp189–191. Their conditional reads remain at633/967/976,884/901 and1496/1501. The three SHA256 anchors remain:

| File | SHA256 |
| --- | --- |
| src/search.cpp | `2b14b62cd675b047478e70b738932ce4c2c699239b3c0de4ec43551464dc8819` |
| src/uci.cpp | `724a4c9c07a4102d38c39fc292f66ba0c850a9c162c090148734da86acd4fb40` |
| include/forge/search.hpp | `9b88252588398bbe83164d6d9e0200522e919ed813a8cb4b04a8c57eee921600` |

The final integration documentation proposal needs no new factual correction: it already preserves the four/eight failed distinctions, both fullKRKtimeouts and splitcoverage, and uses the live/final soak link for later dynamic results. It stays unchanged at `/workspace/work/all-run/review-t1-t8/integration-final-doc/INTEGRATION_ALL.ready.md`, SHA256 `5b12ce8214bf4505c83145f9768df7ad1b2a18ef67fce7b36a853db1ebc6fe6b`.

## Publication audit plan — parent to run after final work settles

1. Close or explicitly retain the active attempt as incomplete; update the final report only from accepted completed counts. Reconcile all four match modes and pair bins separately; preserve original timeouts, failed comparisons and unrun work.
2. Record the final exact source/report refs and audit timestamp. Re-run read-only pinned-to-HEAD and HEAD-to-worktree src/include diffs, tree IDs and the three SHA256 checks. These commands do not run the engine:

```sh
git rev-parse HEAD
git diff --exit-code f27b1971e459581ad4c85b7015f6af83bbfd4af6 HEAD -- forge-combo29/src forge-combo29/include
git diff --exit-code HEAD -- forge-combo29/src forge-combo29/include
git rev-parse HEAD:forge-combo29/src HEAD:forge-combo29/include
sha256sum forge-combo29/src/search.cpp forge-combo29/src/uci.cpp forge-combo29/include/forge/search.hpp
```

3. In the integration checkout, verify the proposed publication changes only `forge-combo29/INTEGRATION_ALL.md` relative to e04556dd; no later logs or candidate source should be copied there. After the documentation commit, repeat the pinned source diff and compare `git diff --name-status e04556ddc3a430b2e751159b0d46111ef56c8b89 HEAD` to that single permitted documentation path.
4. Publish the soak evidence before or with the integration document. Verify its absolute GitHub soak-branch links resolve to the published final report/evidence. Keep the final24 r3 static review distinct from runtime acceptance; historical21/23 placeholder records are already marked superseded.

No engine workloads, source/state/production edits, refs or pushes were performed for this review. Only scratch snapshots and notes were written. A helper delegation attempt was refused by the collaboration thread limit; the source audit was completed directly instead.
