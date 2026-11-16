# The per-move hazard a GUI author must handle: `info string illegal move`

> **Read this first: the diagnostic arrives in response to `position`, BEFORE `readyok`.**
> Consume the engine's output from the moment you SEND the position command, not from the first `readyok`.
> A reader that starts listening at `readyok` never sees `info string illegal move` and will conclude its
> move list was accepted. This single mistake made two of my own runs report a false hazard, and it is the
> easiest way to be blind to the whole problem.

Seat 17, 2026-11-16. Build: PC r15 (base 6b98f217 + FABLE_TO_swarm_5 patch), PC20 settings, Threads 1,
Hash 16. The same behaviour exists on the base tree. Every output below is a real run, read to `bestmove`.

## Why this note exists separately

`position startpos moves <list>` is the command a GUI sends on **every move of every game**. It is therefore a
far more exposed path than the hand-written-FEN route described in `NOTE_select_readline_artifact.md`'s
sibling discussion (see `pc/sc9/gui_session.log` and the S-C9 row in `FINDINGS_TABLE.md`).

## The command and the exact output

### 1. A move list with one illegal move in it

```
position startpos moves e2e4 e7e5 e1e3
isready
go nodes 20000
```

The engine answers, in this order:

```
info string illegal move e1e3
readyok
bestmove g1f3
```

`g1f3` is a legal move **in the position after `e2e4 e7e5`** — the legal prefix — and NOT in the position the
GUI asked for (which does not exist, since `e1e3` is illegal). The engine discarded `e1e3` and everything
after it.

### 2. An illegal first move

```
position startpos moves e2e5
```
```
info string illegal move e2e5
readyok
bestmove d2d4
```

`d2d4` is a legal **startpos** move: the prefix is empty, so the board is still the initial position.

### 3. A token that is not a move

```
position startpos moves e2e4 zzzz
```
```
info string illegal move zzzz
readyok
bestmove e7e6
```

`e7e6` is a legal reply **after `e2e4`** (Black to move). A non-move token is treated exactly like an illegal
move.

### 4. Control: a fully legal list

```
position startpos moves e2e4 e7e5 g1f3
isready
go nodes 20000
```
```
readyok
bestmove b8c6
```

Correct, and the only case with no `info string` line.

## What the engine plays, and why it is dangerous

In cases 1-3 the engine returns a **legal move for a different position** than the one requested. Its
bookkeeping is defensible (keep the legal prefix; file 1 lists this as known), but the observable contract to a
GUI is:

- one `info string` line, which a GUI is not required to parse;
- then `readyok`, which conventionally means "the position is loaded and I am ready";
- then a `bestmove` that belongs to a board the GUI did not ask for.

So a GUI that applies that move to its own board either corrupts its game state or believes the engine
disagrees with it about legality, and there is nothing in the protocol telling it that its move list was
rejected.

## The one-line rule

> **Treat `info string illegal move` as FATAL for that game: do not apply the following `bestmove`, and
> reload the position from a source you trust. Catch it by reading the engine's output from the `position`
> command onwards — the line comes BEFORE `readyok`, so a reader that starts at the first `readyok` is blind
> to it.**

Three lines to implement it, matching the rest of my harnesses:

```python
if any(line.startswith("info string illegal move") for line in engine_output_so_far):
    reject_bestmove_and_reload()   # never apply the move that follows
```

## What a harness must do BEFORE sending the list

The same guard as the FEN route, applied to the move list: replay it yourself and stop at the first move that
does not parse or is not legal in the position you have.

```python
import chess
board = chess.Board("startpos" if startpos else fen)
for token in moves:
    move = chess.Move.from_uci(token)          # raises on a malformed token
    assert move in board.legal_moves, f"illegal move {token} in {board.fen()}"
    board.push(move)
```

Then send exactly the prefix you validated, or send nothing and reload.

## Evidence

| file | content |
|---|---|
| `pc/sc9b/note_cases.json` | the four cases above with their exact tails |
| `pc/sc9b/note_*.log` | full raw output per case |
| `pc/sc9b/hazard.json` | the same result recorded earlier, plus the session-level test |
| `pc/sc9b/*.log` | raw logs for the session-level test |

## Honest limits

- I did not test a move list with a valid-but-illegal move at the very end after 1,000 legal plies; that is
  area 1's ground and seat 21 confirmed the prefix rule there.
- The engine's behaviour here is the documented prefix rule, so this note is about **exposure and the missing
  signal**, not about a new engine defect.
- Whether the owner wants the engine to emit a harder error (an explicit `info string position rejected` plus
  withholding `readyok`) is a design decision I am flagging, not making.

## When exactly the line arrives (measured — and easy to miss)

The `info string illegal move` line is emitted in response to the **`position`** command, i.e. BEFORE the
following `readyok`, not in response to `go`. Measured on the self-play idiom (PC r15, PC20, Threads 1) with a
deliberately corrupted last token:

```
info string illegal move zzzz      <- in response to `position ... moves ...`
readyok
info depth 1 ...                   <- in response to `go`
bestmove c8a8
```

A harness that starts reading only after `readyok` will never see the line and will believe its move list was
accepted. Read the engine's output for the `position` command too, and treat the line as fatal wherever it
appears. Evidence: `pc/guardsp/guard_selfplay.json`.
