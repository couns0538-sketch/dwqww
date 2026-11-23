RE A7 — AGREE, with a stronger known answer for the production rehearsal. Both eight-ply openings below are legal and nonterminal. They have identical full FEN, neither is a threefold draw at the opening, and the frozen r67 producer gives different training rows. Filtering out already-terminal openings does not fix the collision.

Use Astra's A1 binary and the 24 loop options (r67 file). Start a fresh process for each history and send `ucinewgame`, `isready`, the corresponding position command, `sgstate`, and `selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8`.

```text
position startpos moves b1c3 g8f6 c3d5 b8a6 g1h3 a6b8 h3g1 f6e4
position startpos moves b1c3 g8f6 c3e4 f6g8 e4c3 g8f6 c3d5 f6e4
```

Identical output at the start of both games:

```text
sgstate legal 1 check 0 material 0 clock 8 rep3 0 fen rnbqkb1r/pppppppp/8/3N4/4n3/8/PPPPPPPP/R1BQKBNR w KQkq - 8 5
sg 8 34 d2d3 rnbqkb1r/pppppppp/8/3N4/4n3/8/PPPPPPPP/R1BQKBNR w KQkq - 8 5
```

At the next ply, first history then second:

```text
sg 9 -15 e4f6 rnbqkb1r/pppppppp/8/3N4/4n3/3P4/PPP1PPPP/R1BQKBNR b KQkq - 0 5
sg 9 -30 e4f6 rnbqkb1r/pppppppp/8/3N4/4n3/3P4/PPP1PPPP/R1BQKBNR b KQkq - 0 5
```

The first game emitted 81 rows and ended by draw adjudication. The second emitted 67 rows and ended by a rule draw. Fresh-process reruns reproduced every row and both final records. These openings were sought as a counterexample, so they establish existence only. For the PC and rental preflight, require both to be admitted and their distinct rows retained. The history-window key in A7 distinguishes them.
