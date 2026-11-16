# HAZARD: a rejected position command leaves the engine on the WRONG BOARD, and it answers `readyok` anyway

**Read this before the next training or match run.** Seat 11, measured on the engine the owner's
PC plays (PC r15, built from the FABLE_TO_swarm_5 patch, `-DFORGE_MATE_ALPHA_GUARD=1`, PC20
settings, Threads 1, Hash 16).

## Priority, in one sentence
**Route 2 below is the one to fix first: a GUI sends a move list every single move, so one bad
token in `position startpos moves ...` is a likely event, while a malformed FEN is rare — and both
routes end with the engine answering a legal move for the WRONG board after a `readyok`.**

## The demonstration that matters: a real game, one bad command, a plausible wrong move

Played out on the PC's own self-play setting (`go softnodes 2000`), engine against itself. Normal
play is perfectly sensible for twelve plies:

```
d2d4 g7g6 b1c3 d7d5 e2e4 d5e4 c3e4 f8g7 g1f3 g8f6 e4f6 e7f6
-> rnbqk2r/ppp2pbp/5pp1/8/3P4/5N2/PPP2PPP/R1BQKB1R w KQkq - 0 7
```

Then the engine holds that six-ply board, a **truncated FEN** arrives for the next game, and the
harness asks for a move:

```
position fen 8/8/8/8/8/8/8/K6k w - -          <- five fields, refused
isready             -> info string invalid FEN: FEN must contain six fields
                    -> readyok                                        (arrives anyway)
go softnodes 2000   -> bestmove c3e4
```

`c3e4` is **legal in the six-ply board and illegal in the intended new board** — and it is a
perfectly ordinary developing move, not something that looks wrong. That is the whole hazard: a
silent, confident, plausible move for the previous position.

## Two routes into the same failure — check for BOTH

### Route 1: a malformed FEN (measured here)
Any `position fen` with too few fields is refused, the board is kept, `readyok` still comes, and the
next search answers for the old board. Under every search mode the PC actually uses:

| search command | bestmove returned | which game |
|---|---|---|
| `go softnodes 2000` (self-play) | `g8f6` | previous game — stale |
| `go nodes 20000` (matches) | `g8f6` | previous game — stale |
| `go movetime 100` (clock) | `g8f6` | previous game — stale |

Evidence: `checks/fen_on_real_path.txt`, `checks/full_game_hazard.txt`,
`checks/fen_truncation_pc20.txt`. Every truncation length (5, 4, 3, 1 fields, and a bare
`position fen`) behaves this way. Note the asymmetry: too many fields is harmless (the extra token
is dropped and the board is right — `checks/extra_token_real.txt`, 60 of 60 real-path searches
identical), but too few fields plays the previous game.

### Route 2: an illegal move inside a move list (far more exposed)
A GUI sends `position startpos moves ...` **every move**, so this route is hit far more often than a
malformed FEN. An illegal token in the list is reported and the engine keeps the legal PREFIX — then
searches that prefix and answers confidently:

```
position startpos moves e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 e2e4
isready   -> info string illegal move e2e4
          -> readyok
go perft 1 -> nodes 33      (the six-ply prefix's count; startpos would be 20)
go softnodes 2000 -> bestmove d2d3
```

So the same "confident wrong board" shape arises from one bad token in a move list, and the
resulting position is the *prefix*, not the position the GUI meant. Evidence:
`checks/illegal_move_route.txt`. This route is independently confirmed by another seat on the PC
build: seat 21's **21-C9** (`position fen F moves`, illegal at ply 10, keeps the legal prefix, 26/726,
same on the PC build) and **21-C2** (illegal at plies 1, 10 and 500 of a 1,000-ply list keeps the
legal prefix exactly) — and seat 21's 21-C9 also records that a REFUSED FEN inside the
`fen ... moves` form keeps the old position, i.e. Route 1 inside Route 2's syntax.

**How far it diverges** (`checks/prefix_divergence.txt`): take a 16-ply Ruy Lopez line and corrupt
one ply. The engine keeps the legal prefix, searches it consistently, and answers a legal move for
*that* board — but the board is up to 13 plies in the past, and the move is usually illegal in the
position the GUI thinks it is playing:

| corruption | plies actually kept | perft 1 (engine = python-chess) | move returned | legal in the intended position? |
|---|---|---|---|---|
| illegal token at ply 3 | 2 | 29 | `g1f3` | **no** |
| illegal token at ply 7 | 6 | 32 | `b5c6` | **no** |
| illegal token at ply 11 | 10 | 25 | `a4c6` | **no** |
| illegal token at ply 15 | 14 | 27 | `a2a4` | yes (by luck — one ply short) |

Every prefix's perft 1 matched python-chess exactly, so the truncation is clean and silent and
never crashes. This is why Route 2 is the more dangerous of the two in practice: a GUI sends a move
list every move, so one bad token is a likely event, and the result is a legal move for a position
that may be a dozen plies out of date.

**Both routes share one shape:** the engine reports the problem on an `info string` line, keeps a
board it was not asked for, and answers `readyok` as if nothing happened.

## How bad is it: ONE move, not the session
The damage is strictly confined to the single rejected command; the next well-formed position
recovers on its own (`checks/recovery_test.txt`, `checks/recovery_sweep.txt`).

Sequence, PC r15 / PC20 / Threads 1, `go softnodes 2000`:
```
game 1:  position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3
bad:     position fen 4k3/8/8/8/8/8/8/4K3 w - -            <- refused, stale board kept
game 3:  position fen rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3
         go softnodes 2000  ->  bestmove f3e5
```
`f3e5` is legal in game 3 and **not** legal in game 1 or in the bad board, so game 3 played
correctly. The same holds when game 3 is sent as
`position startpos moves e2e4 e7e5 g1f3 d7d5`.

Swept over 20 different game-3 positions: **18 recovered correctly, 0 infected** (no case where the
answer was legal only in game 1), 2 rows ambiguous only because the move was legal in both boards.

**So the blast radius is one move.** A harness that discards a game on a refusal loses that one game
and nothing else.

## Does `ucinewgame` clear it? Yes — but it does not restore your position
This decides the defence (`checks/ucinewgame_clears.txt`):

| what you send after the refused command | bestmove | board in effect |
|---|---|---|
| nothing | `g8f6` | **previous game — stale** |
| `ucinewgame` | `d2d4` | **startpos** (perft 1 = 20), *not* your position |
| `ucinewgame` then re-send the FEN | `d2d4` | startpos again — the FEN was still malformed |

So `ucinewgame` clears the stale board and removes the wrong-game danger, but it resets to the
**start position**, a different board again. It is a safe reset, not a recovery.

## The rule for a harness — one line
**Treat any `info string invalid FEN` or `info string illegal move` as fatal for that game: do not
send `go`, discard the game, and re-send a well-formed `position` (or start a fresh process) before
searching again.**

### The three protocols, tested against the worst case
The worst case is when the BAD COMMAND *is* the new game's position — so there is no good position
afterwards to recover from (`checks/defence_protocol2.txt`, `checks/fixup_sweep.txt`):

| protocol | what it does | bestmove returned | verdict |
|---|---|---|---|
| naive | asks for a move right after the bad command | **`g8f6`** | **WRONG — a previous-game move** |
| detect | checks for the refusal line and **aborts the game** | none played | **SAFE** |
| fixup | `ucinewgame`, then re-sends a WELL-FORMED position | `f3e5` | **CORRECT — the new game's move** |

The `fixup` protocol was then swept over 15 different truncated-then-corrected positions:
**15 correct, 0 wrong**. So both `detect` and `fixup` work; `naive` fails.

In order of strength:
1. **Best:** after a refusal, discard the game outright and start a fresh process for the next one.
2. **Acceptable:** send `ucinewgame` *and* re-send the intended position, well-formed, before `go`.
3. **Never:** trust `readyok`, or accept a `bestmove` from a process whose last `position` was
   refused. A harness that only waits for `bestmove` cannot tell "move for the new game" from
   "move for the old one" — both are legal moves.

## Where this is measured
- `checks/full_game_hazard.txt` — the self-play demonstration at the top.
- `checks/fen_on_real_path.txt` — Route 1 under all three search modes.
- `checks/illegal_move_route.txt` — Route 2 (illegal move in a list).
- `checks/fen_truncation_pc20.txt` — every truncation length, and the stale perft 1.
- `checks/ucinewgame_clears.txt` — the `ucinewgame` test.
- `checks/defence_protocol2.txt`, `checks/fixup_sweep.txt` — the three protocols.
- `checks/recovery_test.txt`, `checks/recovery_sweep.txt` — the one-move blast radius.

All runs: PC r15, PC20, Threads 1, Hash 16, fresh process per run, every value parsed.
