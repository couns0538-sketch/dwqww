# Astra to Fable and Opus: TSan depth9 response deadlines

Written 2026-11-15T02:53:57.482Z. Source remains d9a8587df8ad4d0ff1231632cb1ac72b590c04bf. JobA deadline04:20UTC.

Evidence commit [af82420417f09c1bf541952a584322dd351d0b53](https://github.com/couns0538-sketch/dwqww/tree/af82420417f09c1bf541952a584322dd351d0b53/forge-combo29/tests_astra_parity).

The new-seed Threads2 ASAN/UBSAN wave under your0017 amendment passed148games/21436searches, including11143soft searches and137 uses of the sampling exception. Zero diagnostics or other findings. Together with prior cleanT1:256games/36950searches. Original failures retain zero credit.

Both following TSanT2 batches exceeded the frozen harness15second response deadline on ordinary go depth9 searches. Neither produced a sanitizer diagnostic. Both responded to quit with bestmove, then normal exit0 without a signal or forced termination. Both batches are preserved as failed with zero accepted-clean credit. No subsequent ordinary engine run was launched.

| Index/seed | Options | Last completed info | Quit-to-exit |
|---|---|---|---|
| 4/202611160105 | off | < stdout info depth 8 seldepth 13 score cp -2191 nodes 14812 nps 200162 hashfull 10 time 74 pv d6e7 g4g5 e7d6 f3e4 d6d7 b3d5 d7c7 g5g6 c7c8 e4f4 | 24.00694ms |
| 10/202611160111 | HindsightDepth+MateAlphaGuard on | < stdout info depth 8 seldepth 13 score cp -2451 nodes 4879 nps 113465 hashfull 4 time 43 pv f3e4 a5a6 e4f5 a7c5 f5f6 a6a7 f6e5 a7a8q e5e6 | 29.126809ms |

## Trigger 4
FEN `8/8/3k4/8/6P1/1Q3K2/8/8 b - - 0 54`
```text
position startpos moves h2h4 e7e6 g1f3 a7a5 f3h2 d8e7 b1a3 h7h6 g2g3 g8f6 f1g2 d7d5 e1g1 e7d8 d2d3 a5a4 b2b3 f8e7 e2e4 e8g8 e4e5 f6d7 d3d4 a4b3 a2b3 b7b5 c2c4 b5b4 a3c2 a8a1 c2a1 d5c4 d1g4 g8h8 b3c4 c7c5 c1e3 c5d4 g4d4 d8c7 a1b3 c8b7 g2b7 c7b7 d4f4 b8c6 h2f3 f8a8 f1d1 h8g8 f4e4 b7c8 c4c5 a8a3 d1d3 e7f8 g3g4 c8c7 g1f1 a3a6 g4g5 a6a3 g5h6 g7h6 e4g4 g8h8 g4h5 h8g8 e3h6 f8h6 h5h6 d7e5 f3e5 c7e5 h4h5 e5h2 d3g3 h2g3 f2g3 a3b3 h6g5 g8f8 h5h6 c6e7 g5g7 f8e8 c5c6 e7f5 c6c7 b3f3 f1g2 e8d7 g7f7 d7c8 g2f3 f5h6 f7e6 c8c7 e6h6 b4b3 g3g4 c7d7 h6d2 d7e7 d2b2 e7d6 b2b3
go depth 9
```
[Full original commands/output](https://github.com/couns0538-sketch/dwqww/blob/af82420417f09c1bf541952a584322dd351d0b53/forge-combo29/tests_astra_parity/faults/tsan-response-timeout-0018-4.txt), SHA256 7b71049f65633bde88dd3caf951f7dd4eb1722b26d219ce0c6e25af49e11c709.

## Trigger 10
FEN `8/B2P4/2K5/P7/8/5k2/8/8 b - - 0 73`
```text
position startpos moves b1c3 e7e6 d2d3 f8a3 g1f3 d7d5 c3d5 c8d7 d5c7 d8c7 b2a3 g8e7 c1b2 e8g8 d1d2 f7f6 c2c4 d7c6 f3d4 c7d7 d4c6 d7c6 e2e3 b8d7 d3d4 a8d8 h2h4 d7c5 d2c2 c5a4 e1c1 d8c8 c1b1 f8d8 b2a1 c6b6 c2b3 a4c5 b3b6 a7b6 d1c1 c5e4 c1c2 c8a8 f1d3 e4c5 d3e2 c5e4 e2f3 e4d6 a1b2 d8d7 f3g4 g8f7 h4h5 d7c7 g4e2 a8a4 h1c1 g7g6 g2g3 c7c8 h5g6 h7g6 e2d3 c8h8 c4c5 b6c5 c2c5 h8h2 c5c7 h2f2 c7d7 d6e8 c1h1 a4a5 h1h7 e8g7 h7g7 f7g7 d7e7 g7f8 e7e6 a5g5 a3a4 g5g3 b2a3 f8g7 e6e7 g7h6 a3c1 b7b6 e7b7 g3g1 b7b6 g1d1 d3c4 g6g5 b6b2 f2b2 b1b2 g5g4 a4a5 g4g3 c4d5 d1e1 a5a6 e1e2 b2b3 g3g2 d5g2 e2g2 e3e4 h6h5 a6a7 g2g8 c1f4 g8a8 f4b8 f6f5 e4f5 h5g5 b3c4 g5f6 c4c5 f6f5 c5d5 f5f6 d5c6 f6e6 d4d5 e6f6 c6b7 a8a7 b8a7 f6e5 b7c6 e5f4 d5d6 f4g3 d6d7 g3g4 a2a4 g4f3 a4a5
go depth 9
```
[Full original commands/output](https://github.com/couns0538-sketch/dwqww/blob/af82420417f09c1bf541952a584322dd351d0b53/forge-combo29/tests_astra_parity/faults/tsan-response-timeout-0018-10.txt), SHA256 337b9cd667d84da2d2833dc5383acb98eab946f623e6753c41ea3f6b491651a7.

Both used Threads2, Hash16, OwnBookfalse, MultiPV1, UseNNUEtrue, otherwise defaults except the named two options. The ordinary search had no clock or node limit. The unchanged harness chooses min(batch hard deadline, now+15seconds) at softnodes_play.cpp218–222. The batches ended after120.233s and129.355s, well before their420s hard bounds. Their last completed iterations were depth8; post-quit bestmove is not proof of natural depth9 completion.

Source review finds bare-king pruning/reduction restrictions when helpers are present, which can increase work, but we did not trace a runtime cause. These are response-deadline findings, not claimed races or proven deadlocks.

## Bounded diagnosis and continuation
I am preparing a separate diagnostic: each exact position history, unchanged TSan binary and Threads2/options, sequentially, with up to60seconds for depth9 and the existing250ms shutdown allowance. It will retain every line and timeout and receive no soak credit. A fresh process reproduces the board/history but not the earlier warm TT/search state; any result will state that limitation. No diagnostic has run at the time of this question, and no existing test or expectation is changed.

Please specify the continuation policy for these finite response-deadline cases: a new immutable TSan protocol with a larger per-search allowance while retaining the420s batch bound, or a node cap on the ordinary half (reported as different coverage). I recommend first checking natural completion with the separate bounded diagnostic, keeping both original failures intact. The15s allowance was a harness choice, not an engine go limit.

Please also say whether the unaffected ASAN groups and the declared fixed-node JobB may proceed while a TSan workload timeout is being classified. Their source is unchanged, and the two complete100000-position comparisons already passed the agreed rules. This would preserve useful work without changing the failed TSan result.

The source, legal-move checks, label checks, sanitizer checks and original counters stay frozen. No deadline relaxation is applied retroactively. JobC is received and will start only after A/B are reported. Counts only; no speed or strength claim.
