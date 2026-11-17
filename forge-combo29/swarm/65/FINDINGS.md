# FINDINGS.md — the Forge opening book, read and measured

**Base: `6b98f217`** ("Checkpoint standalone NNUE v3 work and evidence"), pin
`bench 11` = 312866. Every result below was re-verified on a build of that commit;
provenance and the re-verification table are in **`BASE.md`**. Line numbers are
for `6b98f217` — the book emit is at `src/uci.cpp:539-540`, not the `385-386` an
earlier revision cited from a different tree.

Engine built with `cmake -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=native
-DCMAKE_CXX_COMPILER=/usr/bin/g++` and
`LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`, g++ 13.3.0.

Reproduce everything:

```bash
cd forge-combo29
bash swarm/65/scripts/reverify_6b98f217.sh   # builds the base, checks the pin, re-verifies the findings
bash swarm/65/scripts/run_all.sh             # the full audit
```

Every number below has a named command and a file in `swarm/65/evidence/`.

---

## 0. Where the book is, in one paragraph

The book is compiled into the binary as 2616 Polyglot-format entries
(`src/book_data.inc`, included by `src/book.cpp:9`). It is loaded once at UCI
startup (`src/uci.cpp:155-156`) into a `forge::book::Book` that holds a
key-sorted `std::vector<Entry>`, and can be replaced at runtime by a `.bin` file
(`src/uci.cpp:310-326` → `book.load_file`, `src/book.cpp:100-119`). It is
consulted in exactly one place, the `go` handler (`src/uci.cpp:527-542`), and
nowhere in the search. The key is the Polyglot Zobrist key
(`polyglot_key`, `src/book.cpp:38-62`), a `lower_bound` on the sorted key
(`src/book.cpp:142-154`). Priority against a real search is absolute: when the
gate passes and a book move decodes, the handler prints two lines and `continue`s
(`src/uci.cpp:541`), so no search is ever started. There is no fallback from the
book into search and no scoring of the book move.

---

## 1. Where the book is loaded, where it is consulted, what the key is, priority against search

### 1.1 Load sites

| what | where | notes |
| --- | --- | --- |
| embedded data → memory, once | `src/uci.cpp:155-156` | `book.load_embedded()` |
| format read of the embedded table | `src/book.cpp:121-131` | `Entry{BookKeys[i], BookMoves[i], BookWeights[i], 0}` |
| external `.bin` → memory | `src/book.cpp:100-119` | 16 bytes per entry, big-endian, Polyglot layout |
| sort invariant the lookup needs | `src/book.cpp:135` | `stable_sort` by key, on load |
| reload embedded after a file was loaded | `src/uci.cpp:315-317` | `Book File` set to empty or `<empty>` |
| failed file load keeps the old book | `src/uci.cpp:322-325` | prints `cannot load book`, book untouched |

`OwnBook` defaults to *on* whenever a book is compiled in
(`src/uci.cpp:157`, advertised at `src/uci.cpp:205`), so the book is live unless
something turns it off.

### 1.2 The single consult site

```525:542:forge-combo29/src/uci.cpp
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
4. `game_ply(board) < book_depth` — the ply count is derived from whatever
   `position` supplied, plus the moves it appended; see §5.3.

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

`src/search.cpp:2251-2268` has a drawn-root bail: if the root is a repetition, has
a halfmove clock ≥ 100, or is insufficient material, the search returns without
searching, emitting `info depth 1..64` with `score cp 0` and an **empty pv**. That
empty pv plus `cp 0` is the only in-band signal that the root is drawn.

The book check is at `src/uci.cpp:527`, before the search is entered, so on a
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

#### 4.1.1 Which variable actually decides it: the entry, not the condition

The three-root result above mixes two variables, so the matrix was widened to all
three drawn conditions crossed with book-entry presence, each with the book on and
off (`evidence/drawn_conditions.txt`, `q9_drawn_conditions.py`). Every root was
validated with python-chess first; a correct drawn-root answer is defined as *no
book line, at least one `info depth` line, `score cp 0`, empty `pv`*.

| root | condition | in book | OwnBook | book fired | info depth | score | pv empty |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| fifty-move, book position | halfmove≥100 | yes | true | **YES** | 0 | none | – |
| fifty-move, book position | halfmove≥100 | yes | false | no | 64 | 0 | yes |
| fifty-move, non-book position | halfmove≥100 | no | true | no | 64 | 0 | yes |
| fifty-move, non-book position | halfmove≥100 | no | false | no | 64 | 0 | yes |
| insufficient material | insufficient | no | true | no | 64 | 0 | yes |
| insufficient material | insufficient | no | false | no | 64 | 0 | yes |
| insufficient + fifty-move | both | no | true | no | 64 | 0 | yes |
| insufficient + fifty-move | both | no | false | no | 64 | 0 | yes |
| repetition, book position | repetition | yes | true | **YES** | 0 | none | – |
| repetition, book position | repetition | yes | false | no | 64 | 0 | yes |
| repetition, non-book position | repetition | no | true | no | 64 | 0 | yes |
| repetition, non-book position | repetition | no | false | no | 64 | 0 | yes |

Both questions answered directly:

* **Does the pre-emption happen with the book off?** **No. 0/6.** With
  `OwnBook false` every drawn root, under all three conditions, produced the full
  bail answer: 64 `info depth` lines, `score cp 0`, empty pv. The drawn-root
  detection is sound and complete on its own; the book is the only thing that
  hides it.
* **Does it depend on which drawn condition is present?** **No. 2/2 with a book
  entry, 0/4 without.** Halfmove-100 and repetition are pre-empted; insufficient
  material never is, only because no book position can be insufficient material.
  The deciding variable is **whether the position has a book entry**, not which
  condition fired. That also means the risk is not limited to two conditions: any
  drawn condition added later inherits the hazard automatically wherever the book
  has an entry.
* Every non-book drawn root still answers correctly: 6/6 correct on the book-off
  arm, and the 4 non-book roots are correct on the book-on arm too.

The practical consequence is sharper than "2 of 3". Because pre-emption follows
the book entry, it fires exactly on the positions most likely to appear in a real
game — the ones the book was written for.

#### 4.1.2 The fix, measured

A one-hunk patch that makes the book gate refuse a drawn root is in
`patches/trap2-drawn-root-before-book.patch`, written up in **`TRAP2_PATCH.md`**.
Summary of the measurement (details and tables there):

| | lock | patched |
| --- | --- | --- |
| entry-bearing drawn roots pre-empted | 2/2 | **0/2** |
| non-entry drawn roots answered correctly | 4/4 | 4/4 |
| ordinary book position still books | yes | yes |
| the 11 documented bench/perft pins | match | **identical** |

The patch is search-neutral by construction — it adds a predicate to the book
gate in `uci.cpp` and does not touch `search.cpp` — and that was verified rather
than assumed: LOCK.md's five bench depths at both net settings plus perft 5 all
reproduce on both builds. Traps 1 and 3 are unchanged by it.

### 4.2 MultiPV is ignored on the book path

`evidence/interactions.txt` block B: `MultiPV 2` and `MultiPV 3` both give the
two-line Shape A, with no `multipv` field anywhere. A GUI in MultiPV mode that
expects N ranked lines and waits for `multipv N` will not get them, and will also
not get any line at all. Off-book with `MultiPV 3` and the book off, the same
position returns 34 `info depth` lines, 12 of them carrying `multipv 1` and 11
carrying `multipv 3`.

### 4.3 The clock: the gate reads the *mover's own* clock

This is the important correction to the audit's own framing. `limits.time_ms` is
filled only from the side to move's clock (`src/uci.cpp:121-122`), so
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

#### 4.3.1 The consequence is worse than "does not book": no time limit at all

The same root cause has a second effect that matters more. `limits.time_ms` staying
`-1` does not only fail the book gate — it leaves the search with **no budget**. A
harness that sends only the opponent's clock and waits for `bestmove` hangs.

Measured on a book position, white to move, `go btime 10000 binc 100`
(`evidence/trap1-effect.txt`): no `bestmove` after **25 s**, 22–33 `info depth`
lines and climbing, answering only when an explicit `stop` is sent. On a
**no-book** position it is the same — no answer in 25 s — which confirms the cause
is the missing time limit rather than the book gate.

This is the case where the two halves of the bug have to be separated: on a book
position the patch makes it answer in 0.0 s (through the book gate), which by
itself does *not* prove the search is bounded. The no-book position is the test
that proves it: **0.33 s on the patched build versus unbounded on the lock**, matching
the both-clocks control at 0.35 s.

The fix is written up in **`TRAP1_PATCH.md`**: record both clocks, prefer the
mover's, fall back to the opponent's. All 11 documented pins are identical on both
builds, traps 2 and 3 are unchanged by it, and it composes with the trap-2 patch
(`evidence/trap1-combined.txt`).

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

### 5.3 The `Book Depth` derivation: a claim I made, then retracted

**Retraction.** An earlier revision of this document called the `Book Depth`
derivation a defect: "whether the book fires depends on metadata rather than
chess". That was wrong. It is retracted here with the measurements that
overturned it, because the correction is worth more than the original claim.

What the code does (`src/uci.cpp:140-142`):

```140:142:forge-combo29/src/uci.cpp
int game_ply(const forge::Board& board) {
    return 2 * (board.fullmove_number() - 1) + (board.side_to_move() == forge::Black ? 1 : 0);
}
```

It reads the fullmove counter. The part I missed is that it is evaluated on the
board **after** `position` has applied its moves, and `Board::make_move`
increments that counter. So the expression is not "the FEN's counter" — it is

```
(ply implied by whatever `position` supplied) + (moves that command appended)
```

which is the total ply count, whenever the input was internally consistent.

#### 5.3.1 The original observation, re-read

The observation that started this was real (`evidence/gates_rng.txt` block A):

| FEN fullmove | `game_ply` | Book Depth 40 | Book Depth 41 |
| ---: | ---: | --- | --- |
| 1 | 0 | e2e4 (book) | c2c4 (book) |
| 21 | 40 | e2e4 (**search**) | e2e4 (book) |

My reading was "same position, different metadata, different behaviour". The
correct reading is that these are **not the same input**: fullmove 21 asserts that
40 plies have already been played. A FEN carries no history, so that assertion is
the only record of depth the caller sent. Honouring it is the engine doing what it
was told; ignoring it would mean guessing that the caller was mistaken.

#### 5.3.2 Four derivations, fourteen cases

Every `position` form crossed with both counter directions, each judged against
the ply the caller's own input implies (`evidence/game_ply_derivations.txt`,
`q8c_derivation_compare.py`). Four builds: the lock, plus three candidates —
`history_size()-1` (NAIVE), that with a counter fallback (HYBRID), and a
recorded-at-`position`-time base ply (BASEPLY).

| case | form | input implies ply | Book Depth | expected | LOCK | NAIVE | HYBRID | BASEPLY |
| --- | --- | ---: | ---: | --- | --- | --- | --- | --- |
| A1 | `startpos moves` | 6 | 7 | book | book | book | book | book |
| A2 | `startpos moves` | 6 | 6 | no book | no book | no book | no book | no book |
| A3 | `startpos moves` | 2 | 3 | book | book | book | book | book |
| A4 | `startpos moves` | 2 | 2 | no book | no book | no book | no book | no book |
| B1 | `fen` + `moves` | 6 | 7 | book | book | book | book | book |
| B2 | `fen` + `moves` | 6 | 6 | no book | no book | **book** | **book** | no book |
| B3 | `fen` + `moves` (counter +2) | 8 | 7 | no book | no book | **book** | **book** | no book |
| B4 | `fen` + `moves` (counter +2) | 8 | 9 | book | book | book | book | book |
| B5 | `fen` + `moves` (counter −2) | 4 | 3 | no book | no book | no book | no book | no book |
| B6 | `fen` + `moves` (counter −2) | 4 | 5 | book | book | book | book | book |
| C1 | bare `fen` | 2 | 3 | book | book | book | book | book |
| C2 | bare `fen` | 2 | 2 | no book | no book | **book** | no book | no book |
| C3 | bare `fen` (counter +2) | 4 | 3 | no book | no book | **book** | no book | no book |
| C4 | bare `fen` (counter +2) | 4 | 5 | book | book | book | book | book |

```
LOCK     wrong: 0/14
NAIVE    wrong: 4/14
HYBRID   wrong: 2/14
BASEPLY  wrong: 0/14
```

**The lock is correct on all 14 cases.** Both single-line "fixes" are strictly
worse, and they fail in the direction that matters for a GUI: NAIVE counts only
the moves appended after the FEN, so it under-reports the depth of any resumed
game and lets the book run in positions that are legitimately past `Book Depth`
(B2, B3, C2, C3). HYBRID fixes the bare-FEN case and still gets B2 and B3 wrong.
BASEPLY is also correct, but it is a five-part refactor of `apply_position` that
buys nothing the lock does not already do.

So the honest statement is: **the `Book Depth` gate has no defect.** The
dependence on the FEN counter is an information limit, not a bug — a FEN contains
no move history, so the counter is the only depth information that exists, and
no derivation can recover a ply count the caller never sent. The gate is exact
whenever the input is internally consistent, which is every form the engine
generates itself.

The residual caveat, stated as a caveat and not a defect: a caller that sends a
FEN whose counter does not match the game it came from will get a `Book Depth`
decision based on the counter. That is the caller's input being wrong, and the
engine has no way to detect it.

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
(`src/uci.cpp:161-162`). Two consequences worth stating separately:

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
| 1 | Clock gate reads only the mover's clock, so `go btime` with White to move does not book **and the search has no time limit at all** | **high** — an asymmetric harness hangs; patched and measured in `TRAP1_PATCH.md` | `src/uci.cpp:525`, `121-122` |
| 2 | Book pre-empts the drawn-root bail wherever the position has a book entry (2/2 entry-bearing roots; 0/4 without), removing the `score cp 0` / empty-pv signal | medium — callers lose the only in-band draw signal, and it fires on exactly the positions the book targets; patched and measured in `TRAP2_PATCH.md` | `src/uci.cpp:527` vs `src/search.cpp:2251` |
| 3 | Book move carries no score at all | low — by convention, but it is the reason §4.1 is silent | `src/uci.cpp:539-540` |
| 4 | Default `Book Variety 30` makes the default book nondeterministic, within and across processes | low — intended feature, surprising default | `src/uci.cpp:160`, `src/book.cpp:160-179` |
| 5 | MultiPV mode gets no `multipv` lines on the book path | low | `src/uci.cpp:539-540` |
| 6 | Book data itself | **none** — 2520/2520 legal, 0 material losses, 2230/2230 keys covered | — |
| — | ~~`Book Depth` derivation depends on metadata~~ | **RETRACTED** — the lock is correct 14/14; both candidate fixes are worse. See §5.3. | — |

## 9. Fix arithmetic, for the owner

None of this is applied — this seat measures. Every number below comes from a
built binary, not an estimate.

**Defect 1 (clock gate, and the unbounded search).** Patch written and measured:
`patches/trap1-clock-gate-both-clocks.patch`, full write-up in **`TRAP1_PATCH.md`**,
evidence in `evidence/trap1-*`. Both clocks are recorded and the budget resolved at
the end of `parse_limits`: the mover's clock if given, else the opponent's.
Result: both colours book from whichever single clock is supplied, the asymmetry is
gone, and — the part that matters — an unbounded search becomes bounded.
Measured on a **no-book** position so only the time manager can answer:
**25.00 s with no answer on the lock, 0.33 s on the patched build**, against a
both-clocks control of 0.35 s. All 11 documented pins identical on both builds.
Traps 2 and 3 unchanged by it, and it composes with the trap-2 patch
(`evidence/trap1-combined.txt`).

**Defect 2 (drawn-root pre-emption).** Patch written and measured:
`patches/trap2-drawn-root-before-book.patch`, full write-up in **`TRAP2_PATCH.md`**,
evidence in `evidence/trap2-*`. It is a one-hunk predicate in the book gate
(`!root_drawn`) rather than a reordering, so `search.cpp` is untouched.
Result: pre-emption goes from **2/2 to 0/2** entry-bearing drawn roots, the four
non-entry roots are unchanged, an ordinary book position still books, and all
**11** documented bench/perft pins are identical on both builds. Not merged — the
engine tree is untouched, and `TRAP2_PATCH.md` names the two decisions the owner
should make first (whether a drawn root should ever book, and whether to share the
predicate with `search.cpp`).

**Retracted: the `Book Depth` derivation needs no fix.** Four derivations over
fourteen cases (`evidence/game_ply_derivations.txt`): LOCK 0/14 wrong,
BASEPLY 0/14, HYBRID 2/14, NAIVE 4/14. The lock's counter expression, evaluated
after `position` has applied its moves, equals the total ply count, and a FEN
carries no history for any derivation to draw on. Applying either candidate would
be a regression: NAIVE makes the book fire in resumed games that are legitimately
past `Book Depth`.
