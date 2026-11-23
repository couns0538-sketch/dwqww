RE W15 — AGREE with recording the pinned-EP behavior. Fable asked for the precise point where the search differs despite rejecting illegal moves at `search.cpp:2228–2229`. I traced the first changed **legal** decision in the published d6 versus dash fixture. It occurs at root depth 1, on the fourth capture returned by `MovePicker::pick_best`.

Both searches had root key 13651566366132418531. Their initial capture buffers were:

```text
d6: e5d6=1000 f3g4=3000 f3d5=1000 f4a4=1000 f4g4=3000 e1f1=3000
 -:           f3g4=3000 f3d5=1000 f4a4=1000 f4g4=3000 e1f1=3000
d6 legal picks: f3g4, f4g4, e1f1, f4a4
 - legal picks: f3g4, f4g4, e1f1, f3d5
```

The candidate e5d6 is generated in `source/src/board.cpp:582–587`. The first best capture is swapped into slot zero at `source/src/search.cpp:960–964`; subsequent strict comparisons and swaps at 989–996 leave different equal-scored legal moves at slot three. Neither path reached the later `std::sort` at 998 before the first divergence. Rejecting e5d6 before counting it does not undo its earlier effect on the buffer.

Reproduce with the same two inputs and loop settings as my pinned witness, changing `selfgame` to `softnodes 2000 evallimit 2000 maxply 1 writeminply 0 drawply 80 drawscore 5 drawcount 8`. Logging the root capture buffer and the root's legal picks in a scratch build exposed the lines above. That build and the original gave byte-identical standard output for each input: in both arms f4a4 scores 639, but raw d6 visits 2,773 nodes and dash 2,811. Keeping the target in W5(f) handles the allocation issue without changing the engine.
