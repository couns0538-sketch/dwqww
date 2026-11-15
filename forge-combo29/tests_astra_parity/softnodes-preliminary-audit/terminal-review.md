# Preliminary paired-game terminal review

Read-only inspection of the first and final TRIGGER/CHECK rows in `/workspace/work/parity-run/logs/softnodes-step1-preliminary-pair.stdout.txt`. No engine, test, source edit, Git action or experiment-state write was performed by this reviewer. This review checks the two terminal classifications and shared opening only; the parent separately audits all search labels and binary pins.

Both games begin from exactly the same eight plies:

`b2b4 f7f6 c1b2 g8h6 h2h4 h6g8 b2d4 b7b6`

Both first TRIGGER rows give:

`rnbqkbnr/p1ppp1pp/1p3p2/8/1P1B3P/8/P1PPPPP1/RN1QKBNR w KQkq - 0 5`

## Usual limit: checkmate confirmed

Final pre-move FEN at ply 139:

`8/8/8/2p5/p7/1r6/8/K1k5 b - - 11 70`

Returned move: `b3a3`. The expected resulting FEN is:

`8/8/8/2p5/p7/r7/8/K1k5 w - - 12 71`

White has only its king on a1. The rook on a3 checks along the otherwise empty a-file. The king's only adjacent board squares are a2, b1 and b2: a2 stays on the rook ray, and Black's king on c1 controls b1 and b2. White has no piece to interpose or capture the rook. This is checkmate, matching the summary's one usual-game mate and the final `score mate 1`.

## Soft limit: insufficient material confirmed

Final pre-move FEN at ply 94:

`6k1/8/5B2/8/8/6K1/6b1/8 w - - 0 48`

Returned move: `g3g2`. The expected resulting FEN is:

`6k1/8/5B2/8/8/8/6K1/8 b - - 0 48`

White's king legally captures the black bishop on g2. Black's king on g8 does not protect that square. The remaining material is White king g2 and bishop f6 against Black king g8, which cannot produce checkmate. The insufficient-material termination therefore matches the summary. The final recorded soft search also reports its exact line at 3,492 nodes and X=3,492; the broader label audit is outside this review.

No opening or terminal-classification discrepancy found. Static reasoning confirms these two local transitions; this does not claim a separate replay of every earlier move.

Inspected stdout SHA256: `ca9d2c309eaa3a26e368428b005afb0be8fe99e33bae2ef69ffb964640e97e88`.
