# S02 check of seat 16's S-F6 (book only on game searches) — CONFIRMS

Their claim: "the built-in book cannot affect an analysis search: src/uci.cpp:524-528 probes it only when
`game_search` holds, i.e. only for `go wtime/btime` or `go movetime` (not `go depth`, `go nodes` or
`go infinite`)".

## what I measured (my own harness, `check_book_gate.py`; each search the first of a fresh process, so COLD)

Startpos, where a book hit is most likely. Same `go` form sent twice: OwnBook true and false.

| go form | OwnBook | book line? | bestmove | info depth lines |
|---|---|---|---|---|
| `go depth 8` | true | no | d2d4 | 8 |
| `go depth 8` | false | no | d2d4 | 8 |
| `go nodes 20000` | true | no | d2d4 | 10 |
| `go nodes 20000` | false | no | d2d4 | 10 |
| `go infinite` | true | no | e2e4 | 16 |
| `go infinite` | false | no | e2e4 | 16 |
| `go wtime 5000 btime 5000` | true | **YES: `info string book move c2c4`** | **c2c4** | 0 |
| `go wtime 5000 btime 5000` | false | no | e2e4 | 16 |
| `go movetime 300` | true | **YES: `info string book move e2e4`** | e2e4 | 0 |
| `go movetime 300` | false | no | e2e4 | 16 |

### verdict checks (printed by the script that measured them)
```
- a book line DOES appear for `go movetime` with OwnBook true      PASS
- a book line DOES appear for `go wtime` with OwnBook true         PASS
- NO book line for `go depth 8` with OwnBook true                  PASS
- NO book line for `go nodes 20000` with OwnBook true              PASS
- NO book line for `go infinite` with OwnBook true                 PASS
- `go depth 8` gives the same bestmove with OwnBook on and off     PASS
```

## verdict: CONFIRMS S-F6
Analysis searches (`depth`, `nodes`, `infinite`) never touch the book; game searches (`wtime`, `movetime`) do.
The 0 `info depth` lines on both book rows is the sharpest evidence: those searches never ran at all.

## beyond their finding: a book hit can CHANGE THE MOVE, not just save time
Seat 16 frames this as "the book cannot affect an analysis". My table shows the more consequential half:
`go wtime 5000 btime 5000` on startpos answers **c2c4 from the book** while the same position searched without
the book answers **e2e4**. Same position, same clock, different move — so `OwnBook` is not a speed knob, it
changes what the engine plays. The brief's known list says a few start positions are answered from the book;
what I add is that the book's move need not be the searched move, which is why every latency or
bestmove-agreement harness must send `setoption name OwnBook value false` (as the PC apparently does).

This also explains a number in my own job-1 report: 786 of 5,779 searches (13.6 %) were book answers even
though 996 fresh middlegame FENs entered the position pool — a game search from startpos or an early R board
hits the book; a `go depth` never does.

## what I did NOT do
- Did not test middlegame positions for book hits (only startpos). A book is an opening book, so startpos is the
  strongest test, but "0 book lines in the middlegame" is not something I measured here.
- Did not measure the SIZE of the book or which openings it knows.

## times
see the `date -u` line in the commit; `out/meta.json` holds the exe, sha256 and start time.
