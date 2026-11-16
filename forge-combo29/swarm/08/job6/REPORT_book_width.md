# CHECK + MEASUREMENT — how wide is the opening book that 08-F3 hit? — seat 08 job 6

Follows Opus file 3 ("`OwnBook` is true by default on the base tree; a few start positions are answered from the
built-in book (seats 08, 20)") and my own 08-F3.

## The answer
**9 of 14 opening positions are answered from the built-in book with `OwnBook` at its default true**, including
`position startpos` itself. The book reaches at least to `1.e4 e5 2.Nf3 Nc6 3.Bb5` and stops by
`1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4` (that one is a real search, 12 info lines).

| position | answered by | bestmove | info lines |
|---|---|---|---|
| **startpos** | **BOOK** | c2c4 | 0 |
| 1.e4 | BOOK | e7e5 | 0 |
| 1.e4 e5 | BOOK | g1f3 | 0 |
| 1.e4 e5 2.Nf3 | BOOK | g8f6 | 0 |
| 1.e4 e5 2.Nf3 Nc6 3.Bb5 | BOOK | c6d4 | 0 |
| 1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 | search | f8c5 | 12 |
| 1.d4 | BOOK | d7d5 | 0 |
| 1.d4 d5 | BOOK | g1f3 | 0 |
| 1.d4 d5 2.c4 | BOOK | e7e6 | 0 |
| 1.c4 | BOOK | g8f6 | 0 |
| 1.Nf3 | search | d7d5 | 13 |
| 1.a3 (non-opening) | search | e7e6 | 12 |
| 1.h4 (non-opening) | search | d7d5 | 13 |
| random 20 plies | search | c4a5 | 13 |

`go depth 12` from startpos is a **search** (12 info lines, e2e4) — the book is not probed for a depth search,
which confirms my prediction and seat 06's S-F6.

## A run-to-run variation worth knowing
The book move at startpos is NOT fixed: one run printed `info string book move e2e4`, another (the script) `c2c4`
with `bestmove c2c4`. The engine exposes `Book Variety type spin default 30 min 0 max 100`, so two identical
book-answered searches can return different moves. Anyone using a book-on engine for repeatability gets none.

## Why this matters to every harness in the swarm
`position startpos; go movetime 50` — the most likely first line anyone writes — is answered in ~0.2 ms with no
search at all. A "startpos latency" or a "startpos bestmove" measured with the default options is measuring the
book, not the engine. That is now a measured fact, not a suspicion, and it sharpens 08-F3 from "one position in
my set" to "the default input itself".

## Verification of my own claim
`OwnBook true` -> `info string book move e2e4` then `bestmove e2e4`. `OwnBook false` -> `bestmove e2e4` with no
book line. Both waited out to `bestmove` (no piped quit; seat 19's 19-F12).

## Show it again

    cd forge-combo29/swarm/08/job6 && python3 book_width.py ~/builds/release/forge /tmp/bw.txt

    printf 'uci\nsetoption name OwnBook value true\nisready\nucinewgame\nisready\nposition startpos\nisready\ngo movetime 50\n' | ~/builds/release/forge | grep -E 'book|bestmove'

Raw output committed as `book_width.txt`.

## What I did not do
- Did not map the whole book (I tested 14 lines, not the book's full key set).
- Did not test whether `Book File` (default `<empty>`) can change the book.
- Did not measure the book's hit rate over O and G beyond 08-F3's 1-in-200.
