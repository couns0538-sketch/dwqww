# MATCH PROTOCOL: do not compare two builds at fixed node counts

Seat 11. Read this before the next match run. Measured on the engine the PC plays (PC r15,
PC20, Threads 1) against base 6b98f217 (Threads 1, Hash 16), on the same ten openings.

## The one-line conclusion
**A fixed `go nodes N` does NOT give two different builds the same search depth. Compare builds at
a fixed DEPTH, or on the clock — not at fixed nodes.**

## Why: the same budget buys different depths

Ten different openings, each searched by both builds with exactly the same node budget.

### `go nodes 50000`
| opening | base depth | PC r15 depth | same depth? |
|---|---|---|---|
| Italian quiet | 10 | 11 | no |
| Sicilian Najdorf | 12 | 12 | yes |
| French Winawer | 11 | 12 | no |
| Caro-Kann Classical | 11 | 12 | no |
| Queen's Gambit | 11 | 12 | no |
| King's Indian | 11 | 11 | yes |
| English Opening | 11 | 14 | no |
| Ruy Lopez closed | 11 | 11 | yes |
| Scandinavian | 11 | 12 | no |
| London System | 11 | 11 | yes |

**Same depth on 4 of 10 openings.**

### `go nodes 250000`
| opening | base depth | PC r15 depth | same depth? |
|---|---|---|---|
| Italian quiet | 16 | 15 | no |
| Sicilian Najdorf | 15 | 14 | no |
| French Winawer | 14 | 17 | no |
| Caro-Kann Classical | 14 | 16 | no |
| Queen's Gambit | 14 | 16 | no |
| King's Indian | 14 | 16 | no |
| English Opening | 15 | 17 | no |
| Ruy Lopez closed | 15 | 18 | no |
| Scandinavian | 14 | 16 | no |
| London System | 14 | 16 | no |

**Same depth on 0 of 10 openings.** The PC build is consistently 1 to 4 plies deeper for the same
node count.

## Why this happens (not a bug)
`go nodes N` stops at the end of the first completed iteration, so what you actually get is a
DEPTH, and the depth a given N buys depends on how efficiently the engine searches. The PC build
searches more efficiently, so the same 250,000 nodes carry it deeper. That is the point of the
build — it just means the node budget is not a neutral yardstick between old and new.

Two related facts from the same measurements:
- `go nodes N` usually uses LESS than N (median 20–34 % short across positions), because it stops
  at an iteration boundary. So "nodes 50000" already means "until depth d completes", not "50000".
- `go softnodes N` does the opposite and overshoots N (median ~33 % over at N=2000).

## Always send BOTH clocks

(`uci_guard.py` in this folder enforces this: `bestmove(wtime=...)` without `btime` raises rather
than silently searching for twelve seconds.)


| command | wall time | depth reached |
|---|---|---|
| `go wtime 6000 btime 6000` | **136 ms** | shallow |
| `go wtime 6000` (no `btime`) | **~12 s** (11.8 s measured) | depth 31, 18.9 M nodes |

**136 ms versus 12 seconds — about two orders of magnitude, from one missing field.** `go wtime 6000`
without `btime` does not hang and does not play an illegal move, but it searches ~12 s instead of
0.14 s. The time manager needs BOTH clocks to build a plan; given only one, the side to move's
budget is effectively unbounded. Send `wtime` and `btime` on every `go`, or a 0.14 s move becomes a
12 s move and can lose on time. (`go btime` alone behaves normally — it is the side to move's clock
that must not be omitted.) Evidence: `checks/clock_edge.txt`.

## The engine relies on YOUR program to end a game
Measured on the self-play path (`go softnodes 2000`, PC20, Threads 1): two complete games each ran
**212 plies** and ended only by **insufficient material** — and along the way each game passed
**nine positions that were a threefold repetition** without the engine ending anything. That is
correct behaviour (a repetition is a CLAIM the arbiter makes, not something an engine enforces), but
it means: **a match program that does not itself detect the third occurrence and the 100th half-move
will play straight past them,** and a game can run far longer than the engine's own evaluation would
suggest. File 6 says the owner's program does end games at the third occurrence and the 100th
half-move — this measurement confirms the engine is relying on it. Evidence:
`checks/selfplay_long.txt`.

## Send the MOVES form when history exists
The two ways to set a position are **not** equivalent. `position fen X` carries **no history**;
`position startpos moves ...` **does**, and the search depends on that difference.

Measured on PC r15 / PC20 / Threads 1 / `go softnodes 2000`: the same board
`r1bqkb1r/pp2pppp/2n2n2/2pp4/3P1B2/4PN2/PPP2PPP/RN1QKB1R w KQkq - 1 5` gives `f1b5` in **3,570 nodes**
from the FEN form and `f1b5` in **3,556 nodes** as that board's third occurrence by move list — the
move agrees, the search tree does not. Another seat (23-C20) reports the stronger case, a **different
move** on its Ruy Lopez line (`b4f8` from FEN versus `f1b5` from the move list) and `c2c4` at 4,532
versus 3,336 nodes on its London line, and isolated the cause as history by showing the en-passant
field makes no difference.

**So: when history exists, send the moves form.** A FEN is fine for a position with no history (a bare
diagram, a FEN file, the honesty pins), but a GUI or match harness that holds a move list should send
the move list — reconstructing it as a FEN discards information the search uses.

Honest scope: my own samples of eight and six openings found no move change, so on most positions the
difference is too small to alter the answer at this budget. That is why my first test missed it, and
why the guidance is "prefer the moves form" rather than "the FEN form is broken".

## Two separate problems — only one needs a protocol change
Worth separating, because they are easy to conflate:
- **Within one build, Threads 1: the decisions are reproducible.** Over 12 real positions the
  answer was identical run to run at `go nodes` 20000, 50000 and 250000 (0 of 12 unstable, with
  bestmove, node count and score all equal) — `checks/match_repeatability.txt`. A node-limited
  match is not noisy.
- **Across two builds, the depth is unequal.** That is the S-F49/S-F50 result above, and it is the
  only reason to change protocol.
So a node budget is fine for repeatability; it is fairness between different engines that it
cannot deliver.

## What to use instead
1. **Fixed depth** (`go depth D`) — both engines search to the same ply. Best for A/B of search
   changes, and it is what the honesty pins already use.
2. **The clock** (6 s + 0.06) — equal in the sense that matters for play, though note the engine
   currently uses only a few hundred ms of it on typical positions (median 238 ms over 20 G
   positions), so it is effectively "as deep as fits in ~0.2–0.8 s".
3. **A node budget is still valid for comparing one build against ITSELF** across a change that
   does not alter efficiency much; it is not valid across builds whose efficiency differs.

**Never quote a clock-stop node count as a deterministic result.**

And never quote a single clock TIME as though it were the clock's behaviour either: fifteen identical
searches on one FEN, same binary and settings, ranged **143 to 661 ms — 4.6x** from nothing but when the
timer fired. Quote a median with its position set, or a range.

Run `clock_repeat_check.py <exe> <name> 5` before quoting any timing figure: it repeats the SAME binary
against itself and reports, per command, whether the move and the metric are stable. It is a procedure,
not advice — and on its first run it caught a `movetime 50` node count varying 47,601 vs 69,531 across
five repeats, and an 11.8 ms wall-time spread at the 6 s clock.

*(A clock search stopped at an 11-60 ms budget returns varying node counts across identical runs of the
same binary; only the chosen move is stable. Measured and corrected by seat 07; see S-F91 and trap 8 in
`PROBES_THAT_LIED.md`.)*

## Where this is measured
- `checks/paired_depth.txt` — the two tables above (both builds, same openings, same budgets).
- `checks/depth_spread.txt` — depth spread within one build: 11–14 at 50k, 14–18 at 250k.
- `checks/nodes_real.txt` — how far under N `go nodes` lands, and its determinism (it is fully
  deterministic run to run, 0 of 15 positions differing).

All runs: fresh process per line, Threads 1, every value parsed from `info depth ... nodes ...`.
