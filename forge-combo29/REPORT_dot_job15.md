# Dot Job 15

## 1. Branch R, literally selected
Job15's declared rule says ANY disagreement in Job14 S1/S2/S3/L1 selects R. Job14 report section6 records L1 exact final-info lines differing37/60, firstsearch1, solely time/nps; deterministic fields and bestmoves agreed. S1/S2/S3 had no normal-counter/tree disagreement. Therefore R applies literally. I did not silently substitute BranchN or pretend exact final-info equality held.
Result: the time/nps-only difference reproduces, but both engines implement the same live elapsed-time semantics. No semantic engine defect or justified repair was found. The requested repaired-engine proof is NOT supplied as a spurious success.

## 2. Fresh reproduction and shortest scripts found
All executions use unchanged original binaries: r15d SHA256bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6; kF SHA256340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea. Both prior GCC14.2.0/CMake4.4.5/libstdc++.so.6.0.33/glibc2.41 Release x86-64-v4 builds. Every run freshprocess, one thread. All26 complete raw transcripts retained. Every script variant attempted is supplied as a .uci.txt text input with synchronization comments, not an executable.

V1_original_first_search.uci.txt retains exact Job14 PC20/net768 setup and firstW1FEN, depth9, and removes all later59 searches/transitions. Threepairs: raw final-info differs2/3; allsix deterministic final-info fields and bestmoves agree,7372 last-completed-depth nodes each. One pair happens to have equal milliseconds and NPS: the mismatch is timing-dependent, not guaranteed every launch.

V2_nooptions_same_position.uci.txt removes option/net/handshake setup, preserving first board and depth9. It has two search-driving commands:
```text
position fen r1bq1rk1/1p1nbppp/p3pn2/3pN3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 b - - 0 11
go depth 9
```
Wait for bestmove before quit. Fivepairs: raw final-info differs4/5, all deterministic fields/bestmoves equal5/5,16956 last-completed-depth nodes each. Removing options changes the exact tree versus V1; this is a smaller demonstration of the SAME timing-only difference class, not a claim to preserve the7372-node trace.

V3_nooptions_startpos.uci.txt additionally removes position, allowing the engine's initial startposition:
```text
go depth 9
```
Wait for bestmove before quit. Fivepairs: raw final-info differs4/5; all deterministic fields/bestmoves equal5/5,9653 last-completed-depth nodes each. This one search command is the smallest command-count demonstration found: removing it produces no search/final-info. It changes the board relative toV1/V2 and is explicitly a generalized demonstration, not the identical original position. No claim of shortest byte sequence or universally reproducible unequal timing. No other script version was tried.

## 3. Patch(es) and SHA256
No engine repair patch proposed. No engine source changed, no repaired binary built. The existing emitted measurements satisfy the identical formula in both versions. Replacing time/NPS with constants, fake node-derived timing, or copied reference timings would falsify telemetry, not fix a demonstrated engine error. Script/prose evidence is not labeled an engine repair. Patch SHA256: not applicable.

## 4. Known answers and controls
The requested BranchR fresh first-disagreement reproduction completed. BranchN Step0/K1/K3 and new-counter controls were not run because BranchN was not selected. Repair K1/S1 row-by-row proof was not run because there is no justified repair. Prior Job14 gates remain prior evidence, not new Job15 runs.
Repeating unchanged binaries is a liveness check for the observation: raw time/NPS may vary while depth,seldepth,score,nodes,hashfull,PV,bestmove remain equal within each configuration. Raw exact equality and deterministic-field equality are reported separately; excluding only time/nps is a proposed appropriate comparison, not retroactive fulfillment of the literal all-fields requirement.

## 5. Prediction graded
Not applicable: BranchR has no prescribed prediction. No prediction invented after seeing results.

## 6. Cause, source lines and why no repair proof
Opened unchanged source:
- kF src/search.cpp3217–3218 and r15d2715–2716 compute elapsed as duration_cast<milliseconds>(steady_clock::now()-start_).count(). This is real monotonic elapsed time, not civil UTC or deterministic node progress.
- kF3220–3221 and r15d2718–2719 select reported nodes and compute elapsed>0 ? nodes*1000/elapsed :0.
- kF3257–3262 and r15d2755–2760 print NPS,hashfull,time with the same implementation. The cited kF3215–3270 and r15d2713–2768 emission-code ranges are textually identical.
- kF3118–3121 and r15d2624–2627 use the same timing-origin fallback. Plain fixed-depth search without a supplied clock origin uses its own steady_clock::now().
Thus there is no differing r15d semantic line to identify as a counterpart defect. Independent process samples need not consume equal real elapsed milliseconds. Scheduling/cache/load and actual implementation speed can contribute; these tiny samples do not separate those effects or establish speed regression.

Original Job14 firstpair:7372nodes at4ms gives1843000NPS, at5ms gives1474400NPS, exactly both emitted values. Current V1 pair1:7372nodes at6ms gives1228666NPS, at8ms gives921500NPS. Strict byte equality incorrectly treats live telemetry as a deterministic search answer. Both outputs can be correct simultaneously.

A bounded test-oracle clarification is to preserve all raw lines, verify each time/NPS arithmetic relation, and compare every remaining field plus bestmove exactly. That is not permission to ignore clock-sensitive search behavior in timed or multithreaded workloads. No comparator change was retroactively applied to claim the original literal test passed.

### Raw reproduction extracts
Job15 independent first-search reproduction: three fresh-process pairs.
Same exact PC20/net768 initialization as Job14 L1, same pre-search isready, first W1 FEN, depth9; no ucinewgame. No source modifications.
Only time and nps excluded in canonical comparison; hashfull retained.
FEN: r1bq1rk1/1p1nbppp/p3pn2/3pN3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 b - - 0 11
Pair1: exact final info equal=False; canonical final info equal=True; bestmove equal=True.
r15d info depth 9 seldepth 19 score cp -74 nodes 7372 nps 1228666 hashfull 1 time 6 pv d8a5 d1e1 g7g6 e5g4 f6g4 e2g4 d7f6 g4e6 e7d8 e6c8
r15d bestmove d8a5
kF info depth 9 seldepth 19 score cp -74 nodes 7372 nps 921500 hashfull 1 time 8 pv d8a5 d1e1 g7g6 e5g4 f6g4 e2g4 d7f6 g4e6 e7d8 e6c8
kF bestmove d8a5
Pair2: exact final info equal=True; canonical final info equal=True; bestmove equal=True.
r15d info depth 9 seldepth 19 score cp -74 nodes 7372 nps 1843000 hashfull 1 time 4 pv d8a5 d1e1 g7g6 e5g4 f6g4 e2g4 d7f6 g4e6 e7d8 e6c8
r15d bestmove d8a5
kF info depth 9 seldepth 19 score cp -74 nodes 7372 nps 1843000 hashfull 1 time 4 pv d8a5 d1e1 g7g6 e5g4 f6g4 e2g4 d7f6 g4e6 e7d8 e6c8
kF bestmove d8a5
Pair3: exact final info equal=False; canonical final info equal=True; bestmove equal=True.
r15d info depth 9 seldepth 19 score cp -74 nodes 7372 nps 1228666 hashfull 1 time 6 pv d8a5 d1e1 g7g6 e5g4 f6g4 e2g4 d7f6 g4e6 e7d8 e6c8
r15d bestmove d8a5
kF info depth 9 seldepth 19 score cp -74 nodes 7372 nps 1843000 hashfull 1 time 4 pv d8a5 d1e1 g7g6 e5g4 f6g4 e2g4 d7f6 g4e6 e7d8 e6c8
kF bestmove d8a5
Across all six fresh processes: canonical final info equal=True; bestmove equal=True.
Every node count above is the last completed-depth info nodes, not an independent total. Raw transcripts include executable SHA256, options, active net checksum, all commands and stdout. These observations cannot prove all positions or build/platform equivalence.

Fresh unchanged builds; five repetitions each version. Node count from last completed-depth info.
V2_nooptions_same_position: exact final-info differences 4/5; deterministic final-info equal 5/5; bestmoves equal 5/5; nodes r15d [16956, 16956, 16956, 16956, 16956], kF [16956, 16956, 16956, 16956, 16956].
First differing pair, repeat2:
info depth 9 seldepth 19 score cp -7 nodes 16956 nps 1211142 hashfull 4 time 14 pv d7e5 f4e5 b7b5 b2b3 c8b7 a2a4 h7h6 a4b5 a6b5 a1a8
info depth 9 seldepth 19 score cp -7 nodes 16956 nps 1413000 hashfull 4 time 12 pv d7e5 f4e5 b7b5 b2b3 c8b7 a2a4 h7h6 a4b5 a6b5 a1a8
V3_nooptions_startpos: exact final-info differences 4/5; deterministic final-info equal 5/5; bestmoves equal 5/5; nodes r15d [9653, 9653, 9653, 9653, 9653], kF [9653, 9653, 9653, 9653, 9653].
First differing pair, repeat1:
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 402208 hashfull 2 time 24 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 1072555 hashfull 2 time 9 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5

## 7. Map
BranchN map extension not performed. Job14 map remains29NONE, including H85 because literal31 liveness was not shown. No new engine-hunk coverage claim made from timing reproduction.

## Facts
Claim2026-11-18T20:35:56Z; minute50 cutoff21:25:56, reportdeadline21:35:56. All fresh runs completed well before cutoff. The branch decision follows the exact statedANY-disagreement rule. Both source arithmetic and fresh transcripts support timing-only variability. All variants attempted and all successes/coincidental equalities are disclosed, not cherry-picked.

## Suspicions
No new semantic engine bug established. Strict raw telemetry equality is the immediate explanation of this branch trigger, rather than a mismatched search result. Hardware/load/scheduler shares of elapsed variation are not identified.

## What I did not do
No bogus repair, no timing falsification, no repaired-build K1/S1 proof, no BranchN counters, no clocked or multithread tests, no speed/Elo claim. No standalone positions/game dataset or binary/net committed. Auxiliary skill auditor remains unavailable; no claim it ran. No request to extend the original job's scope by treating a normalized test as its literal requirement.

## What I am not sure about
Unseen boards/options, other platforms/compilers/nets, clock-managed searches and thread interactions remain outside these observations. Tiny integer-millisecond measurements can coincide, so no script guarantees inequality on every run. V2/V3 simplify the mismatch class but change settings/board as explicitly stated.

### What this check cannot see
Positions and sessions these scripts do not reach; the PC's net, compiler and build; more than one search thread.

## Publication
All33 evidence files fully read back by20:44:23 UTC:91522bytes,max9025. All26 complete raw transcripts, all3attemptedscriptversions and source/reproduction/QA prose published. Ledger publication_verified.json.txt verified. No missing intended evidence, no errors/denials. Derived local JSON remains local; no standalone positions/game dataset. Jobtotalunder200KB and eachfileunder100KB. Local stale checkout status below preserves evidence rather than implying remote engine source changes.

## FOR FABLE AND OPUS
The literal BranchR ends without a proposed engine repair because both timing formulas are identical and correct for their sampled durations. Please specify deterministic-field comparison if that is the intended oracle and direct the next uncovered-row work. Continuing nextjob wait under Finn's latest ONEHOUR rule, capped by2026-11-19T06:16:10Z; no need to wait out remaining budget when no valid repair is warranted.

## Last command before report commit
```text
git status --short; ls -R forge-combo29/dot/job15
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job10.md
?? forge-combo29/REPORT_dot_job11.md
?? forge-combo29/REPORT_dot_job12.md
?? forge-combo29/REPORT_dot_job13.md
?? forge-combo29/REPORT_dot_job14.md
?? forge-combo29/REPORT_dot_job15.md
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
forge-combo29/dot/job15:
V1_original_first_search.uci.txt
V2_nooptions_same_position.repeat1.kf.raw.txt
V2_nooptions_same_position.repeat1.r15d.raw.txt
V2_nooptions_same_position.repeat2.kf.raw.txt
V2_nooptions_same_position.repeat2.r15d.raw.txt
V2_nooptions_same_position.repeat3.kf.raw.txt
V2_nooptions_same_position.repeat3.r15d.raw.txt
V2_nooptions_same_position.repeat4.kf.raw.txt
V2_nooptions_same_position.repeat4.r15d.raw.txt
V2_nooptions_same_position.repeat5.kf.raw.txt
V2_nooptions_same_position.repeat5.r15d.raw.txt
V2_nooptions_same_position.uci.txt
V3_nooptions_startpos.repeat1.kf.raw.txt
V3_nooptions_startpos.repeat1.r15d.raw.txt
V3_nooptions_startpos.repeat2.kf.raw.txt
V3_nooptions_startpos.repeat2.r15d.raw.txt
V3_nooptions_startpos.repeat3.kf.raw.txt
V3_nooptions_startpos.repeat3.r15d.raw.txt
V3_nooptions_startpos.repeat4.kf.raw.txt
V3_nooptions_startpos.repeat4.r15d.raw.txt
V3_nooptions_startpos.repeat5.kf.raw.txt
V3_nooptions_startpos.repeat5.r15d.raw.txt
V3_nooptions_startpos.uci.txt
first_search_pair1_kf.raw.txt
first_search_pair1_r15d.raw.txt
first_search_pair2_kf.raw.txt
first_search_pair2_r15d.raw.txt
first_search_pair3_kf.raw.txt
first_search_pair3_r15d.raw.txt
first_search_reproduction.txt
independent_QA.txt
minimize_results.local.json
minimize_summary.txt
publication_verified.json.txt
timing_source_audit.txt
```
