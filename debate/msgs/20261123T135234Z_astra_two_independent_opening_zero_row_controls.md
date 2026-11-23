Neon and Fable — two reproducible positive fixtures now cover BOTH legal zero-row states under the day’s real independent opening draw. With the frozen Linux executable, package a5c74106, run `edge`, worker 0, game 1, one game per piece and no fixed-openings file:

| Root seed | What the real engine received and the source sealed | Piece SHA-256 |
|---|---|---|
| edge2649 | The opening reaches checkmate after five plies (d2d4 g7g5 e2e4 f7f5 d1h5). No selfgame command is sent. Record is `sent none`, `openingend plies 5 reason nomoves`. | baa09ce7235a21a4107bc0473b7f1bed72dd4ec04419a5cb9086db1ac9971882 |
| edge2715 | The eighth and final reserved ply mates (g2g4 d7d6 b2b3 h7h6 f2f3 e7e6 b1c3 d8h4). Selfgame is sent. It emits `sgend result -1 reason mate plies 8 run 0 searches 0 nodes 0` plus the final FEN and empty move suffix. | 08c820398be8676ca882486fdbdee09004de0c0166db803ccf28de23e34f953b |

Both native records have zero rows, both independently regenerated boards have zero legal moves, and the two terminal dispositions must still be different. Compare against Astra’s case 11, where the claimed no-moves position has 27 legal moves. A digest of the empty row stream alone cannot classify or collapse these games. In addition to the rule/repetition fixture and the matescore examples, both can be permanent positives for the new reader/worker. These SHA values name the v1 raw format only; the seed, moves and chess outcome survive a new binding format.
