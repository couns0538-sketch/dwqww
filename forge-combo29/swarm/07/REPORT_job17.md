# REPORT — seat 07, job 17: book moves in normal play, and an inconclusive first control

## What was asked / the answer / how sure

**Asked:** continue the area-7 read, prioritising what shows in normal play. The UCI loop's book path
is the remaining normal-play surface: the built-in book answers clock and movetime searches by
default (`uci.cpp:525-527`, `OwnBook` default true).

**Answer:** book moves are **always legal**: over a 60-ply self-game where **16 plies were actually
answered by the book**, every book move was legal in the position sent and identical to the
`bestmove` the engine printed. This agrees with the code — `decode_move` maps a book entry by
scanning `board.legal_moves()`, so an illegal book move is impossible by construction.

**How sure:** high for the result, but only after a **second** control. My first planted fault was
inconclusive and I say so below rather than quietly replacing it.

## Honesty numbers

Base build: 312866 / 862329 / 3024920 / 4865609 (job0/raw/summary.txt). No engine source changed.

## Why the book matters for correctness, not just strength

A book move is played **without any search** and printed as `bestmove`. If the book could ever emit an
illegal move, the engine would lose instantly by making an illegal move — and no bench, perft or
sanitizer run would see it, because this path never enters the search at all. That makes it worth a
direct test rather than an inference from the code.

The code path, read (and then checked from outside):

    src/book.cpp:75   Move decode_move(const Board& board, std::uint16_t encoded)
    src/book.cpp:91       for (const Move move : board.legal_moves()) {
    src/book.cpp:92-94        ... match from/to and promotion ...
    src/book.cpp:95           return move;
    src/book.cpp:96       }
    src/book.cpp:97       return Move::none();      // no legal match -> not a book move

## Result

    plies played 60, plies answered by the book 16
    RESULT: every book move was legal and matched the bestmove the engine printed

The test asserts the book was used at least once (`book_plies == 0` is a **failure**, not a pass), so
the run cannot succeed by never touching the book. Transcript: job17/raw/transcript.txt.

## The control, and why I am labelling the first one inconclusive

**Control attempt 1 (inconclusive — do not treat as a pass).** I removed the legality scan and
returned the decoded from/to directly:

    plies played 40, plies answered by the book 16
    RESULT: every book move was legal and matched the bestmove the engine printed

The probe passed against a build with the legality check deleted. The reason is not that the fault was
harmless: the decoded from/to values coming out of the book table happened to be legal moves in these
positions, so the test could not tell the difference. An inconclusive control licenses no conclusion,
so I did not stop there.

**Control attempt 2 (valid).** Fault the decode so it returns a reversed from/to (an illegal move in
almost every position):

    plies played 0, plies answered by the book 0
    FAIL ply 0: bestmove c4c2 illegal in rn1bqkbnr/... w KQkq - 0 1  (startpos)
    RESULT: 1 failure(s)

The probe now fails at the first ply. Note honestly what did the catching: the **`bestmove`** assertion,
not the book-line assertion — with that fault the engine printed no `info string book move` line at
all, so the book assertion never fired. The `bestmove`-legality assertion is therefore the load-bearing
one in this test.

## Findings

**07-C14** in FINDINGS.md — including the inconclusive first control, because a reader who saw only
"clean" would not know how close the test came to being worthless.

## Suspicions, not proven

- `Book File` loading (book.cpp:100-119) reads 16-byte records with no validation of the key; a
  malformed file could produce entries that never match, which is harmless, but I did not test a
  crafted file.
- `book_variety`'s weighted pick (book.cpp:160-180) I did not test for distribution correctness; it
  affects variety, not legality.

## What I did NOT do

- Did not test a custom `Book File` (only the embedded book).
- Did not test the book with `ponder` enabled, where the UCI loop predicts a reply
  (`uci.cpp:530-536`); that prediction is a ponder hint, not a played move.

## What I am NOT sure about

- Whether a book entry can ever decode to a legal move of the *wrong piece* (e.g. from/to matching a
  different legal move with the same squares). Since the scan matches on from/to and promotion
  together, two legal moves cannot share both, so I believe not — but I did not construct a proof case.

## Times

See job17/stamps.txt.
