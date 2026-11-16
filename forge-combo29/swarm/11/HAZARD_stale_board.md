# HAZARD: a refused FEN leaves the PREVIOUS board, and the engine answers `readyok` anyway

**Read this before the next training or match run.** Seat 11, measured on the engine the owner's
PC plays (PC r15, built from the FABLE_TO_swarm_5 patch, `-DFORGE_MATE_ALPHA_GUARD=1`, PC20
settings, Threads 1, Hash 16).

## The hazard in one paragraph
If a `position fen` command is malformed — here, a FEN with too few fields — the engine prints an
`invalid FEN` line, **keeps the board from the previous game**, and still answers `readyok`. A
harness that syncs on `readyok` (the normal UCI way) then asks for a move and receives a **legal,
confident move for the wrong game**. Nothing in the reply says anything is wrong. This fires on
every search command the PC actually uses: `go softnodes 2000`, `go nodes 20000`, `go movetime`.

## The exact sequence, with the exact output

### Without a defence — the wrong move comes back
```
game 1:  position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3
game 2:  position fen 4k3/8/8/8/8/8/8/4K3 w - -          <- truncated: five fields
         isready
           info string invalid FEN: FEN must contain six fields
           readyok                                          <- arrives anyway
         go softnodes 2000
           bestmove g8f6                                    <- a GAME-1 move
```
`g8f6` is legal in game 1 (Black to move) and **not** legal in the intended game-2 position, so a
harness that trusts the move is playing the previous game.

Measured identically under all three real search modes (`checks/fen_on_real_path.txt`):

| search command | bestmove returned | which game |
|---|---|---|
| `go softnodes 2000` (self-play) | `g8f6` | game 1 — stale |
| `go nodes 20000` (matches) | `g8f6` | game 1 — stale |
| `go movetime 100` (clock) | `g8f6` | game 1 — stale |

Every truncation behaves this way (`checks/fen_truncation_pc20.txt`): 5, 4, 3 and 1 fields, and a
bare `position fen`, are each refused with `FEN must contain six fields` and each leaves perft 1 at
the previous board's count (26 in that test). The full 6-field FEN gives the new board normally.
The same table on base 6b98f217 is identical (`checks/...`), so this is original engine behaviour,
not a regression of the PC patch.

## How bad is it: ONE move, not the session
The damage is strictly confined to the single rejected command; the next well-formed position
recovers on its own (`checks/recovery_test.txt`, `checks/recovery_sweep.txt`).

Sequence tested, PC r15 / PC20 / Threads 1, `go softnodes 2000`:
```
game 1:  position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3
bad:     position fen 4k3/8/8/8/8/8/8/4K3 w - -            <- refused, stale board kept
game 3:  position fen rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3
         go softnodes 2000  ->  bestmove f3e5
```
`f3e5` is legal in game 3 and **not** legal in game 1 or in the bad board, so game 3 played
correctly. The same holds when game 3 is sent as
`position startpos moves e2e4 e7e5 g1f3 d7d5` — same answer, same legality.

Swept over 20 different game-3 positions: **18 recovered correctly, 0 infected** (no case where the
answer was legal only in game 1), 2 rows ambiguous only because the move was legal in both boards.

**So the blast radius is one move.** A harness that discards a game on `invalid FEN` loses that one
game and nothing else. This does not make the hazard harmless — the wrong move comes back and looks
completely legal — but it tells you the cost of the simple defence is one game, not the run.

## Does `ucinewgame` clear it? Yes — but it does not restore your position
This is the part that decides the defence (`checks/ucinewgame_clears.txt`):

| what you send after the refused FEN | bestmove | board in effect |
|---|---|---|
| nothing | `g8f6` | **game 1 — stale** |
| `ucinewgame` | `d2d4` | **startpos** (perft 1 = 20), *not* game 2 |
| `ucinewgame` then re-send the FEN | `d2d4` | startpos again — the FEN was still malformed |

So `ucinewgame` does clear the stale board and removes the wrong-game danger, but it resets to the
**start position**, which is a different board again. It is a safe reset, not a recovery.

## The rule for a harness — one line
**Treat any `info string invalid FEN` as fatal for that game: do not send `go`, discard the game,
and re-send a well-formed `position` (or start a fresh process) before searching again.**

### The three protocols, tested against the worst case
The worst case is when the MALFORMED FEN *is* the new game's position — so there is no good
position afterwards to recover from (`checks/defence_protocol2.txt`, `checks/fixup_sweep.txt`):

| protocol | what it does | bestmove returned | verdict |
|---|---|---|---|
| naive | asks for a move right after the bad FEN | **`g8f6`** | **WRONG — a game-1 move** |
| detect | checks for `invalid FEN` and **aborts the game** | none played | **SAFE** |
| fixup | `ucinewgame`, then re-sends a WELL-FORMED position | `f3e5` | **CORRECT — game 3's move** |

The `fixup` protocol was then swept over 15 different truncated-then-corrected game-3 positions:
**15 correct, 0 wrong**. So both `detect` and `fixup` work; `naive` fails.

Concretely, in order of strength:
1. **Best:** after a refused FEN, discard the game outright. Never accept a bestmove from a process
   whose last `position` was refused.
2. **Acceptable:** send `ucinewgame` *and* re-send the intended position before `go`. This clears the
   stale board (startpos) and then applies your position — but only if your FEN is now well-formed;
   re-sending the same malformed FEN leaves you on startpos.
3. **Safest of all:** drive each game in a fresh process.

What NOT to do: trust `readyok`. It is emitted after the refusal and carries no information about
whether the board changed. A harness that only checks for `bestmove` cannot distinguish "move for
game 2" from "move for game 1" — both are legal moves.

## Where this is measured
- `checks/fen_on_real_path.txt` — the three real search modes.
- `checks/fen_truncation_pc20.txt` — every truncation length, and the stale perft 1.
- `checks/ucinewgame_clears.txt` — the `ucinewgame` test above.
- `checks/gui_sequence_pc20.txt` — the same hazard framed as a GUI game switch.

All runs: PC r15, PC20, Threads 1, Hash 16, fresh process per run, every value parsed.
