# TWO GUI HAZARDS, ONE RULE — for anyone writing a front end for this engine

> **The owner's match program is unaffected.** It drives the engine directly with well-formed positions, so
> neither hazard arises in the PC's self-play or matches. Everything here matters for anyone else writing a
> front end, and for analysis tools.

Seat 23, verified on **PC r15 under PC20, Threads 1, Hash 16, OwnBook false**. Both hazards are confirmed on the
build the owner's PC actually plays, and both share a single defensive rule at the end.

## The detail that matters most

**A corrupted move list is DISCARDED from the first illegal token onward, not skipped.** One bad ply does not lose
one ply — a corruption at ply 3 loses the five good plies that followed it, and the engine then searches a board from
a different game entirely, without saying so beyond one line.

## Hazard 1 — a refused position is silently replaced by the previous game

Send a `position fen` the engine rejects, then ask for a move.

| step | what the engine does |
|---|---|
| `position fen <impossible castling right>` | prints `info string invalid FEN: castling right without king and rook` |
| `isready` | answers **`readyok`** — as if nothing happened |
| `go depth 6` | returns the **PREVIOUS game's move** |

Measured: base tree `d2d4` before and after the refusal; PC r15 `f1c4` before and after. So the refusal is
announced only on an `info string` line that most GUIs never read.

## Hazard 2 — one illegal token replaces the game from that point on

Send `position startpos moves <list>` with one illegal token in it.

| corruption | engine says | perft 1 | intended |
|---|---|---|---|
| illegal token at ply 3 of 8 | `info string illegal move e2e4` | **29** | 38 |
| illegal token at ply 5 | same | **27** | 38 |
| illegal token at ply 7 | same | **33** | 38 |
| clean list (control) | — | **38** | 38 |

The engine keeps the legal prefix, answers `readyok`, and searches that. This is the **more exposed** of the two,
because a GUI sends a move list on every move, whereas hazard 1 needs a malformed FEN.

## The one rule that covers both

> **After every `position` command, count the `info string` lines the engine emits. If any appeared, do not trust
> the position — rebuild it from scratch (`ucinewgame`, then a well-formed `position`).**

Validated by experiment, not recommended on theory. Same corrupted list, intended perft 1 = 38:

| protocol | diagnostics seen | perft 1 | outcome |
|---|---|---|---|
| **naive** — use whatever the engine searched | 1 | **29** | **wrong board, silently** |
| **detect** — abort the game if any diagnostic appears | 1 | not used | safe, plays nothing |
| **fixup** — `ucinewgame` + re-send the well-formed list | 0 | **38** | **exactly right** |

The naive protocol plays a different game; detect refuses to play a wrong move; fixup recovers. **Detect is the
minimum; fixup is what makes the engine usable.**

## Why this is safe for the owner's PC games

The match program drives the engine directly and sends well-formed positions, so neither hazard arises in the PC's
own self-play or matches. These matter for **anyone else writing a front end**, and for analysis tools.

## Where the evidence lives

| hazard | raw evidence |
|---|---|
| refused FEN -> previous game's move | `forge-combo29/swarm/23/check21/RESULT.txt`, `refused_readyok.out` |
| illegal token -> truncated game | `forge-combo29/swarm/23/check11/RESULT_SF57.txt`, `s57.out` |
| the defence, three protocols | `forge-combo29/swarm/23/check11/gui_defence.out` |
| related, same family | 23-C23 (refused FEN keeps previous board), 23-C24 (illegal token truncates), 23-F53 (the defence) |
