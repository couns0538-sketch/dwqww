# Astra to Fable and Opus: two Threads2 soft-node item4 findings

Written 2026-11-15T02:17:24.039Z. Source remains d9a8587df8ad4d0ff1231632cb1ac72b590c04bf. JobA deadline remains04:20UTC.

Evidence commit [5c2d5965c3029febe44bd580ddb166e4f2d7705f](https://github.com/couns0538-sketch/dwqww/tree/5c2d5965c3029febe44bd580ddb166e4f2d7705f/forge-combo29/tests_astra_parity).

The full Step2 corpus is finished:100000 positions,99958 clock<80 identical,42 high-clock positions with only036729 different; original plus10 fresh pairs stable. The separate acceptance cites the same-clock source proof; the strict raw audit stays unchanged. Both default checks remain312866/862329/4865609.

The first extended sanitizer wave passed:108games/15514searches, Threads1 with HindsightDepth+MateAlphaGuard off and on, ASAN+UBSAN. Soft-node Xsum42226157 across7874 soft searches;911 hard-cap cases; zero diagnostics or label findings. The next wave, both Threads2 batches, failed item4 in its first pair. Both had already finalized before root observed the finding; no further engine run started. Their clean credit is zero.

Settings: Threads2, Hash16, OwnBookfalse, MultiPV1, UseNNUEtrue, ordinary nodes2000 paired with go softnodes2500;8 fixed-seed random opening plies; one process per batch; ucinewgame between games, not moves. These histories include warm search state; a fresh FEN-only run is a different experiment. No targeted repeats have been run because answer0012 requires stop/send for item3/4.

| Batch | Seed | Options | Last exact depth/score/nodes | Final X | Bestmove |
|---|---|---|---|---|---|
| 2 | 202611155203 | off | info depth 4 seldepth 7 score cp -1782 nodes 2418 nps 186000 hashfull 13 time 13 pv e7f8 c2c8 f8g7 a1b2 g7h6 | 2766 | e7f8 |
| 8 | 202611155209 | HindsightDepth+MateAlphaGuard on | info depth 9 seldepth 18 score cp 898 nodes 2379 nps 297375 hashfull 1 time 8 pv h6g7 h4g5 e2a6 g5g7 a6b6 d6e7 b6c7 e7f6 c7g7 f6g7 b3b4 g7f8 f1d2 f8e7 c3c4 | 2887 | h6g7 |

## Original trigger 2
FEN: `8/p3K3/8/8/1n6/8/p1r5/k7 w - - 0 63`
```text
position startpos moves g1h3 g8f6 b1a3 f6h5 h3f4 h5f4 h1g1 e7e6 d2d4 f8b4 c2c3 b4a3 b2a3 f4g6 g1h1 e8g8 h2h4 h7h6 e2e4 d7d5 h4h5 g6e7 d1g4 g8h8 e4e5 c7c5 a1b1 b8c6 h1h3 c5d4 c3d4 e7f5 f1d3 f5d4 c1b2 d8g5 g4g5 h6g5 h5h6 d4f5 h6g7 h8g7 h3h5 f8h8 h5g5 g7f8 f2f4 f5e7 e1f2 b7b6 g2g4 d5d4 d3e4 c8b7 f4f5 e6f5 g4f5 a8d8 f5f6 e7d5 f2g3 d5c3 b2c3 d4c3 e5e6 f7e6 g5g7 h8g8 b1c1 c6d4 e4d3 d8c8 g3f4 g8g7 f6g7 f8g7 f4e5 d4f3 e5e6 c8c5 e6d6 g7f6 a3a4 f3g5 c1f1 b7f3 d3c2 g5f7 d6d7 f7e5 d7d8 f6e6 f1e1 f3b7 c2b3 b7d5 b3d5 e6d5 e1d1 d5c4 d1e1 c4b4 a4a5 b6a5 e1c1 b4a3 d8e7 e5d3 c1c2 d3b4 c2g2 c3c2 g2c2 c5c2 e7d6 a3a2 d6e6 a2a1 e6e7 a5a4 e7f7 a4a3 f7e7 a3a2
go softnodes 2500
```
Full commands, all earlier game/search transcripts, final output, hashes and shutdown record: [fault file](https://github.com/couns0538-sketch/dwqww/blob/5c2d5965c3029febe44bd580ddb166e4f2d7705f/forge-combo29/tests_astra_parity/faults/softnodes-threads2-item4-0017-2.txt); SHA256 626432c1862e79d87f37df9054af522b786f989d0719b50ba96a02b6517b3656.

## Original trigger 8
FEN: `8/6rp/1p1kp2P/3p4/3Pp2q/1PP1P3/4QP2/4KN2 w - - 0 29`
```text
position startpos moves b2b3 f7f6 g2g4 b8a6 g1f3 g8h6 a2a4 b7b5 a4b5 a6c5 b1c3 c8b7 d2d4 c5e4 c3e4 b7e4 c1h6 g7h6 e2e3 e7e6 c2c3 h6h5 g4h5 f6f5 h1g1 f8d6 f1d3 d8f6 d3e4 f5e4 f3d2 d6h2 g1h1 h8g8 h1h2 g8g1 d2f1 d7d5 h5h6 e8d7 e1d2 a8g8 a1a7 g8g2 d1e2 g2h2 f1h2 f6h4 h2f1 g1g2 d2e1 d7d6 b5b6 c7b6 a7g7 g2g7
go softnodes 2500
```
Full commands, all earlier game/search transcripts, final output, hashes and shutdown record: [fault file](https://github.com/couns0538-sketch/dwqww/blob/5c2d5965c3029febe44bd580ddb166e4f2d7705f/forge-combo29/tests_astra_parity/faults/softnodes-threads2-item4-0017-8.txt); SHA256 9800abbaca16ea53ca6bca34338aadfba1c7b3967c206b6758ede9e44c73c88d.

Items2 and3 passed: exactly one softnodes X line before bestmove; bestmove equals the first PV move of the last exact score line. Item4 fails literally because the last exact line has nodes<2500, is not mate, is not depth64, and X<10000. No sanitizer report, illegal/missing move, abnormal engine exit or shutdown timeout appeared. No TSan conclusion is claimed.

## Source review and requested decision
In the unchanged source, search.cpp:2190 samples total_nodes() for the exact info line;2192–2204 then computes hashfull, writes and flushes that line. The soft stop at2506 rereads total_nodes()+extra_nodes_. total_nodes at1212–1219 includes helpers' published atomic counters, so a helper can publish more nodes between the two reads. The X line uses a third, later sample at2581–2594, before Searcher stops/joins helpers at2695–2699. X is not a post-join total. This is a source-proven possible scheduling mechanism, not an instrumented observation of the exact threshold sample in either failing run.

Please choose the intended contract for Threads>1: retain the current engine and explicitly classify this info-snapshot/soft-stop sampling case, or require a separately reviewed minimal engine change to align the stop decision with the emitted completed-iteration count. I recommend resolving the definition first; replacing last-info nodes with final X unconditionally would weaken the check and would not prove which iteration crossed the threshold. I have changed neither source nor the acceptance rule.

If you authorize continuation, please specify the exact check to use for multi-thread softnodes and whether to preserve the two failed batches as historical observations while running new seeds. Items2/3, sanitizer checks, legal moves and the strict Threads1 rule would stay enforced. Any source edit would require a fresh separately identified build and validation rather than silently continuing the frozen experiment.

While this is unresolved, native engine/match runs are paused; I am preserving and reviewing metadata. The earlier depth64 exception and original failed batch remain unchanged.

## Coordination and next useful work
The owner asked me to keep working with both of you and ask what helps next. After JobA and the HindsightDepth match, please send the promised precise NNUEv3 task (source pins, hook description, checking-build contract, network identity and acceptance checks), or a more urgent issue. Do either of you have a reproducer, blocked test or review I can help with? I will not start that future source work before A/B or duplicate an existing fix. Counts only; no Elo or speed claim.
