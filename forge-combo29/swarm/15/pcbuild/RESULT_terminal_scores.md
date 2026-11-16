# Terminal-root scores: what is correct, what each build does, and a RETRACTION of my 15-F13

## 0. Read this first — I was wrong

In 15-F13 I wrote that the PC build's `score mate 0` at a checkmated root was a defect and that the
score kinds across terminal cases "read inverted". **That claim is withdrawn.** Measured against a
real UCI parser, `score mate 0` at a checkmated root is the CORRECT output, and the engine's three
terminal cases are each reported correctly. The evidence is in §2 and §3 and is reproducible with
the committed script `mate0_parser.py`.

I had reasoned from "0 is the no-mate value" instead of testing. python-chess documents the opposite
(`Mate(-0) < Mate(-1) < … < MateGiven`), and its parser turns the engine's line into
`PovScore(Mate(-0), …)` with `.mate() = 0` and `.is_mate() = True` — precisely "the side to move is
mated on the spot", which is what a checkmated root means.

## 1. What correct output is, from the UCI specification's own wording

The April 2006 UCI specification (Rudolf Huber / Stefan-Meyer Kahlen, Shredder Chess; quoted from
the marked-up copy at <https://backscattering.de/chess/uci/>):

On the move format, under **Move format**:

> "The move format is in long algebraic notation.
> A nullmove from the Engine to the GUI should be sent as `0000`."

On the score field, under **info**:

> "`score`
> : `cp` x
> : the score from the engine's point of view in centipawns.
> `mate` y
> : mate in y moves, not plies.
> If the engine is getting mated use negative values for y."

On the answer to every search, under **bestmove**:

> "`bestmove` move 1 [ `ponder` move 2 ]
> the engine has stopped searching and found the move move best in this position. […]
> this command must always be sent if the engine stops searching […], so for every `go` command a
> `bestmove` command is needed!"

**One honest gap, stated plainly:** the specification does not enumerate terminal positions at all.
It never says what a checkmated, stalemated or drawn root should report. So the expectations below
are derived from those two definitions, not quoted from a rule that does not exist:

| terminal case | score kind I would expect | bestmove I would expect | why, from the quoted wording |
|---|---|---|---|
| **checkmated root** (side to move is mated) | `score mate 0` — `.mate() == 0`, is_mate true | `0000` | "If the engine is getting mated use negative values for y": the side to move is mated, distance 0. `mate 0` with the side to move mated is the `0` case; `0000` is the specified null move, and there is no move to give. |
| **stalemated root** | `score cp 0` | `0000` | Stalemate is a draw, not a mate, so no `mate` score applies; "the score from the engine's point of view in centipawns" for a drawn position is 0. Again no legal move, so `0000`. |
| **drawn by insufficient material** | `score cp 0` | a real move (NOT `0000`) | Same reasoning for the score. But unlike the two above, the side to move DOES have legal moves, and `0000` is defined as a null move — so returning `0000` here would be wrong. |

## 2. Current output, all three cases, both builds — one table

From `mate0_parser_all.txt`, script `mate0_parser.py`, **Threads 1**, Hash 16, a fresh process per
case, `go depth 8`. "python-chess reads it as" is the engine's exact `info` line put through
python-chess's own `_parse_uci_info`.

| case | build / settings | engine score | bestmove | python-chess reads it as | matches §1? |
|---|---|---|---|---|---|
| **checkmated root** `8/8/8/8/8/6K1/8/Q5k1 b` | base / S14 | `mate 0` | `0000` | `PovScore(Mate(-0))`, `mate()=0`, `is_mate()=True`, as cp **-100000** | **YES** |
| checkmated root | PC r15 / PC20 | `mate 0` | `0000` | same | **YES** |
| **stalemated root** `7k/5Q2/6K1/8/8/8/8/8 b` | base / S14 | `cp 0` | `0000` | `PovScore(Cp(0))`, `is_mate()=False`, as cp 0 | **YES** |
| stalemated root | PC r15 / PC20 | `cp 0` | `0000` | same | **YES** |
| **insufficient material, K v K** `8/8/4k3/8/8/4K3/8/8 w` | base / S14 | `cp 0` | `e3d2` | `PovScore(Cp(0))`, as cp 0 | **YES** |
| insufficient material, K v K | PC r15 / PC20 | `cp 0` | `e3d2` | same | **YES** |
| **insufficient material, K v K** `8/8/4k3/8/8/4K3/5N2/8 w` | base / S14 | `cp 0` | `f2d1` | `PovScore(Cp(0))`, as cp 0 | **YES** |
| insufficient material, KN v K | PC r15 / PC20 | `cp 0` | `f2d1` | same | **YES** |

**All eight cells are correct.** There is no inversion: checkmate reports a mate score (as it must),
the two drawn cases report `cp 0` (as they must), and the drawn cases correctly return a real move
while the terminal ones correctly return `0000`. Both builds agree because none of this is what the
patch touches.

**Correction to a claim I made earlier in this file.** I first wrote that the K v K and KN v K rows
were *searched* because they print 8 info lines and a real bestmove. That was wrong, and it was
wrong for the reason this whole exercise is about: I had not measured the node count. Measured with
`repcount2.py` (which records nodes), an insufficient-material root is **short-circuited at 0 nodes**
on BOTH builds:

```
K v K   8/8/4k3/8/8/4K3/8/8 w        cp 0   0 nodes   e3d2    SHORT-CIRCUITED
KN v K  8/8/4k3/8/8/4K3/5N2/8 w      cp 0   0 nodes   f2d1    SHORT-CIRCUITED
KB v K  8/8/4k3/8/8/4K3/5B2/8 w      cp 0   0 nodes   f2e1    SHORT-CIRCUITED
```

which matches file 3 exactly ("only a root with insufficient material is still answered at once").
The lesson is the one seat 19 and the coordinator both pushed: an `info` line and a plausible
bestmove are not evidence a search happened; `nodes` is.

## 3. Does a GUI show `mate 0` as a loss or as a zero-distance mate?

Measured, not guessed, using the parser every seat in this swarm already uses:

```
score mate 0  ->  PovScore(Mate(-0), BLACK)
                  .mate() = 0        .is_mate() = True
                  .score(mate_score=100000) = -100000
                  Mate(0) < Mate(-1)  ->  True
```

and python-chess's own documented ordering is

```
Mate(-0) < Mate(-1) < Cp(-50) < Cp(200) < Mate(4) < Mate(1) < MateGiven
```

So a parser built on this library reads the engine's line as **the worst score that exists** — below
being mated in one — which is exactly right for a side that is already mated. There is no
zero-distance-win ambiguity in this parser: `Mate(0)` compares equal to `MateGiven` only after
negation, i.e. `-Mate(0) = MateGiven` holds because *the opponent* has delivered mate. The
documented warning in python-chess about `Mate(0)` conflating "we lost" with "we won" applies to the
sign convention at the call site, not to what this engine emits.

I cannot report what a specific graphical GUI (Arena, Cute Chess, Banksia, Nibbler, …) renders for
`score mate 0`, because none is installed on this machine and I will not assert behaviour I did not
observe. What I can say is what a library-based consumer does, and that is correct. If the owner
needs the GUI-level answer, it needs a machine with the GUI on it.

## 4. Corrections this forces in my own file

- **15-F13 is WITHDRAWN.** Its first half ("`mate 0` at a checkmated root is a defect") is wrong:
  §2 shows it is the correct output. Its second half ("the score kinds read inverted") is also
  wrong: checkmate→mate score and stalemate→cp 0 is exactly the correct distinction, not an
  inversion.
- **15-F5 keeps only its second half.** The real defect in 15-F5 was never the score — it was that a
  terminal root walks the depth ladder to 64 (`go nodes`/`go movetime`) and prints 64 info lines with
  `nodes 0` instead of answering at once. That part stands and is measured.
- What remains genuinely open from file 3's claim is the **repetition count**: my threefold root is
  searched on the PC build (§5 of `RESULT_thread_on_PC.md`, and `repcount_all.txt`). Whether that is
  correct depends on whether the PC is meant to declare a *third* occurrence drawn — the test is
  below and is the next job.

## 5. Method notes, so this can be checked

```bash
cd forge-combo29/swarm/15/pcbuild
python3 mate0_parser.py ~/builds/pc/forge  --regime PC20   # PC build
python3 mate0_parser.py ~/builds/rel/forge --regime S14    # base tree
```

The first version of this script crashed (`UciProtocol()` needs a running asyncio loop); the
committed version calls `chess.engine._parse_uci_info` directly, which is the same parser without
the protocol wrapper. The crash is recorded because a script that fails is not evidence.
