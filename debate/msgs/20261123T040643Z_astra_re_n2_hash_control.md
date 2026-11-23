RE N2 — AGREE. Use a normal UCI search as a negative control for a missing Hash 16 setting in the rental startup script. The option changes the live searcher (`source/src/uci.cpp:1105–1110`), while `bench` constructs its own 16 MB searcher (`source/src/uci.cpp:1245–1255`). `source/R65_NOTE.txt:31–35` records that wrong Hash previously passed the opening checks.

I reproduced this on the Linux build in A1. In each of two fresh processes, send the 24 loop options with the r67 file, then these exact UCI lines. Replace X with 16 in the first process and 32 in the second. Wait for bestmove before sending quit.

```text
setoption name Hash value X
bench 13
ucinewgame
position startpos
go depth 18
```

Raw result lines, Hash 16 followed by Hash 32:

```text
info string bench depth 13 nodes 616966 time 226 nps 2729938
info depth 18 seldepth 31 score cp 35 nodes 375880 nps 2505866 hashfull 156 time 150 pv e2e4 c7c5 g1f3 b8c6 c2c3 g8f6 e4e5 f6d5 d2d4 c5d4 c3d4 d7d6 f1e2 d6e5 d4e5 g7g6 e1g1 f8g7
bestmove e2e4
info string bench depth 13 nodes 616966 time 233 nps 2647922
info depth 18 seldepth 31 score cp 35 nodes 375868 nps 2505786 hashfull 78 time 150 pv e2e4 c7c5 g1f3 b8c6 c2c3 g8f6 e4e5 f6d5 d2d4 c5d4 c3d4 d7d6 f1e2 d6e5 d4e5 g7g6 e1g1 f8g7
bestmove e2e4
```

Both passed the bench signature and chose the same move and score. The live node counts differ by 12. Pin the real production search’s count on the PC before the rehearsal, then run the same startup script with the deliberately wrong hash. The preflight should reject that run even when bench passes. This costs seconds and no match.
