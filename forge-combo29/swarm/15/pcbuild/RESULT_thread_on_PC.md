# The PC build (r15) on the drawn-root / fifty-move thread

Build identity checked before any number was taken:
- patch extracted from `FABLE_TO_swarm_5.md` exactly as fenced: 2319 lines, 11 files, 125,376 bytes,
  **`sha256sum` = d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a**, matching the
  `d6bd72c531f785f4` the file states.
- applied to a separate copy of 6b98f217 with `patch -p1`: all 11 files, no reject, no fuzz.
- built with `-DCMAKE_BUILD_TYPE=Release -DFORGE_MATE_ALPHA_GUARD=1`, g++ 13.3.0.
- **Threads 1** everywhere, Hash 16. No result in this file used Threads > 1.

## 1. The three known-answer rows — ALL NINE NUMBERS MATCH

`pc20.py`, one fresh process per line, every option name taken from the exe's own `uci` list and
stopped on if absent (92 options listed):

```
=== none (0 setoptions) ===
  bench 11 got 312866     want 312866     MATCH
  bench 13 got 862329     want 862329     MATCH
  bench 16 got 3024920    want 3024920    MATCH
  perft 5  got 4865609    want 4865609    MATCH
=== S14 (14 setoptions) ===
  bench 11 got 242796     want 242796     MATCH
  bench 13 got 656517     want 656517     MATCH
  perft 5  got 4865609    want 4865609    MATCH
=== PC20 (20 setoptions) ===
  bench 11 got 278024     want 278024     MATCH
  bench 13 got 587276     want 587276     MATCH
  perft 5  got 4865609    want 4865609    MATCH
OVERALL: ALL ROWS MATCH
```

So the patch reproduces the PC's engine, and my build is the build file 5 describes.

## 2. The four cases of my thread, PC build under PC20, beside the base tree

Both columns from the same script, one fresh process per case, Threads 1.

| case | base tree, S14 | PC r15, PC20 | verdict |
|---|---|---|---|
| 1 mate-in-1, halfmove 99 (control) | `mate 1`, 144 nodes, `a1a8` | `mate 1`, 144 nodes, `a1a8` | **same** — control finds the mate in both |
| 2 mate-in-1, **halfmove 100** | `cp 0`, **0 nodes**, `a1b1` | `mate 1`, **144 nodes**, `a1a8` | **REPAIRED on the PC** |
| 3 threefold-repetition root | `cp 0`, 0 nodes, `a2a3` | `cp 25`, 7799 nodes, `d2d4` | **behaviour changed**: the PC no longer answers a drawn root at 0 nodes |
| 3b same final board as a plain FEN (control) | `cp 14`, 4523 nodes | `cp 22`, 6170 nodes | control searches in both — the base tree's `cp 0` above really was the repetition |
| 4 pawn-move mate (`a7a8=Q#`), **halfmove 100** | `cp 0`, **0 nodes** (move still `a7a8q`) | `mate 1`, 265 nodes, `a7a8q` | **REPAIRED on the PC** |
| 4b same board, halfmove 99 | `mate 1`, 265 nodes | `mate 1`, 265 nodes | same |

Case 4 is worth reading twice: on the base tree the engine plays `a7a8q` at halfmove 100 **with a
score of cp 0 and 0 nodes** — it plays the mating move for the wrong reason, because 0 nodes means
the first legal move, and here the first legal move happens to be the mate. The PC build scores it
`mate 1` and searches 265 nodes. So the base-tree defect is not always a lost half-point; it is
always an unsearched answer.

## 3. Answers to the four questions asked

1. **Does the PC build find the mate at halfmove 99 and 100?** Yes, both: `mate 1` with 144 nodes.
   The base tree finds it at 99 and misses it at 100.
2. **Does it find the pawn-move mate at halfmove 100?** Yes: `mate 1`, 265 nodes, `a7a8q`.
3. **Is the combined patch needed for the PC build?** For this thread, **no**. Every case in it is
   already right on the PC build. The repair is for the base tree only (6b98f217), and my patch's
   audience is a seat still working on the base tree — not the owner's PC.
4. **Does the PC build still print `score mate 0` for an already-checkmated root?** **YES, it does.**
   See below.

## 4. The open question — `mate 0` survives on the PC build, and the score kinds read inverted

```
STALEMATE 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1          -> score cp 0    , 0 nodes, bestmove 0000
CHECKMATE 8/8/8/8/8/6K1/8/Q5k1 b - - 0 1          -> score mate 0  , 0 nodes, bestmove 0000
```

Identical on the base tree under S14. So `score mate 0` at a mated root is **not repaired by the
combined patch** — it is present in both builds. Two things are wrong with that line and both are
worth stating precisely:

- `mate 0` is not a legal UCI mate score: a mate score must be non-zero and signed, and 0 is the
  "no mate" value. A GUI reading `score mate 0` has no defined rendering for it.
- The two terminal cases are reported with **different score kinds for the same situation**. A side
  with no legal moves is lost (checkmate) or drawn (stalemate), and here checkmate prints `mate 0`
  while stalemate prints `cp 0`. If the intent is "the game is over at the root", both should be
  handled the same way; if it is "report the score", neither should be 0.

My earlier 15-F5 reported the same `mate 0` on the base tree; this run shows it is **not** one of
the defects the patch fixes, so it is still an open item for the PC build. I did not read the code
path, so I state the behaviour and not the cause.

## 5. One thing I did NOT settle

Case 3 shows the PC build searching a thrice-repeated root instead of declaring it drawn. File 3 says
the PC "also needs a THIRD occurrence: a second one is searched normally", which a reader could take
to mean a third occurrence *is* declared drawn. On my board the start position occurs three times
(verified with python-chess: 3 occurrences of the same board/turn/castling/ep key) and the PC build
searches it. I have NOT yet tested 2 versus 3 occurrences separately, so I do not claim file 3 is
wrong — I record that a threefold root is searched on the PC build and that this is the next test.
