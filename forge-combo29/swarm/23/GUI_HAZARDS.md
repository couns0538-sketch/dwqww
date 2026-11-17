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

## Hazard 3 — a `go` with only the opponent's clock never answers

Send `go wtime N` while it is **Black** to move (or `go btime N` while White is to move). The clock that was sent does
not belong to the side to move, so no limit is set:

| probe | PC r15 + PC20 | base |
|---|---|---|
| Black to move, `go wtime 1000` | **no bestmove within 3 s**, 0 diagnostics | same |
| Black to move, `go btime 1000` (own clock) | answered in 0.02 s | 0.04 s |
| White to move, `go btime 1000` | **no bestmove within 3 s**, 0 diagnostics | same |
| White to move, `go wtime 1000` (own clock) | answered in 0.03 s | 0.05 s |

This is the least diagnosable of the three: hazards 1 and 2 give you a **wrong board** with a diagnostic line
available; this one gives you **no move at all** and **no diagnostic**. A GUI that sends a partial clock simply stops
receiving moves with nothing in the engine's output to say why. Remedy (seat 02's design suggestion, not my
measurement): print an `info string` and fall back to a bounded default when neither clock belongs to the side to move.

## The rules that cover all three

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


## What a well-behaved driver looks like, end to end

Three seats were bitten by DRIVER SHAPE rather than by engine behaviour (the FEN-vs-moves difference in 23-C20, the
refused-FEN stale board, the illegal-token truncation). Here is the whole protocol in one block, in the order that
avoids every hazard on this page.

```
startup      uci  ->  read until "uciok"
             for each option you set:   setoption ...
                                        isready  ->  read EVERY line until "readyok"
                                        (stop on "unknown option" / "invalid value")
             ucinewgame         ONCE, before any position        <- see 23-C1: it DISCARDS a position sent before it
position     ALWAYS send the move list when you have one:
                 position startpos moves e2e4 e7e5 g1f3 ...
             only use `position fen` when there is no history
             then:  isready  ->  read EVERY line until "readyok"
             **count the `info string` lines you just read.**
                 if ANY appeared  ->  the position was refused or truncated.
                                       do not search it. `ucinewgame` and rebuild.
search       send BOTH clocks for the current game, every time:
                 go wtime <ms> btime <ms> winc <ms> binc <ms>
             never one clock alone (hazard 3: no answer, no diagnostic)
             read until "bestmove" — never send the next command first (19-F12: a pipelined `quit`
                 makes this build answer `bestmove a2a3` with 0 nodes)
shutdown     quit, only when no search is running
```

The four rules, which are the whole of it:

1. **`ucinewgame` before the first `position`, never between a `position` and its search.**
2. **Send the move list, not a FEN, when history exists** — the FEN form can change the answer (23-C20).
3. **Count `info string` lines after every `position`; rebuild if any appeared.** The line is the only signal that
   the engine is not on the board you think it is.
4. **Send both clocks, and read to `bestmove` before the next command.**

Every one of those maps to a hazard measured on the PC build on this page, and to a seat that lost time to it.
**Claim strength, stated plainly:** this driver shape is **validated for all three hazards**, each with a control
showing what a naive driver does instead — H1: the naive driver searches the *stale* board; H2: it searches a *third*
board (the truncated prefix); H3: it never gets a move at all, while the compliant driver gets one in 30 ms.

## Why this is safe for the owner's PC games

The match program drives the engine directly and sends well-formed positions, so neither hazard arises in the PC's
own self-play or matches. These matter for **anyone else writing a front end**, and for analysis tools.

## Where the evidence lives

| hazard | raw evidence |
|---|---|
| refused FEN -> previous game's move | `forge-combo29/swarm/23/check21/RESULT.txt`, `refused_readyok.out` |
| illegal token -> truncated game | `forge-combo29/swarm/23/check11/RESULT_SF57.txt`, `s57.out` |
| the defence, three protocols | `forge-combo29/swarm/23/check11/gui_defence.out` |
| partial clock -> no answer, no diagnostic | `forge-combo29/swarm/23/check02/RESULT.txt`, `partial_clock.out` |
| related, same family | 23-C23 (refused FEN keeps previous board), 23-C24 (illegal token truncates), 23-C25 (partial clock hangs), 23-F53 (the defence) |
