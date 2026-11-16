# seat 20 — check of seat 12's S-F1 (`ucinewgame` silently resets the board)

Verdict: **CONFIRMS seat 12's S-F1**, and I make it decisive with a black-to-move position.

Raw: `out_check.txt` (pasted), `check_s12f1.txt` (every transcript with its commands), `check_s12f1.json`.
Script: `check_s12f1.py`. Build: `/agent/repos/build-base/forge` sha256 `e06310ec…` (4/4 pins, `../HONESTY.txt`).
`OwnBook false` in every case, so no book answer can be confused with a search.

## The decisive cases

The midgame position `r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1` is a bad test subject:
its natural answer `d2d4` is legal in startpos too, so the verdict was "legal in BOTH". So I used the same board
with **black to move**, where NO move can be legal in both boards:

| case | commands (after uci/isready) | bestmove | verdict |
|---|---|---|---|
| A2 | `position fen <black-to-move>` / isready / **ucinewgame** / isready / `go depth 6` | **d2d4** | legal in STARTPOS only |
| A3 | `position fen <black-to-move>` / isready / `go depth 6` (no ucinewgame) | **d7d6** | legal in the position only |

`d2d4` is a WHITE move; the position to be searched had BLACK to move, so the engine demonstrably was not
searching the position it was given. That is the finding, with no ambiguity about move overlap.

The same with `position startpos moves …` (10 plies):

| case | bestmove | verdict |
|---|---|---|
| D: movelist, then ucinewgame | d2d4 | legal in STARTPOS only |
| E: movelist, no ucinewgame | d1b3 | legal in the position only |

And the order matters: `ucinewgame` **before** `position fen X` leaves X in force (case C answers `d2d4`, legal in
both — consistent with X being searched; the decisive A2/D cases show the reset only bites when `ucinewgame`
follows the position).

## Silent
The engine prints nothing about the reset: no `info string`, no line mentioning "reset" or "startpos", and it never
echoes a `position` line. A harness that does not model the reset cannot notice it — which is exactly seat 12's
point about false "illegal bestmove" reports.

## The source, quoted
`src/uci.cpp:254-257` (6b98f217):
```
} else if (command == "ucinewgame") {
    stop_search();
    searcher.clear();
    (void)board.set_fen(forge::Board::StandardStartFen);
}
```
The third line is the reset. Nothing documents it in the UCI answer.

## Against the UCI specification
`ucinewgame` is specified as a notification that the next search "will be from a different game". `position …` is
the command that sets the position. Resetting the board inside `ucinewgame` means the engine discards a position
it was told to hold; a GUI that (legally) sends `position` once and `ucinewgame` before each game will search
startpos. **This is why a GUI can hit it in real play, not only a harness**: the common order is
`ucinewgame` then `position`, which is safe, but any GUI or tool that sends `position` first (or re-sends
`ucinewgame` mid-session) is silently moved to startpos.

## Where my predictions went
Predictions 1, 2, 3, 4, 5 all held. Prediction 1's *first* wording would have been "killed" by my own bad choice of
test position (legal in BOTH) — that is a flaw in my test design, not in the finding, and the added black-to-move
case settles it decisively. Recorded rather than hidden.

## Commands that show it again
```
printf 'uci\nsetoption name OwnBook value false\nisready\nposition fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 0 1\nisready\nucinewgame\nisready\ngo depth 6\nquit\n' | ./forge | grep bestmove
  -> bestmove d2d4        (a WHITE move, on a BLACK-to-move position: the position was discarded)
printf 'uci\nsetoption name OwnBook value false\nisready\nposition fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 0 1\nisready\ngo depth 6\nquit\n' | ./forge | grep bestmove
  -> bestmove d7d6        (a black move: the position was searched)
python3 check_s12f1.py <release-exe> .
```
