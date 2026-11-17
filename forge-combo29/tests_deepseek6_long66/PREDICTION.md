# deepseek6 long 66 — PREDICTION (written before the first eval comparison)

Item (file 16, long 66): **EVALUATION SYMMETRY.** The engine's static evaluation (`eval`, using the final number
from the side to move's view) for each of the **353 G positions** and its **colour-flipped mirror**; then the same
for the **left-right mirror** (only positions without castling rights). Control: one position against itself must
be equal. Any difference gets its FEN and the code term with file and line.

Model: DeepSeek V4.1 Flash 1017, chat 1794862262. Time: `stamps.txt`, first line is the claim.

## Fixed now

- Build: plain 6b98f217 release, `/tmp/ds6/build-release/forge`, sha256 `7c4e1aee…33622`. No search is run — this
  item is about the static evaluation, so the pins that matter are that the binary is the one I have used all
  session (its four pins were exact at the start of this chat).
- **What `eval` prints** (measured now, not assumed): `info string eval hce 49 nnue 83 total 132 incheck 1` — three
  numbers plus an in-check flag. **The number I compare is `total`**, and the item says "from the side to move's
  view", so the engine's own sign convention is what I test; I do not re-sign it.
- **Colour flip**: `python-chess` `Board.mirror()` — colours swapped, side to move swapped, castling rights and
  the en-passant square mirrored. Every one of the 353 G positions.
- **Left-right flip**: `transform(chess.flip_horizontal)`, **only** positions with **no castling rights**
  (`board.castling_rights == 0`); a horizontal flip breaks castling legality, so including those would test
  python-chess, not the engine.
- **Control**: position 1 compared with itself must be equal (a trivial check that the harness reads the number
  right).

## Predictions, each with the range that kills it

**P1 — the control is equal.** Kill range: the self-comparison differing → the harness is broken and nothing else
in the item means anything.

**P2 — the colour flip is symmetric for at least 340 of 353 positions (96 %).** A correct engine with a
colour-symmetric evaluation should be exact everywhere; small asymmetric terms (tempo, side-to-move bonuses,
in-check handling) are the usual suspects. Kill range: fewer than 340 equal kills P2; **more than 0 differences at
all is the interesting finding** and I list every one.

**P3 — any colour-flip differences will be small: |difference| ≤ 30 cp.** Kill range: any difference above 30 cp.

**P4 — the left-right flip is symmetric for all positions tested, with at most 2 exceptions.** A horizontal flip
is a harder symmetry to get exactly right (passed pawns, king shelter, file-dependent bonuses), so I expect it to
be *less* clean than the colour flip — kill range: more than 6 differing positions.

**P5 — `incheck 1` appears in the mirror exactly when it appears in the original** (it is a property of the
position, not of the evaluation). Kill range: any position where the flag differs between the position and its
colour mirror.

**P6 — budget.** 353 + ~353 + 353 eval calls, one process: **under 5 minutes**. Kill range: over 20 minutes.

## What would make me report "not done"
An `eval` line I cannot parse (then the count of unparsed positions is reported and no global "all equal" is
claimed), or a `mirror()` failure on a position (named, not skipped silently).
