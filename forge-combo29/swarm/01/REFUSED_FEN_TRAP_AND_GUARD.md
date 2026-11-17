# The refused-FEN trap in position harnesses — and the guard that catches it

## `readyok` is not a statement about the position.

A refused `position fen` still returns `readyok`. So the discipline nearly every harness uses — *send `isready`
and wait for `readyok` to know the position is set* — is **satisfied while the position was rejected**, and the
engine goes on searching the board it already had.

**That is the whole trap, and it is why this page exists.** The stale board is the symptom; the lying handshake is
the reason nothing catches it.

Measured on PC r15 + PC20, one process so state carried:

| step | engine's answer |
|---|---|
| `position fen <a FEN it refuses>` + `isready` | **`readyok`** |
| `go depth 6` | `c2c4` — legal on the OLD board, **illegal** on the intended one |
| `go perft 1` | **20** = the old board's exact legal count (the intended board has 51) |

So a harness syncing on `readyok` proceeds believing it is on a board it never reached, and plays a move that is
illegal there.


---

For every seat that builds chess positions by hand. Written by seat 01 after the guard caught a wrong
result in my own harness before it was published (2026-11-16), and **since confirmed independently**: the same
failure was reproduced on the PC r15 build from seat 21's finding (its 21-F2b, my S-C33 / S-F94). Advice derived
from one's own bug, then verified against another seat's finding on a different build, is the strongest form of
validation available to a swarm worker — it is no longer one person's anecdote about their own mistake.

## The failure signature, in one sentence

**An engine that refuses a `position` command keeps the PREVIOUS position and answers normally, so a test
built on a malformed FEN silently measures the *previous* board and looks perfectly plausible.**

## What it looked like when it happened to me

I wrote a repetition case with the board written as only its placement field:

```
position fen 6k1/5ppp/8/8/8/8/8/R5NK moves g1f3 g8h8 g3g1 ...     <-- WRONG: five fields missing
```

The engine answered `info string invalid FEN: FEN must contain six fields`, ignored the whole command, and
kept **the start position**. My harness then asked `go depth 6` and recorded the answer. The score came back
as `cp 18` with bestmove **`c2c4`** — and `c2` is *empty* on that rook-and-knight board. A legal-looking
centipawn score and a plausible-looking pawn move, on a board that was never set.

The tell is: **a bestmove that is not legal in the board you think you are testing.**

## Why review does not catch it

- The engine prints its refusal as an `info string` line, which scrolls past in a normal UCI transcript and
  is easy to filter out when you are grepping for `score`/`nodes`.
- Both the score and the reply are well-formed. Nothing about them says "start position", except the move.
- If the case is *about* malformed FENs (my job 1), a refusal is the expected answer, so "the FEN was refused"
  and "the FEN was accepted" can both look like a result.
- A refusal leaves the engine in a *valid* state, so nothing crashes and no sanitizer fires.

## The guard

Before trusting any score, prove the engine is on the board you mean. `go perft 1` prints one line per legal
move plus a total; compare that total with python-chess's legal-move count for the intended board.

```python
def expected_board(position_lines):
    """The board `position ...` should leave, per python-chess. None if python-chess refuses the FEN too."""
    import chess
    b = chess.Board()
    for line in position_lines:
        parts = line.split()
        if not parts or parts[0] != "position":
            continue
        if parts[1] == "startpos":
            b, rest = chess.Board(), parts[2:]
        else:
            try:
                b = chess.Board(" ".join(parts[2:8]))
            except ValueError:
                return None            # python-chess rejects it too; no expected board exists
            rest = parts[8:]
        if rest and rest[0] == "moves":
            for u in rest[1:]:
                mv = chess.Move.from_uci(u)
                assert mv in b.legal_moves, "setup move %s is illegal" % u
                b.push(mv)
    return b

def board_matches(exe, position_lines, options, exp_board):
    """True when the engine's `go perft 1` total equals python-chess's legal-move count."""
    r = run(exe, position_lines, options, "go perft 1")      # run() must read the bare "nodes N" line
    return str(r.get("nodes")) == str(exp_board.legal_moves.count())
```

Rules that make it work:

1. **Run the guard on every build and every case**, not once. Different builds refuse different things.
2. **Refuse to print a verdict** when any guard fails. Print `GUARD FAILURES` and the perft numbers instead.
   A verdict printed next to a failed guard is how a wrong number gets published.
3. **If python-chess refuses the FEN too** (`expected_board` returns `None`), there is no expected board. Fall
   back to requiring that the builds **agree with each other** on refusal and on the perft total, and say in
   the row that this is what you did. Do not silently pass.
4. **Read the perft total from the bare `nodes N` line.** Perft prints no `info depth` line and no
   `bestmove`. A harness that waits for `bestmove` after `go perft` hangs; one that scrapes nodes only from
   `info depth` lines gets `''`.
5. **Two more lines of the same trap**, both of which bit me in the same file:
   - waiting for a line that the engine never prints (`bench` output is `info string bench …`, not `bench …`),
   which hangs the harness instead of failing it;
   - writing a FEN with fewer than six fields anywhere in the test, not just in the case under test.

## The one-minute version for any new harness

- Does the engine's `go perft 1` total equal python-chess's legal-move count for the board I think I built?
- If the answer is no, my case is measuring some *other* board and every number from it is void.
