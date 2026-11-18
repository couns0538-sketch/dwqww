PC build on P, depth 1 through 20. Each result was reconstructed from raw UCI traffic.

| Arm | Settings | First mate depth | Score | Nodes there | D20 move / score / nodes |
| --- | --- | --- | --- | --- | --- |
| S14 | S14 | 16 | mate 2 | 240516 | g3g6 / mate 2 / 241,262 |
| PC20 | PC20 | not by 20 | — | — | f6h5 / cp 916 / 1,052,250 |
| B1 | PC20 + HistRework 0 | 13 | mate 2 | 75864 | g3g6 / mate 2 / 77,195 |
| B2 | PC20 + CorrHistV2 false | not by 20 | — | — | f6h5 / cp 865 / 930,407 |
| B3 | S14 + CuckooRep true | 15 | mate 2 | 138407 | g3g6 / mate 2 / 141,265 |
| B4 | S14 + HistRework 2 | not by 20 | — | — | f6h5 / cp 836 / 774,832 |
| B5 | S14 + TtPruneV2 true | 16 | mate 2 | 333499 | g3g6 / mate 2 / 334,278 |
| B6 | S14 + CorrHistV2 true | 15 | mate 2 | 135969 | g3g6 / mate 2 / 137,079 |
| B7 | S14 + MateAlphaGuard true | 16 | mate 2 | 240516 | g3g6 / mate 2 / 241,262 |

Both unchanged ladders matched job 3 on all 20 depths.
