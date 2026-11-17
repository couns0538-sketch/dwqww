# BOOK_WIRE.md — the exact wire shapes of the Forge opening book

Scope: `forge-combo29/` at `origin/integrate/combo29-all`. All output below was
captured from a build of that tree (`cmake -DFORGE_MARCH=native`, g++ 13.3.0,
`-O3`). Reproduce everything with:

```bash
cd forge-combo29
bash swarm/65/scripts/run_all.sh
```

Evidence files are under `swarm/65/evidence/`.

---

## 1. There are exactly two reply shapes

### Shape A — the book answers

```
info string book move e2e4
bestmove e2e4
```

That is the whole reply. Emitted at `src/uci.cpp:385-386`:

```385:386:forge-combo29/src/uci.cpp
                        std::cout << "info string book move " << forge::Board::move_to_uci(book_move) << std::endl;
                        std::cout << "bestmove " << forge::Board::move_to_uci(book_move) << prediction << std::endl;
```

Properties, all measured (`evidence/cost_deadlock.txt`, `evidence/latency.txt`):

| property | value |
| --- | --- |
| `info depth` lines | **0** |
| `info` lines of any kind | 1 (`info string book move ...`) |
| `score` anywhere in the reply | **none** |
| `nodes` / `nps` / `time` fields | **none** |
| wall time `go` → `bestmove` | p50 **~0.02 ms**, max **< 0.5 ms** over 200 round trips (`evidence/latency.txt`: p50 0.023 ms, max 0.369 ms) |
| round trips under 1 ms | **200/200** |

### Shape B — the search answers

```
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
...
info depth 10 seldepth 14 score cp 24 nodes 13102 ... pv d2d4 e7e6 ...
bestmove d2d4
```

Shape B always has at least one `info depth` line carrying `score`. Shape A never
does. There is no third shape and no hybrid: the book path `continue`s past the
whole search-and-report block (`src/uci.cpp:387`).

---

## 2. Reading Shape A correctly

### 2.1 Waiting for `info depth` deadlocks

Proved, not asserted (`evidence/cost_deadlock.txt`, `q2_cost_and_deadlock.py`):

```
--- naive reader: waits for `info depth`, 2 s timeout ---
BOOK   position: info depth seen before timeout: no
NOBOOK position: info depth seen before timeout: yes
--- naive reader: waits for `bestmove`, 2 s timeout (the correct wait) ---
BOOK   position: bestmove seen: yes
NOBOOK position: bestmove seen: yes
```

The script exits 2 if the naive reader *does* succeed on the book position, or if
the off-book control *fails*. So it cannot pass vacuously. The only correct wait
is `bestmove`.

### 2.2 "No info depth" does not mean "the book fired"

Two different conditions produce a reply with no `info depth` line:

1. the book fired (Shape A);
2. the `position` command was refused and the engine searched something else, or
   the search was cut off before depth 1 could report.

They are distinguishable, but only by reading text, in this order:

* **`info string book move <move>` is present** → the book fired. This string is
  emitted only on the book path and nowhere else in the engine.
* **`invalid FEN` in the position reply or in the `go` reply** → the FEN was
  refused. Per the corrected rule in the audit brief, the diagnostic's location
  depends on whether `isready` follows `position`:

```
# with isready after position: lands in the POSITION reply, before readyok
$ printf 'uci\nisready\nposition fen nonsense w - - 0 1\nisready\ngo movetime 60\n' | ./forge | tail -4
uciok
readyok
info string invalid FEN: invalid FEN placement
readyok
info string book move c2c4

# without isready: lands in the go output, ahead of everything else
$ printf 'uci\nposition fen nonsense w - - 0 1\ngo movetime 60\n' | ./forge | tail -3
uciok
info string invalid FEN: invalid FEN placement
info string book move e2e4
```

Both windows must be scanned. In the first transcript the refusal is followed by
a **book move**, because a refused FEN leaves the previous board in place and the
previous board was startpos. A probe that only looked at the `go` reply would see
Shape A and conclude the book answered the position it was asked about. It did
not.

### 2.3 The book move is never scored

No score is transmitted. What a GUI shows is therefore entirely the GUI's own
behaviour, and the honest statement is: the engine sends no score for a book move,
so the GUI keeps whatever it last displayed or shows nothing. There is no
`info depth 1 score cp 0` synthesis, no `score cp` on the `bestmove` line, and no
`info string score` line. The strings that do appear on the line are exactly:

```
info string book move <uci>
```

with `<uci>` in the engine's own move string form (`src/board.cpp:1156-1166`):
from-square, to-square, and a promotion letter `n`/`b`/`r`/`q` when the move
promotes. Castling is emitted as the king's two-square move (`e1g1`, `e8c8`),
never in the Polyglot king-takes-rook encoding the book stores. The string is
produced by one emit site in the whole engine (`src/uci.cpp:385`), so the literal
`info string book move ` cannot appear from anywhere else.

The promotion branch of that formatter is unreachable from the embedded book:
`evidence/census.txt` reports `promotion_encoded 0`, and no book move in
`evidence/book_walk.tsv` carries a promotion letter. So the only two shapes a
book `bestmove` can take in this build are a normal move and a king-move
castling.

### 2.4 The `ponder` suffix on a book move comes from the book

When `Ponder` is true, the `bestmove` line gains a `ponder` field whose move is
looked up in the **book**, not produced by a search (`src/uci.cpp:376-383`):

```
info string book move c2c4
bestmove c2c4 ponder e7e5
```

If the booked reply has no book entry of its own, the suffix is omitted and the
line is plain `bestmove c2c4` — so the *presence* of `ponder` on a book move
depends on book coverage one ply deeper, not on whether pondering is enabled.
Measured (`evidence/interactions.txt`, block F).

---

## 3. Which `go` forms reach Shape A

`evidence/go_matrix.txt`, `q1_go_matrix.py`. Two positions: BOOK = startpos,
NOBOOK = a Ruy Lopez position with no book entry. Both validated with python-chess
before use.

| position | go form | book fired | info depth lines | bestmove | invalid FEN |
| --- | --- | --- | ---: | --- | --- |
| BOOK | `go wtime 10000 btime 10000` | **YES** | 0 | c2c4 | no |
| BOOK | `go movetime 100` | **YES** | 0 | c2c4 | no |
| BOOK | `go depth 6` | no | 6 | d2d4 | no |
| BOOK | `go nodes 50000` | no | 11 | d2d4 | no |
| BOOK | `go infinite` (+ `stop`) | no | 16 | e2e4 | no |
| NOBOOK | `go wtime 10000 btime 10000` | no | 18 | a4c6 | no |
| NOBOOK | `go movetime 100` | no | 15 | a4c6 | no |
| NOBOOK | `go depth 6` | no | 6 | a4c6 | no |
| NOBOOK | `go nodes 50000` | no | 11 | a4c6 | no |
| NOBOOK | `go infinite` (+ `stop`) | no | 18 | a4c6 | no |

The five-way split in the brief reproduces exactly. The cause is one boolean at
`src/uci.cpp:371-372`:

```371:372:forge-combo29/src/uci.cpp
                const bool game_search = (limits.time_ms >= 0 || limits.movetime_ms >= 0) && !limits.infinite &&
                                         !limits.ponder && !limits.search_moves_specified && limits.mate_moves == 0;
```

`depth`, `nodes` and `infinite` never set `time_ms`/`movetime_ms`, so they can
never be `game_search`. `searchmoves` and `mate` also exclude the book, which the
brief did not mention.

### 3.1 A sixth exclusion the brief did not have: the wrong clock

`limits.time_ms` is populated only from **the side to move's** clock
(`src/uci.cpp:108-109`):

```108:109:forge-combo29/src/uci.cpp
        else if (token == "wtime") { const std::int64_t value = read_clock(); if (side == forge::White) limits.time_ms = value; }
        else if (token == "btime") { const std::int64_t value = read_clock(); if (side == forge::Black) limits.time_ms = value; }
```

So "the clock form" is really **"the mover's own clock"**, and a `go` that carries
only the opponent's clock does not reach the book:

```
$ # white to move, only btime given
$ printf 'uci\nisready\nposition startpos\nisready\ngo btime 10000 binc 100\n' | ./forge | grep -E 'book move|^bestmove'
bestmove d2d4
$ # white to move, only wtime given
$ printf 'uci\nisready\nposition startpos\nisready\ngo wtime 10000 winc 100\n' | ./forge | grep -E 'book move|^bestmove'
info string book move e2e4
bestmove e2e4
$ # black to move, only btime given
$ printf 'uci\nisready\nposition startpos moves e2e4\nisready\ngo btime 10000 binc 100\n' | ./forge | grep -E 'book move|^bestmove'
info string book move c7c5
bestmove c7c5
$ # black to move, only wtime given
$ printf 'uci\nisready\nposition startpos moves e2e4\nisready\ngo wtime 10000 winc 100\n' | ./forge | grep -E 'book move|^bestmove'
bestmove c7c5
```

An asymmetric harness that sends only the opponent's clock will therefore see the
book on one colour and not the other, which reads exactly like nondeterminism.

---

## 4. Reply shapes for every option that changes them

`evidence/interactions.txt` (`q4_interactions.py`). One process per row, so no
option leaks between rows.

| case | book | info depth | bestmove |
| --- | --- | ---: | --- |
| MultiPV 1, clock | YES | 0 | e2e4 |
| MultiPV 2, clock | YES | 0 | c2c4 |
| MultiPV 3, clock | YES | 0 | e2e4 |
| MultiPV 3, book OFF, movetime 100 | no | 32 | e2e4 |
| wtime 0 btime 0 winc 1 binc 1 | YES | 0 | e2e4 |
| movetime 0 | YES | 0 | e2e4 |
| movetime 0, book OFF | no | 5 | c2c4 |
| halfmove-clock-100 drawn root, book ON | YES | 0 | e2e4 |
| halfmove-clock-100 drawn root, book OFF | no | 64 | a2a3 |
| KvK insufficient material, book ON | no | 64 | e2d1 |
| checkmated root, book ON | no | 64 | 0000 |
| Book Depth 0, clock | no | 18 | e2e4 |
| Book Depth 1, clock, ply 0 | YES | 0 | e2e4 |
| Book Depth 1, clock, ply 1 | no | 19 | c7c5 |
| Book Depth 2, clock, ply 1 | YES | 0 | c7c5 |

Two shapes there are worth calling out to any harness author:

* **MultiPV has no effect on Shape A.** With `MultiPV 3` the book reply is still
  two lines and carries no `multipv` field at all, so a reader that expects
  `multipv 1..N` lines after `setoption name MultiPV value 3` will find none.
* **`movetime 0` still books** but `movetime 0` off-book still runs a search and
  returns 5 `info depth` lines. Zero time is not "no search" here.

The drawn-root bail does **not** pre-empt the book: a startpos with a 100-ply
halfmove clock emits `book move e2e4`, while the same FEN with the book off takes
the drawn-root branch and emits 64 `info depth` lines with `score cp 0` and an
empty `pv`. The book check is earlier in the `go` handler than the search is
entered, so the book wins.

---

## 5. The transition at a book boundary

`evidence/boundary.txt` (`q5_boundary.py`), walking bestmove-vs-bestmove from
startpos with `Book Variety 0`.

| ply | book | info depth | bestmove |
| ---: | --- | ---: | --- |
| 0–15 | YES | 0 | e2e4, c7c5, c2c3, e7e5, g1f3, b8c6, f1c4, g8f6, f3g5, d7d5, e4d5, f6d5, d2d3, f8e7, d1h5, e7g5 |
| 16 | **no** | ~19 | c1g5 |
| 17–23 | no | 19–23 | … |

The transition is exactly one reply wide: ply 15 is Shape A, ply 16 is Shape B,
nothing in between, and ply 16 arrives after roughly half a second instead of
~0.02 ms. A reader that assumes "the first N plies are instant" will under-read
its timeout at the boundary by three orders of magnitude.

The `info depth` counts and timings past ply 16 are clock-driven and differ
between runs; the shape change and its position do not. The book line itself
(plies 0–15) is fixed by `Book Variety 0` and reproduces exactly.

`Book Depth` produces the identical wire change at a chosen ply (`boundary.txt`
block B, gate at ply 4), and the two are indistinguishable from the reply alone.
Only the cause differs: no entry vs. not allowed.

---

## 6. Summary table for harness authors

| question | answer |
| --- | --- |
| How do I know the book fired? | the literal substring `info string book move ` in the reply |
| How do I know it did not? | absence of that substring — but also scan for `invalid FEN` in *both* the position and go windows |
| Does `go btime 10000` reach the book? | Only for Black. The gate reads the mover's own clock, so with White to move it searches. |
| May I wait for `info depth`? | **No.** Wait for `bestmove` with a timeout. |
| Is the book move scored? | No. No score, no nodes, no depth, no pv. |
| Does the book override a drawn root? | **Yes.** On a fifty-move or repetition root it plays a book move instead of reporting `score cp 0` with an empty pv. |
| Does MultiPV change the reply? | No. |
| Does Ponder change it? | Yes: a `ponder <move>` suffix taken from the book. |
| Is the book deterministic? | Only at `Book Variety 0`. The default is 30. |
| How fast? | p50 ~0.02 ms, max under 0.5 ms, all 200 under 1 ms (`evidence/latency.txt`) |
| What timeout is safe? | Any timeout above a few ms works for the book; the *boundary* reply can take a second or more, so do not shrink the timeout to fit the book path. |
| Is any book move illegal? | No. 2520/2520 legal, 154 castles all kingside, 0 king-takes-rook strings on the wire. |
