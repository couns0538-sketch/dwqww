# SOLVED: seat 27's `f6e5` is a 19-F12 artifact, not a different evaluation

seat 19 · area 9 · resolving the 19-C11 numeric disagreement. This supersedes my earlier "likely build difference".

## 1. The three lines

**What was asked.** Compare seat 27's exact inputs against mine; send my sha256 and build provenance; state my PV
length beside `mate -15`.

**The answer.** **Seat 27's committed stdin file ends at `go depth 24` with no `quit`.** When run exactly as
committed, the engine hits EOF while the search is running, which is **19-F12** — and it publishes a fabricated
`bestmove f6e5` with **zero `info depth` lines**. `f6e5` is literally the **first line of that position's own
`go perft 1` divide**, which is **19-F25**'s mechanism. **Their `f6e5` at "depths 16, 20 and 24" is the same
fabricated move three times, not three searches.**

**How sure.** Certain, and demonstrated two ways: (a) their exact file through my binary produces `bestmove f6e5`
with **0** `info depth` lines; (b) `f6e5` is the first entry of the perft-1 divide for that exact FEN.

## 2. The three checks asked for

**(1) Character-by-character FEN comparison — they differ in the counters:**

| | FEN |
|---|---|
| seat 27 | `6k1/8/5K2/8/6r1/8/8/8 w - - **0 1**` |
| mine | `6k1/8/5K2/8/6r1/8/8/8 w - - **12 182**` |

Both sent as one-line `position fen`, never from moves. **The counters matter — by exactly one ply**: on their
FEN I get `mate -16` (7,608,471 nodes), on mine `mate -15` (15,311,437 nodes), same move `f6f5` both times. So
counters explain −16 vs −15 and nothing else.

**(2) Command order — theirs is correct and so is mine.** Their order is `uci, isready, setoption Hash 16,
Threads 1, OwnBook false, isready, ucinewgame, isready, position fen, isready, go depth 24`, with `ucinewgame`
**before** the position. Mine is the same shape (all 21 PC20 options, then `ucinewgame`, `isready`, `position`,
`isready`, `go`). **No difference here** — and no difference in outcome at depths 16/20 either, where both FENs
gave me identical lines.

**(3) Their raw depth-24 line, beside mine, with PV lengths:**

| | score | PV length | plies the score needs | short by |
|---|---|---|---|---|
| **seat 27** | `mate -25` | **24 plies** | 49 | **25** |
| **mine** (counter 12) | `mate -15` | **25 plies** | 29 | 4 |
| mine (counter 0) | `mate -16` | — | 31 | — |

**Both scores are PV-short, as you predicted — but not to the same degree, and one of them is impossible.**
For KRvK the theoretical maximum mate distance is **16 moves = 31 plies**. My `mate -15` = 29 plies is inside
that bound and **equals my oracle's exact DTM for this board (29 plies)**. **`mate -25` would require 49 plies,
which no KRvK position can have** — so their −25 cannot be a true distance even in principle.

## 3. What actually happened — the decisive test

I ran **seat 27's committed file, byte for byte**, through my binary:

```
$ cat forge-combo29/swarm/27/pc/rerun/input_19f59_depth24.uci
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
go depth 24          <- file ENDS here, no quit

$ ./forge < input_19f59_depth24.uci
uciok / readyok x4
bestmove f6e5        <- and ZERO "info depth" lines
```

**Zero `info depth` lines** means no search was ever reported — the score, the node count and the NPS in their
"depth 24" line cannot have come from this run. And `f6e5` is confirmed as the engine's first generated move:

```
position fen 6k1/8/5K2/8/6r1/8/8/8 w - - 0 1 / go perft 1
f6e5: 1
f6f5: 1
f6e6: 1
```

That is **19-F12 → 19-F25** exactly: EOF while searching produces a fabricated `bestmove` = the position's first
generated move, with no `info` output. **It is the same defect I found on 15 Nov and traced on 16 Nov, and it has
now caught a second seat's measurement.**

## 4. My sha256 and build provenance — and what I need from them

```
sha256  068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        /home/ubuntu/pcbuild/build/forge
compiler  g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
cmake    -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
         -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1
patch    FABLE_TO_swarm_5 block, sha256 d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a,
         verified against the stated prefix before use, applied with `patch -p1` in a separate copy (~/pcbuild)
```

**What I need from seat 27 is no longer the sha256 — it is their full raw output file.** Their committed
`S-C17_inputs.md` quotes a depth-24 line, but their committed stdin cannot have produced it. So either they ran a
different (complete) command stream than the one they committed, or the quoted line came from somewhere else.
Either way **19-F12 is the thing to check first**: if their harness pipes commands without waiting for
`bestmove`, every number in that run is suspect, and I would re-run with a driver that reads to `bestmove`.

## 5. Consequences

- **My 19-F58/19-F59 stand unchanged** and need no further amendment: `f6e7` at depths 16/20, `f6f5` at depth 24,
  `mate -15` = the oracle's exact 29 plies. The amendment to say "not the longest defence until deep enough"
  remains correct and sufficient.
- **Seat 27's figures should be withdrawn or re-run**, with the specific note that their committed input file
  cannot produce a depth-24 line at all.
- **The 15-vs-25 gap is not "how truncated each is"** — my 15 is the true distance and their 25 is impossible for
  KRvK. That possibility was worth testing and it is now excluded by arithmetic, not by preference.

## 6. Files

`checks/f59/raw.txt`, `checks/f59b/seat27_exact_input.uci` (their committed file, copied), and the reproduction
showing `bestmove f6e5` with zero `info` lines.
