Part A: source reading only, no run used for these answers. Base 6b98f217, src/search.cpp unless noted; PC workload scope Threads1/MultiPV1.

A1. At qsearch entry 1419-1421 and search entry 1561-1563, node_limit_specified_ makes the test run on EVERY node before ++local_nodes_; should_stop_with 1273-1275 stops when the current total is >=N, so Threads1 cannot count past N: the next node attempt is rejected, the current iteration unwinds as aborted, or the completed-iteration check at2556 stops if its last admitted node exactly reaches N (zero nodes is handled at2273-2277).
A2. Node-budget abort sets stopped_by_nodes_ at1274; 2439-2452 then skips unfinished-root publication, retaining bestmove/PV/score from the last completed iteration recorded at2454-2461 and emitted at2543, with bestmove printed by uci.cpp562-572; if no iteration completed, there is no trained label, only the first legal fallback at2640 (empty PV/default score).
A3. Clock or external stop does not set stopped_by_nodes_; 2444-2450 may replace bestmove/PV with an unfinished iteration's nonempty PV only when its head differs, retain the last completed score, and emit that mixed result tagged with current depth; if that condition is false it retains the previous complete tuple (UCI bestmove from returned result).
A4. Softnodes sets target N and saturated hard cap4N at2174-2180; after a COMPLETED iteration2553-2555 tests total_nodes()+extra_nodes_>=N, while the same per-node stop enforces4N; no node-based forecast refuses to start an iteration, and TmFinishIteration is clock-only (time_managed_/finish_sampling2394-2399,2557,2613-2624), so a node-only iteration can start and later be discarded at4N.

## Part B: no new high-confidence PC-path defect established

The permitted paths were reviewed rather than filling the report with known behavior or tunable extremes. No repair is recommended. The useful result is a directly tested node-stop contract, including a positive control that catches a real overrun even when the displayed finished-iteration label is unchanged.

### Build/settings and prediction commits
All binaries use embedded AL1 s198 (sha256 a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638), GNU14.2.0, libstdc++.so.6.0.33, glibc2.41, CMake4.4.5, Release/x86-64-v4/default feature switches.
- Base source6b98f217: binary2f545495d4e3e2b59af49fbb18212ec2ed8ae297d801e58647cfea37cd18e785.
- PCr15: exact patch d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a from FABLE_TO_swarm_5.md, zero-fuzz apply to isolated base copy, plus -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1. Binary9279d02c2ea8c42875ec83a55399aeb588b72a3ae13e8067969be2cee8219306.
- Base diagnostic twin7a71a58b04e8c30cd1b151bd67f1cabf6ae459a199ebe09bf550abf7f02b5d82; PC diagnostic twin4875aaf2985293618fc2800b95f301b3682cc6b7c9fcb00d4fb69fed96fd7f2d. Twins only print returned SearchInfo at Searcher::search exit; no search change.
- S14 = Threads1 Hash16 OwnBookfalse, LmrQuietBase93 LmrQuietDivisor205 LmrNoisyBase13 LmrNoisyDivisor333 LmrHistoryDivisor5643 NullMoveBase5 LmpBase8 HistoryPruneMultiplier2220 HistoryBonusQuadratic24 HistoryBonusLinear54 HistoryBonusMax2212 SingularDepth6 IirDepth2 NonPawnCorrectiontrue.
- PC20 = S14 plus CuckooReptrue HistRework2 TtPruneV2true CorrHistV2true MateAlphaGuardtrue.
- Every process validates all option names against its own uci listing; unknown option/invalid value/ERROR is fatal. Fresh processes for each test. Every raw process block starts with its label, full executable SHA, and options.

Predictions were committed BEFORE tests and left unchanged:
K0 6a21ed784517441eeed9f58ca119f5cee7a74e5f; KPC84bfbb2b4bc2e0737df993e86fe840028d2e4aaf; K1 0aab31cc371d04b9d07cbbbc966659fba1c68ef1; K2 af7bb3374fc16b0e6b5e71b18b7bdba4009ede3b.
Files are under dot/job2/expectation_K*.txt.

### Gate facts
Base/S14 bench11=242796, bench13=656517. PCr15/PC20 bench11=278024, bench13=587276. Both diagnostic twins passed their corresponding configured gates and default bench11=312866, bench13=862329, perft5=4865609. The already published labeled raw gates are dot/job2/K0_base_gate_raw.txt and KPC_gate_raw.txt. No mismatch or refused option.

### K1: cold normal-node and soft-node matrix
Source sites personally reopened: search.cpp1419-1421/1561-1563 (pre-count test),1273-1275 (budget reason),2439-2461 (finished tuple preservation),2553-2556 (post-iteration stop),2630-2644 (final total), and UCI554-572.
For all eight base bench FENs, tested go softnodes2000, go nodes50000 and go nodes250000 on base/S14 and PCr15/PC20, each with plain and diagnostic binary:48 paired cases/96 searches.
All ordinary non-time search fields matched between each twin pair. Every hard-node case consumed exactly its50000 or250000 budget. Soft cases stayed within2000..8000, but NONE reached8000. Returned depth/score/PV agreed with the last completed UCI line; bestmove agreed with its head and was checked legal by applying it and perft1. These passes did not exercise a soft hard-cap stop, so K2 was added rather than claiming that coverage.

### K2: hard-cap hit and detector control
Fixture: first200 non-comment FENs in base tests_r3fu_12/positions.txt, opened before use; whole fixture SHA256b5a07228d1254afc1a849bd24e11098f75a8dc4cbd2349d347ab35f566e2512d. Its header identifies seed90241290297069, walk-depth4, opening-plies8-12.
Diagnostic fresh-process soft2000 scan:200 base/S14 positions, no hard-cap hit;20 PCr15/PC20 positions through first hit at zero-based index19. All220 totals were within2000..8000 and all returned depth/score/PV matched their last complete line.
The PC hit is:
```
rn1qk2r/pp1bbppn/3pp3/2pP2Pp/2P1P3/1PN2P1P/P3N3/R1BQKB1R w kq - 1 15
```
PCr15/PC20, go softnodes2000:
```
info depth 6 seldepth 10 score cp 148 nodes 1683 ... pv f3f4 a7a6 f1g2 e8g8 c1e3 b7b5
info string softnodes nodes 8000
info string DOT_RESULT nodes 8000 depth 6 score 148 pv f3f4 a7a6 f1g2 e8g8 c1e3 b7b5
bestmove f3f4
```
The dots above abbreviate time/NPS/hashfull only; full labeled raw transcript is preserved separately. Replaying the unmodified PC binary matched all non-time fields of its diagnostic twin.
Deliberately changing the diagnostic PC copy's node stop comparison from >= to > produced8001 consumed nodes while preserving the same depth6, cp148, PV and bestmove. Detector rejected8001>8000. This is a PLANTED FAULT, not a discovered bug and not a repair. Its labeled raw output and exact executable hash are preserved in K2_replay_fault.raw.txt; clean controls are K2_replay_plain.raw.txt and K2_replay_count.raw.txt.

### Dedup and reading attribution
Personally reopened every line supporting A1-A4 and the mechanisms reported above. An internal reader additionally examined base position/reset/option paths, r15 CuckooRep and upcoming-repetition, and known emergency/abort changes; the sentence “no further high-confidence candidate was returned” rests on that review, not a claim that I independently proved every line correct. No finding sentence here relies only on its unverified line citation.
Excluded known clock-abort mixing, terminal-root softnodes-marker omission, exhausted-clock emergency, multithread overshoot outside Threads1, and job1's closed zero-coefficient issue. No speculative behavior repair just to reach three findings.

## What I did not do
No new defect repair, no engine-source repository edits, no PR, no owner's PC/net access, no strength/speed claim, no clock6+.06 timing run, no sanitizer or warm-game coverage. K1/K2 are cold fixed-input tests, not reproduction of sol3's warm synthetic768-net workload. No claim that matching completed info nodes measures all work: the8000/8001 control proves it does not.

## What I am not sure about
There may be undiscovered PC-path defects; this bounded review found none I can substantiate. The full cold matrix does not establish behavior on unseen nets, warm histories, or asynchronous clock stops.

## Interruption and publication status
Claim timestamp11:02:30UTC; native work completed by11:10:38UTC. At approximately11:12UTC, an attempt to prepare/publish a bulk artifact tree stalled in a tool call. The wait later returned “aborted by user after4431.1s”; recovery clock is12:26:46UTC. No branch ref update to that prospective tree was issued and no report existed remotely at recovery. CLI push had also failed because this environment has no GitHub username credential; connected GitHub text writes still work. This report is being published promptly on recovery, rather than holding it behind bulk artifacts.
All evidence remains local; full bulk publication is NOT yet claimed. Existing gates/predictions are remote; essential cap-hit raw transcripts are being published next. No native experiment ran beyond the minute50 cutoff. After report publication I will check FABLE_TO_dot_3.md every2 minutes for30 minutes, then follow successive jobs under the owner's latest instruction.


## Publication recovery completed 2026-11-18 12:33:54 UTC
Nineteen additional evidence files were published in bounded calls and full-body readback verified at branch head6aca6fc39dad5cf604e2e8cdf7ad002572408abd: summaries, harnesses, diagnostic/fault text patches, both diagnostic gate transcripts, and six labeled raw-search extracts. Those extracts retain build SHA/options/label and every search info/bestmove line plus position/go commands, with source raw-file hashes; they expressly omit repeated UCI handshakes/setup. The essential cap-hit plain/diagnostic/planted transcripts were already published in full. The98 repetitive-handshake bulk raw files remain preserved locally and are not falsely claimed as full remote files. No experiment or claimed result changed during recovery.
