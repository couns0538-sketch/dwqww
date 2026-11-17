# CHECK of seat 12's S-F1 — `ucinewgame` resets the board to startpos

## Verdict
**CONFIRMS 12-F1**, with the source line and the behavioural consequence both verified, on BOTH builds.

Seat 12 claimed: `ucinewgame` silently resets the board to startpos (`src/uci.cpp:254-257`,
`board.set_fen(StandardStartFen)`), so `position fen X` / `ucinewgame` / `go` searches **startpos**, not X —
and a checker that does not model this reports false illegal bestmoves (it caused 6 in their own harness).

## Source (read, not assumed)
`src/uci.cpp:386-389` on the PC build:

```cpp
} else if (command == "ucinewgame") {
    stop_search();
    searcher.clear();
    (void)board.set_fen(forge::Board::StandardStartFen);
}
```

So `ucinewgame` does three things: stops any search, **clears the searcher** (which per S-F17 work includes
`shared_.tt.clear()`), and **sets the board to startpos**. Seat 12's line numbers differ slightly from the PC
build's (254-257 vs 386-389) because the PC patch inserts code above; the statement is the same.

## Behavioural confirmation
A K+P position `4k3/8/8/8/8/8/4P3/4K3 w - - 0 1` (10 legal moves, engine chooses `e1d2`):

| sequence | engine answered | nodes |
|---|---|---|
| `position fen <K+P>` then `go depth 1` | `e1d2` | 10 |
| `position fen <K+P>`, **`ucinewgame`**, `go depth 1` | **`d2d4`** | **26** |

`d2d4` with 26 nodes is startpos depth 1. So the board really was replaced by startpos — exactly seat 12's
claim. Both builds behave the same.

## The second half, which turns out to matter for MY OWN work
`ucinewgame` also **clears the transposition table**, so it is a *cold reset*, not merely a board reset. Three
identical depth-12 searches of the same position in one process:

| discipline | node counts |
|---|---|
| `ucinewgame` before each | **52,591 / 52,591 / 52,591** (identical every time) |
| no `ucinewgame` (warm table) | **52,591 / 27,239 / 21,407** (collapses) |

**This invalidates the framing of my own job 16.** That job ran a "cold" arm (fresh process per position) and
a "warm" arm (one process, `ucinewgame` between positions). Because `ucinewgame` is a cold reset, **my warm
arm was never warm** — and the data confirm it: all 38 cold/warm pairs were IDENTICAL in bestmove and node
count, differing in nothing at all.

Job 16's conclusion is unaffected (it was a null result: no missed mates in either arm, with the honest
caveat that the material was too easy). But its *label* was wrong: the two arms were the same experiment, so
the report's claim to have tested "cold and warm disciplines" is not true. I am recording that here and
correcting the report rather than leaving a label that overstates what was done.

The lesson generalises and is worth keeping: **`ucinewgame` is the cold-start control, not a step between
warm searches.** To test warm behaviour you must simply run the second search in the same process with
nothing in between.

## How this affects harnesses (the practical half)
1. A harness that sends `position fen X` / `ucinewgame` / `go` is searching **startpos**. Any bestmove it
   validates against X will look illegal. That is seat 12's warning and it is real.
2. The safe order is `ucinewgame` **then** `position ...`, which is what all three of my scripts that use it
   already do (`checks/check_27f2.py`, `job10/underreport.py`, `job16/loneking.py` — audited).
3. `ucinewgame` is the right way to get a cold table cheaply; it is *not* a way to get a warm one.

## Reproduce
```
# source
sed -n '386,389p' ~/pc/forge-combo29/src/uci.cpp   # or the base tree's equivalent
# behaviour
printf 'position fen 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1\nisready\nucinewgame\nisready\ngo depth 1\n' \
  | ./forge          # answers d2d4 (startpos), not e1d2
```
Raw: `out_12f1/ucinewgame.json`.
