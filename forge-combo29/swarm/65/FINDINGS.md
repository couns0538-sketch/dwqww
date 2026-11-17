# FINDINGS.md — the Forge opening book, read and measured

Scope: `forge-combo29/` at `origin/integrate/combo29-all`. Engine built with
`cmake -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=native`, g++ 13.3.0.

Reproduce everything:

```bash
cd forge-combo29
bash swarm/65/scripts/run_all.sh        # ~4 minutes, writes swarm/65/evidence/
```

Every number below has a named command and a file in `swarm/65/evidence/`.

---

## 0. Where the book is, in one paragraph

The book is compiled into the binary as 2616 Polyglot-format entries
(`src/book_data.inc`, included by `src/book.cpp:9`). It is loaded once at UCI
startup (`src/uci.cpp:141-142`) into a `forge::book::Book` that holds a
key-sorted `std::vector<Entry>`, and can be replaced at runtime by a `.bin` file
(`src/uci.cpp:260-276` → `book.load_file`, `src/book.cpp:100-119`). It is
consulted in exactly one place, the `go` handler (`src/uci.cpp:373-388`), and
nowhere in the search. The key is the Polyglot Zobrist key
(`polyglot_key`, `src/book.cpp:38-62`), a `lower_bound` on the sorted key
(`src/book.cpp:142-154`). Priority against a real search is absolute: when the
gate passes and a book move decodes, the handler prints two lines and `continue`s
(`src/uci.cpp:387`), so no search is ever started. There is no fallback from the
book into search and no scoring of the book move.

---

## 1. Where the book is loaded, where it is consulted, what the key is, priority against search

### 1.1 Load sites

| what | where | notes |
| --- | --- | --- |
| embedded data → memory, once | `src/uci.cpp:141-142` | `book.load_embedded()` |
| format read of the embedded table | `src/book.cpp:121-131` | `Entry{BookKeys[i], BookMoves[i], BookWeights[i], 0}` |
| external `.bin` → memory | `src/book.cpp:100-119` | 16 bytes per entry, big-endian, Polyglot layout |
| sort invariant the lookup needs | `src/book.cpp:135` | `stable_sort` by key, on load |
| reload embedded after a file was loaded | `src/uci.cpp:266-267` | `Book File` set to empty or `<empty>` |
| failed file load keeps the old book | `src/uci.cpp:272-275` | prints `cannot load book`, book untouched |

`OwnBook` defaults to *on* whenever a book is compiled in
(`src/uci.cpp:143`, advertised at `src/uci.cpp:181`), so the book is live unless
something turns it off.

### 1.2 The single consult site

```371:388:forge-combo29/src/uci.cpp
                const bool game_search = (limits.time_ms >= 0 || limits.movetime_ms >= 0) && !limits.infinite &&
                                         !limits.ponder && !limits.search_moves_specified && limits.mate_moves == 0;
                if (game_search && own_book && !book.empty() && game_ply(board) < book_depth) {
                    const forge::Move book_move = book.probe(board, book_variety, book_rng);
                    if (!book_move.is_none()) {
                        std::string prediction;
                        if (ponder_enabled) {
                            forge::Board reply_board = board;
                            forge::Undo undo;
                            (void)reply_board.make_move(book_move, undo);
                            const forge::Move reply = book.probe(reply_board, 0, book_rng);
                            if (!reply.is_none()) prediction = " ponder " + forge::Board::move_to_uci(reply);
                        }
                        const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                        std::cout << "info string book move " << forge::Board::move_to_uci(book_move) << std::endl;
                        std::cout << "bestmove " << forge::Board::move_to_uci(book_move) << prediction << std::endl;
                        continue;
                    }
                }
```

Four conditions, all of which must hold:

1. `game_search` — a clock or `movetime` limit is present, and the search is not
   `infinite`, not `ponder`, not restricted by `searchmoves`, and not a `mate`
   search.
2. `own_book` — the option, default true when a book is embedded.
3. `!book.empty()`.
4. `game_ply(board) < book_depth` — see §5.3, this reads the FEN, not the game.

### 1.3 The key

`polyglot_key` (`src/book.cpp:38-62`) is a faithful Polyglot Zobrist key: piece
codes in Polyglot order (`piece_kind`, `src/book.cpp:26-29`), the four castling
bits at offsets 768-771, the en-passant file at 772-779, side to move at 780.
Verified against an independent implementation: 2429/2429 positions from the walk
and 60/60 randomly generated en-passant positions agree with
`chess.polyglot.zobrist_hash` (`evidence/soundness.txt`,
`evidence/key_conformance.txt`). The en-passant rule is the subtle one — the
engine hashes the ep file only when a pawn of the side to move stands beside the
capturable pawn (`src/book.cpp:53-59`), which is the format's rule, not "an ep
square is present".

`decode_move` (`src/book.cpp:76-96`) turns the 16-bit Polyglot move into a legal
move of the actual board by scanning `board.legal_moves()`, so an entry whose
stored move is not legal in this position is **dropped, not played**
(`src/book.cpp:144-146`). Castling arrives in Polyglot king-takes-rook form and is
rewritten to the king's two-square move at `src/book.cpp:82-91`.

### 1.4 Priority against a real search

Absolute, and it is a `continue`, not a preference. With the gate satisfied and a
decodable move, no search thread is started, no TT is touched, no score exists.
Measured latency difference between the two paths, 200 round trips each
(`evidence/latency.txt`):

| path | p50 | min | max |
| --- | ---: | ---: | ---: |
| book | 0.023 ms | 0.022 ms | 0.369 ms |
| search, 9 plies into a Ruy Lopez | 442 ms | 239 ms | 2646 ms |

(These are the values from the run captured in `evidence/latency.txt`. The book
path's own numbers move by a few tens of microseconds between runs — the
microsecond-scale figure is what matters, not the third digit.)

That is roughly four orders of magnitude, and it is the whole reason the wire
shapes in `BOOK_WIRE.md` are a separate document.

---

## 2. What a book move costs, and why a reader deadlocks

Full treatment and transcripts in `BOOK_WIRE.md`. The load-bearing facts:

* The reply is exactly two lines: `info string book move <uci>` then
  `bestmove <uci>`. Zero `info depth` lines, zero `score`, zero `nodes`.
* A reader that waits for `info depth` before reading anything **times out on
  every book move**. Proved with a passing off-book control
  (`evidence/cost_deadlock.txt`): waiting for `info depth` succeeds off-book and
  fails on-book; waiting for `bestmove` succeeds on both. The script exits 2 if
  the naive reader succeeds on the book, so the claim cannot pass vacuously.
* There is therefore no `info depth` line to deadlock *on* and no line to
  mis-parse: the risk is entirely in the reader's wait condition, not in the
  engine's formatting.

---

## 3. Is the book move scored? What does a GUI display?

**No score is transmitted.** `evidence/score_absence.txt` asserts, and proves the
checker can fail by running the same assertions off-book:

```
field occurrences (BOOK vs NOBOOK):
  score           0     18
  depth           0     36
  nodes           0     18
  nps             0     18
  seldepth        0     18
  hashfull        0     18
  time            0     18
  pv              0     18
BOOK reply carries none of the score-bearing fields: YES
control: the same check fails off-book: YES
BOOK reply is exactly one info string + one bestmove: YES
```

What a GUI displays is therefore not an engine property at all: it keeps whatever
it last showed for that engine, or shows nothing. The engine offers no value to
display and no way to tell "no score yet" from "score is zero", which is precisely
the ambiguity §4 makes dangerous.

---

## 4. Does `OwnBook true` interact with the drawn-root bail, MultiPV, or the clock?

### 4.1 The book pre-empts drawn-root detection — the sharpest finding

`src/search.cpp:1686-1703` has a drawn-root bail: if the root is a repetition, has
a halfmove clock ≥ 100, or is insufficient material, the search returns without
searching, emitting `info depth 1..64` with `score cp 0` and an **empty pv**. That
empty pv plus `cp 0` is the only in-band signal that the root is drawn.

The book check is at `src/uci.cpp:373`, before the search is entered, so on a
drawn root the book answers first and that signal never appears
(`evidence/drawn_root.txt`, `q4c_drawn_root.py`):

| root | OwnBook | book fired | info depth | bestmove | score in last info depth |
| --- | --- | --- | ---: | --- | --- |
| fifty-move rule (halfmove 100) | true | **YES** | 0 | e2e4 | **none** |
| fifty-move rule (halfmove 100) | false | no | 64 | a2a3 | 0 |
| insufficient material (KvK) | true | no | 64 | e2d1 | 0 |
| insufficient material (KvK) | false | no | 64 | e2d1 | 0 |
| threefold repetition history | true | **YES** | 0 | e2e4 | **none** |
| threefold repetition history | false | no | 64 | a2a3 | 0 |

2 of 3 drawn roots are pre-empted. A caller holding a drawn position gets
`bestmove e2e4` with no score and no pv, where the same position with the book off
gets `score cp 0` and an empty pv. Note the direction: this is not "the book plays
a bad move in a drawn position" — it is that **the only signal identifying the
position as drawn is removed**.

KvK is *not* pre-empted, because the book has no entry for it; the drawn-root bail
answers. So the pre-emption is entry-dependent, which makes it harder to notice
than a uniform behaviour.

### 4.2 MultiPV is ignored on the book path

`evidence/interactions.txt` block B: `MultiPV 2` and `MultiPV 3` both give the
two-line Shape A, with no `multipv` field anywhere. A GUI in MultiPV mode that
expects N ranked lines and waits for `multipv N` will not get them, and will also
not get any line at all. Off-book with `MultiPV 3` and the book off, the same
position returns 34 `info depth` lines, 12 of them carrying `multipv 1` and 11
carrying `multipv 3`.

### 4.3 The clock: the gate reads the *mover's own* clock

This is the important correction to the audit's own framing. `limits.time_ms` is
filled only from the side to move's clock (`src/uci.cpp:108-109`), so
`game_search` is really "the mover's clock was given, or movetime was given":

```
$ # White to move, only btime supplied  -> searches
$ printf 'uci\nisready\nposition startpos\nisready\ngo btime 10000 binc 100\n' | ./forge | grep -E 'book move|^bestmove'
bestmove d2d4
$ # White to move, only wtime supplied  -> books
$ printf 'uci\nisready\nposition startpos\nisready\ngo wtime 10000 winc 100\n' | ./forge | grep -E 'book move|^bestmove'
info string book move e2e4
bestmove e2e4
$ # Black to move, only btime supplied  -> books
$ printf 'uci\nisready\nposition startpos moves e2e4\nisready\ngo btime 10000 binc 100\n' | ./forge | grep -E 'book move|^bestmove'
info string book move c7c5
bestmove c7c5
```

So "the clock form reaches the book" is false as stated; only the mover's own
clock does. An asymmetric harness sees the book on one colour and not the other,
which reads as nondeterminism and is not.

Clock *magnitude* is irrelevant: `wtime 0 btime 0 winc 1` and `movetime 0` both
book (`evidence/interactions.txt` block C). The book fires before any time
management is consulted, which is consistent with `continue`.

### 4.4 Forms excluded from the book, with `OwnBook true`

`evidence/interactions.txt` block D: `go depth 6`, `go nodes 50000`,
`go infinite` (+`stop`), `go ... searchmoves e2e3`, `go ... mate 2`, and
`go ... ponder` (+`stop`) all take the search path. The brief named three of these;
`searchmoves` and `mate` are the other two, from the same boolean.

---

## 5. The book boundary, one ply past the last book line

### 5.1 Data boundary

`evidence/boundary.txt`, walking bestmove-vs-bestmove from startpos with
`Book Variety 0`:

| ply | book | info depth | bestmove | wall ms |
| ---: | --- | ---: | --- | ---: |
| 0–15 | YES | 0 | e2e4 … e7g5 | under 1 |
| 16 | **no** | 19 | c1g5 | ~500 |
| 17–23 | no | 19–23 | … | 500–1100 |

The transition is one ply wide, instant → not instant, with the latency jumping
from under 1 ms to about half a second. Nothing in the reply announces the
boundary; the only observable change is the shape.

(The plies after the boundary are clock-driven search: their moves, `info depth`
counts and timings vary between runs, and the values in `evidence/boundary.txt`
will differ from any other run. The *shape* change at ply 16 does not vary, and
that is the claim.)

### 5.2 Gate boundary looks identical

With `Book Depth 4` (`evidence/boundary.txt` block B) the same shape change happens
at ply 4, with ~20 `info depth` lines and a few hundred ms. From the wire alone,
"the book ran out" and "the book was not allowed here" are indistinguishable. Only
the implementation distinguishes them (§1.2 condition 4 vs `candidates()`
returning empty).

### 5.3 The gate reads the FEN's move counter, not the game

```127:129:forge-combo29/src/uci.cpp
int game_ply(const forge::Board& board) {
    return 2 * (board.fullmove_number() - 1) + (board.side_to_move() == forge::Black ? 1 : 0);
}
```

`fullmove_number()` comes from the FEN. The same chess position with different
metadata therefore books or does not (`evidence/gates_rng.txt`, block A):

| FEN fullmove | game_ply | Book Depth 40 | Book Depth 41 |
| ---: | ---: | --- | --- |
| 1 | 0 | e2e4 (book) | c2c4 (book) |
| 21 | 40 | e2e4 (**search**) | e2e4 (book) |

Both FENs are the start position, both validated by python-chess, both legal. The
difference is that a caller reconstructed the position without the original move
number, and `Book Depth` then silently disabled the book. This is a metadata
dependence on whether an opening-book move is played.

---

## 6. Is the book deterministic? Ten fresh processes

`evidence/determinism_v0.txt`, `evidence/determinism_v30.txt`,
`evidence/gates_rng.txt` block B, `q6_determinism.py`, `q4b_gates_and_rng.py`.

| Book Variety | 10 fresh processes | 10 probes in one process |
| --- | --- | --- |
| 0 | 1/10 distinct → e2e4 10/10 | 1/10 distinct → e2e4 10/10 |
| 30 (default) | 2/10 distinct → e2e4 8/10, c2c4 2/10 | 2/10 distinct → e2e4 6/10, c2c4 4/10 |
| 100 | 3/10 distinct → d2d4 4/10, e2e4 4/10, c2c4 2/10 | 3/10 distinct → e2e4 4/10, c2c4 4/10, d2d4 2/10 |

(These are single 10-sample runs and the counts move between runs; the *number of
distinct moves* is the stable result, not the exact split.)

Deterministic **only at variety 0**. The default is 30, so the default book is
nondeterministic by design. The mechanism: `Book::probe` advances a xorshift64\*
state (`src/book.cpp:170-179`) seeded once from `steady_clock` at process start
(`src/uci.cpp:147-148`). Two consequences worth stating separately:

* Across processes, the seed differs, so outcomes differ — that is what the
  brief's "ten fresh processes" question is about, and the answer is no.
* Within one process, the RNG advances per probe, so a repeated identical `go`
  also varies. Even a same-process A/B cannot be compared command-for-command
  with the default variety.

At `Book Variety 0`, `probe` returns `moves.front()` before touching the RNG
(`src/book.cpp:164`), which is why variety 0 is stable in both columns.

The weighted choice itself is correct and biased as intended: at variety 30 the
threshold is `best * 70 / 100` (`src/book.cpp:165`), and startpos weights are
e2e4 100, c2c4 80, d2d4 64, so only e2e4 and c2c4 clear it — which is exactly the
two-value distribution measured. d2d4 never appears at variety 30 and does at
variety 100.

---

## 7. Is any book move illegal or materially losing?

### 7.1 Coverage first

A soundness claim is only worth its coverage. `evidence/coverage.txt`:

```
book entries (BookKeys): 2616
distinct keys in book:   2230
positions reached by walk: 2429 (2230 with book moves, 199 without)
book keys never reached: 0/2230
COVERAGE COMPLETE: the soundness audit spans every book key
```

The walk (`scripts/probe_book.cpp`) starts at startpos, expands every book move
recursively, and reaches all 2230 distinct keys with 2520 distinct (key, move)
pairs and 199 terminal positions just past the last entry. The census
(`evidence/census.txt`) confirms 2616 entries → 2230 keys → 2520 unique
key-move pairs, with 96 exact duplicates (merged, weight-summed at
`src/book.cpp:147-154`), 0 zero-weight entries, 0 promotion-encoded moves, and 0
entries out of key order.

### 7.2 Legality and keys

`evidence/soundness.txt`:

```
positions checked: 2429/2429
book moves checked: 2520
invalid FEN (python-chess): 0/2429
polyglot key mismatch vs chess.polyglot: 0/2429
illegal book moves (python-chess): 0/2520
```

Every book move is legal, judged by python-chess, which is an independent move
generator from `board.cpp`. Nothing is illegal.

Castling is the one encoding hazard: the book stores it as Polyglot
king-takes-rook (`e1h1`, `e8a8`) and `decode_move` must rewrite it before it
reaches UCI (`src/book.cpp:82-91`). 154 of the 2520 book moves are castles — all
kingside, no queenside anywhere in the book. All 154 castle positions were
replayed through the engine with `Book Variety 0`
(`evidence/castles.txt`, `q1b_castles.py`):

```
castle positions exercised through the engine: 154/154
  replies that were book moves: 154/154
  replies that were a castle:   151/154
king-takes-rook strings on the wire: 0/154
illegal or unparseable replies:      0/154
```

Zero king-takes-rook strings reached the wire, and every reply was legal — so the
decode is correct. The three positions that did not castle are cases where the
heaviest book move is something other than the castle, not failures.

### 7.3 Material

Static exchange flags 135 of 2520 moves as "material at risk". **None of them is
an actual defect**, and the reason is worth stating precisely rather than
dismissing the flags wholesale:

* some flags are captures whose recapture is **poisoned** — the swap list assumes
  the opponent recaptures and it loses to be the one who does;
* the rest are quiet moves after which the opponent has a capture the swap list
  scores as winning material, where the engine judges the resulting position
  acceptable anyway. `f1c4` in `rnbqkb1r/pp2pppp/5n2/2pP4/8/2P5/PP1P1PPP/RNBQKBNR w KQkq - 1 4`
  is one: SEE is right that `...Nxd5` wins a pawn, and the engine still scores
  White +31 after it at depth 14, i.e. the pawn is a real concession that buys
  enough. So SEE is measuring material, and the book is occasionally willing to
  give material for development — which is a judgement call, not a bug.

Re-checked with the engine's own search, book off, depth 12, `Clear Hash` between
searches (`evidence/soundness_verified.txt`):

```
SEE-flagged book moves: 135
positions scored: 135 (unscoreable 0)
book moves with gap > 100 cp: 0/135
```

That is the operative result: **no flagged move costs more than 100 cp**, so no
book move loses material in a way the engine regards as losing.

### 7.4 Exhaustive quality gap

`evidence/gap_depth10.txt`, all 2520 book moves, `Clear Hash` between every pair,
`score(unrestricted) - score(searchmoves <book move>)`:

```
book moves scored: 2520 (skipped/unscoreable 0)
max gap: 103 cp
mean gap: 6.87 cp
median gap: 4.0 cp
  gap >  50 cp: 34/2520
  gap > 100 cp: 1/2520
  gap > 150 cp: 0/2520
```

**The outlier is a horizon artifact, not a book defect.** Three reasons, each
measured:

1. The measurement has its own noise: forcing the move the unrestricted search
   itself chose gives `|delta|` up to 66 cp with 6/111 samples above 25 cp
   (`evidence/noise_floor.txt`). So a few tens of cp of gap is not signal.
2. The single 103 cp case (`e8g8` in `r1bqk2r/pppnbppp/3p1n2/4p3/3PPP2/2N2N2/PPP1B1PP/R1BQK2R b KQkq - 4 6`)
   does not survive deeper search: gap 4 → 3 → 27 cp at depths 10 → 14 → 18
   (`evidence/deep_check.txt`).
3. The other nine worst cases collapse the same way — `f8c5` goes 48 → −1 → 5 cp,
   `g8f6` 60 → 20 → 8 cp, `d8a5` −17 → −23 → 11 cp.

So: **no book move is illegal, and none is unsound. The book is clean.** The only
caveats are stylistic (early `d1h5`/`Ng5` lines, a couple of offbeat weights) and
are not defects.

### 7.5 The SEE bug this audit had to fix before it could say any of that

The first SEE implementation in `q7_soundness.py` validated each candidate
recapture against `board.legal_moves` while the board's turn was still the side
that had just moved. chess's `legal_moves` is relative to `turn`, so **every
recapture was rejected as illegal**, the swap list collapsed to a single capture,
and every even trade was reported as a loss. It reported **929/2520** moves as
material-losing; the correct number is 0/2520 by the same criterion after
re-checking. A second bug in the same file clamped the mover's own first capture
at zero, so a genuinely losing capture reported 0 instead of negative.

Both were caught by `see_selftest.py`, which asserts hand-computed values
including a regression case (`exd5` with `Qxd5` available must be 0, not +100) and
a losing capture (`Nxg5` into an f6 pawn must be −220, not 0). The self-test runs
as step 4 of `run_all.sh` and aborts the pipeline on failure, so the soundness
numbers cannot be produced from a broken SEE.

Practical note for anyone writing their own SEE: a *plausible* wrong answer here
is not a near miss, it is a 929-versus-0 reversal that would have been reported as
"37% of the book loses material".

---

## 8. Summary of defects

| # | finding | severity | where |
| --- | --- | --- | --- |
| 1 | Gate uses the mover's own clock, so `go btime` with White to move does not book | medium — harness-visible asymmetry, reads as nondeterminism | `src/uci.cpp:371`, `108-109` |
| 2 | Book pre-empts the drawn-root bail, removing the `score cp 0` / empty-pv signal on 2 of 3 drawn roots | medium — callers lose the only in-band draw signal | `src/uci.cpp:373` vs `src/search.cpp:1686` |
| 3 | `Book Depth` reads the FEN's fullmove counter, so book eligibility depends on metadata | medium — position reconstruction silently disables the book | `src/uci.cpp:127-129` |
| 4 | Book move carries no score at all | low — by convention, but it is the reason §4.1 is silent | `src/uci.cpp:385-386` |
| 5 | Default `Book Variety 30` makes the default book nondeterministic, within and across processes | low — intended feature, surprising default | `src/uci.cpp:146`, `src/book.cpp:160-179` |
| 6 | MultiPV mode gets no `multipv` lines on the book path | low | `src/uci.cpp:385-386` |
| 7 | Book data itself | **none** — 2520/2520 legal, 0 material losses, 2230/2230 keys covered | — |
