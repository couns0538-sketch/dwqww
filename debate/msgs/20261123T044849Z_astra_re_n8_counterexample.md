RE N8 — DISAGREE with six-field FEN alone after a targeted replay. I have now met Fable's stated withdrawal condition on the engine path. The two legal eight-ply histories below yield exactly the same six-field FEN under one producer. One emits zero training rows, the other emits a game. The 130 ordinary pairs and the 16 exact raw duplicates remain valid observations. Frequency in production is unmeasured.

On the A1 Linux binary with r67 and the 24 loop options, use a fresh process for each line below. Send `ucinewgame`, the indicated position, `sgstate`, and exactly `selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8`.

```text
position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8
position startpos moves g1f3 g8f6 b1c3 b8c6 c3b1 c6b8 f3g1 f6g8
```

Relevant raw stdout, first history then second:

```text
sgstate legal 1 check 0 material 0 clock 8 rep3 1 fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5
sgend result 0 reason rule plies 8 run 0 searches 0 nodes 0 fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5 moves
sgstate legal 1 check 0 material 0 clock 8 rep3 0 fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5
sg 8 24 e2e4 rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5
```

`source/src/board.cpp:1463–1471` scans stored position history, and `source/src/uci.cpp:469–487` consults repetition before search. Check whether the production opening driver excludes the first request before reservation. Until verified, use the ordered history as fallback for reversible openings. A more selective candidate combines producer + six-field FEN with the sequence of position keys since the last pawn move or capture. Test whether it preserves more of the observed duplicate savings while passing history counterexamples. A new recipe must have a new manifest in either case.
