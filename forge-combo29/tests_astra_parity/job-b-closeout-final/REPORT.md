# Job B fixed-node match closure

1400 credited games (700 color-reversed pairs). HindsightDepth on first: W-L-D 389-350-661. Five pair counts (LL, LD, DD_or_WL, DW, WW): 28, 154, 302, 183, 33.

Stopped after the last recorded native batch at 2026-11-15T05:00:27.265Z. Declaration: 2026-11-15T03:06:50.313Z; declared deadline: 2026-11-15T05:06:50.313Z; closure evidence: 2026-11-15T05:01:43.995Z. The sum of native batch process wall times was 1743.238 seconds. Declaration-to-last-native-stop elapsed time was 6816.952 seconds. These are actual recorded durations; two continuous hours of play are not claimed.

Closure reason: Remaining declared budget cannot admit another full bounded batch. The last safe launch threshold was 2026-11-15T04:59:00.313Z; each launch required at least470 seconds remaining.

Conditions: same binary; HindsightDepth true versus false; MateAlphaGuard false; Threads1, Hash16, OwnBook false; 50000 nodes per move; remaining options at advertised defaults. Official fastchess, UHO random opening order, seed202611150011; 4 concurrent games, 100-game batches; each opening twice with reversed colors; recover enabled; no adjudication.

Source: d9a8587df8ad4d0ff1231632cb1ac72b590c04bf. Binary SHA256: df76cddaea8a37dae7f8d1a5178700e0168aad8c463764ed6870d9c4fce2dc56. Fastchess source: 3d7a4db2493fc85a05ef010fd7e13a3884667aa2; binary SHA256: f8f1706b6b4906d524dd0ac0547deb9ec2b6b10b4e32d7bde66914ddee0ebd4f. Book SHA256: 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a.

| Configuration | Illegal games / events | Disconnect games | Stalls | Time forfeits | Nonzero process exits | Crash signals | Cleanup signals |
|---|---|---|---|---|---|---|---|
| hindsight-on | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| hindsight-off | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Global engine stop at closure: inactive. Root phase at verification: Job B: HindsightDepth fixed-node match. Closure does not clear that stop.
Separate ASan shutdown finding0020 paused native launches; its state at closure is unresolved. Finding UTC: 2026-11-15T04:11:30.796Z; fault evidence: /workspace/work/dwqww-parity/forge-combo29/tests_astra_parity/faults/asan-shutdown-0020.txt, SHA256 f205dfeaa23737f6ba4d36a1f5354639d24e5400d36429084b427bdde2eb882b. It remains in the sanitizer record; match fault counts above come from match events.

Aborted games: 0; raw crash markers: 0; unattributed abort/game records: 0; unattributed process records: 0. Failed/incomplete batches: 0; excluded raw finished games: 0. Disconnects and process deaths remain separate observations.

Target: 6000 games; completed 1400; shortfall 4600. Optional250000-node leg: not run in this declared experiment. No result from that leg is claimed.

Job A was incomplete and its sanitizer work pending at this match's declaration, as explicitly authorized by0018. This closure changes only JobB status; it does not close sanitizer work or rewrite its findings.

Verified 14 receipts and 28 immutable packages against source artifacts and reconstructed chunks. Package reconstruction bytes: 1136012039. Full raw transcripts, PGNs, events, audits and faults remain linked by the closure index.

Counts only. No Elo, strength or speed conclusion is drawn.
