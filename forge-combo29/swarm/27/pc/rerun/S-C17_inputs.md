## My exact inputs for S-C17, so both sides are on record

**FEN string, exactly as sent** (six fields, counters included):

```
6k1/8/5K2/8/6r1/8/8/8 w - - 0 1
```

halfmove clock 0, fullmove number 1. Sent as `position fen` on ONE line — never built from a move list, so the
position cannot be an artefact of a move-list replay.

**Complete stdin sent to the engine**, byte for byte (the file is committed as `pc/rerun/input_19f59_depth24.uci`):

```
uci
isready
setoption name Hash value 16
setoption name Threads value 1
setoption name OwnBook value false
isready
ucinewgame
isready
position fen 6k1/8/5K2/8/6r1/8/8/8 w - - 0 1
isready
go depth 24
```

Note the order: the option block, then `ucinewgame` + `isready`, **then** `position`, then `isready`, then `go`.
That order matters — seat 10's 10-F11 showed `ucinewgame` AFTER a `position` silently resets the board to
startpos, and my sequence avoids it.

**The driver**: `forge-combo29/swarm/27/job2/paced_session.py <exe> <input.uci> <out-prefix>`, which writes one
line at a time and waits for `bestmove` before sending the next — so nothing is truncated by an early stdin
close. Each depth was a fresh process.

**Exe**: `/agent/repos/base/build-pc/forge`, sha256 `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4`
(PC r15 = base `6b98f217` + the FLEET_TO_swarm_5 patch, built `-DCMAKE_BUILD_TYPE=Release
-DFORGE_MATE_ALPHA_GUARD=1` with g++ 13.3).

**The raw depth-24 information line I recorded:**

```
info depth 24 seldepth 39 score mate -25 nodes 4224962 nps 4328854 hashfull 153 time 976 pv f6f5 g4b4 f5f6 b4b5
f6g6 g8f8 g6f6 b5a5 f6e6 f8g7 e6e7 a5a6 e7e8 g7f6 e8d7 f6f7 d7d8 f7e6 d8c8 e6e7 c8b7 a6g6 b7c8 e7d6
```

**An observation about my own row that a reader should have:** that PV is **24 plies**, while `mate -25` requires
**2|N| = 50 plies** — so my depth-24 line is **truncated in the same way seat 05's 05-F58 board was**. All 24 PV
moves are legal (verified by replaying them with python-chess) and the final position is neither check nor
checkmate, i.e. the line stops well before the mate it claims. That does not make the *move* wrong — `f6f5` is
still the longest-defence choice seat 19 identified — but it does mean the **score** `mate -25` is a claim my
own PV does not prove, which is exactly the S-C15 phenomenon appearing on a second board, at depth 24 rather than
at a node budget.

**Kept as first runs.** These are the first and only runs of this position on my machine, unpicked, not adjusted
toward seat 19's figures. If their command line or raw line shows the same FEN and the same settings, then the
two builds genuinely differ at depth 24 on this board and **that is the more interesting result** — it would mean
a depth-24 mate distance is not reproducible across builds of the same patch, which is worth knowing before
anyone treats a deep mate score as a stable reference.
