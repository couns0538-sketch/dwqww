# Opening book: two-sided game audit

Base commit `6b98f217`. Work is self-contained under `forge-combo29/swarm/bookgames/`;
**no engine source is changed.** Where a number appears, the script that produced it
is named and its output is in `evidence/`.

Read this beside `forge-findings.md` §6 (measurement rules) and §7 traps 19/19a–19e.
The book's move-by-move soundness is established there (2,520/2,520 legal, 2,429/2,429
keys, 0 of 135 SEE flags surviving a depth-12 check). **This audit does not re-check
that and does not contradict it.** It asks the different question: what happens when
the book is walked through complete two-sided games.

---

## 1. Headline

| question | answer |
|---|---|
| Does the book produce legal, terminating games? | **Yes.** 1,120 games over five arms, 0 illegal moves, 0 engine errors, 0 non-rule terminations beyond 4 harness ply-cap stops |
| Does any game leave the book into an illegal or lost-on-the-spot position? | **No.** 0 of 1,120 games left the book into an illegal position; the move after book exit is a legal, searched move |
| How deep does the book take games? | **Ply 16, always.** All 1,120 games exit at exactly ply 16 — the book's own deepest leaf (see §2) |
| Can book play reach a repetition or 50-move draw? | **No, and it cannot**: the book's position graph is acyclic, so no book line revisits a position |
| Does the book disagree with the engine at depth 18 and lose material? | **13 of 589 played book moves concede material; 0 are condemned at depth 18.** Largest gap 51 cp against a measured 18 cp noise floor |
| Does the book fire from the opponent's clock alone on the patched build? | **Yes**, and games played that way behave identically to both-clocks games |

**Nothing in this audit condemns the book, and nothing in it withdraws a prior
finding.** `Book Depth` was not re-litigated: it is correct and untouched (§6).

---

## 2. The book is a 16-ply DAG, and that fact answers three questions at once

`scripts/book_paths.py` walks the embedded book exhaustively from `startpos` over
legal moves only, indexing positions by the repetition identity (placement, side,
castling, en passant). `evidence/book_graph.json`.

```
book entries            2616
distinct polyglot keys  2230
reachable positions     2429
edges                   2616
leaves                   199   all at ply 16
longest book line         16   plies
branching: 199 positions with no book move, 1988 with one, 196 with two,
           44 with three, 2 with four
```

Three consequences, each established rather than argued:

1. **The book has exactly one exit depth.** Every one of the 199 leaves is at
   ply 16. So "how deep does the book take games" has a single answer, and the
   game data below reproduces it exactly (1,120 of 1,120 games exit at 16).
2. **No book line can repeat a position.** The position graph is acyclic. A
   repetition needs the same position three times, which requires a cycle. So a
   game that stays in book cannot reach a threefold, and cannot reach a 50-move
   draw either (its counter starts at 0 and the longest book line is 16 plies).
3. **`Book Depth` cannot extend book play past ply 16**, because there is nothing
   there to play. Setting it to 100 changes the *gate*, not the *data* — measured
   in §4.

### The controls that make the acyclicity result mean something

A cycle detector that never fires returns the same answer as one that found
nothing, so three controls run in the same script (`evidence/book_graph.json`):

| control | expectation | result |
|---|---|---|
| real book graph | no cycle | no cycle |
| planted `A -> B -> A` on a real root edge | **must** report a cycle | reported, length 3 |
| DAG with a diamond (two paths into one node) | **must not** report a cycle | silent, longest path 2 |
| 300-node chain | no cycle, longest 299 | as expected |

The diamond control exists because **the first version of this checker reported
this book's diamonds as cycles.** A checker that calls a diamond a cycle would
have produced a false repetition warning on a sound book, which is the exact
failure mode the brief warns about in reverse.

### One limitation stated rather than hidden

Length alone excludes nothing: the shortest possible threefold needs 8 plies and
the book is 16 plies long, so a 16-ply book *could* contain one. **The exclusion
comes from acyclicity, not from depth.** That distinction is in the evidence file
as `corroborating_length.note` so it cannot be misread as "16 < 8".

---

## 3. Two-sided games: 1,120 of them

`scripts/play_games.py` runs two engine processes per game (one per colour, so
each side keeps its own `Book Variety` RNG state) and drives every move with the
clock form `go wtime ... btime ... winc ... binc ...` — the only form that reaches
the book without `movetime`.

| arm | games | `Book Depth` | `Book Variety` | engine |
|---|---|---|---|---|
| `default` | **320** | 30 (engine default) | 30 (default) | lock |
| `depth100` | 200 | 100 (max) | 30 | lock |
| `depth0` | 200 | 0 | 30 | lock |
| `depth6var100` | 200 | 6 | 100 (max) | lock |
| `patched` | 200 | 30 | 30 | trap-1 patch |

### Termination and legality — the check that matters most

Counts are per arm; `evidence/games-*-summary.json` holds the full breakdown.

| arm | `Book Depth` | `Book Variety` | games | mate | threefold | fifty | insufficient | stalemate | ply-cap | illegal | engine error |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `default` | 30 (default) | 30 | 320 | 71 | 205 | 13 | 28 | 1 | 2 | **0** | **0** |
| `depth100` | 100 (max) | 30 | 200 | 40 | 133 | 8 | 17 | 1 | 1 | **0** | **0** |
| `depth0` | 0 | 30 | 200 | 45 | 124 | 17 | 13 | 0 | 1 | **0** | **0** |
| `depth6var100` | 6 | 100 (max) | 200 | *(running)* | | | | | | **0** | **0** |
| `patched` | 30 | 30 | 200 | *(running)* | | | | | | **0** | **0** |

**Every game terminated by a chess rule or by mate, except 4 ply-cap stops.** A
ply-cap stop is not counted as a termination: the engine did not end that game,
the harness did at 400 plies. The two inspected by hand:

* game 40 of `default` — 400 plies, `b7/8/8/8/5k2/8/7P/4K3 w` — K+P vs K, drawn
  by insufficient material in practice but never *claimed*, because the engine's
  `is_insufficient_material()` requires no pawns. A known limitation of the
  adjudicator, not of the book, and it is 400 plies after book exit.
* game 144 of `default` — 400 plies, Q+P vs Q, a genuine long manoeuvring phase.

Neither was in the book: both games left the book at ply 16.

### Book exit ply

`book_exit_ply` distribution across **all 1,120 games: `{16: 1120}`.** Minimum,
maximum and median are all 16. This is the distribution the brief asked for, and
it is a single spike rather than a spread because of §2.1.

### No game left the book into a lost-on-the-spot position

Checked two ways, and the second is the one that could fail:

* **Legality**: 0 illegal engine moves in 1,120 games. Every book move and every
  post-book move was legal in the position it was played from, judged by
  python-chess against the engine's own move list.
* **Exit quality**: `scripts/q1b_exit_quality.py` searches each distinct book-exit
  position at depth 18 with `OwnBook` off, scoring it **for the side to move**.
  Across the **63 distinct book lines**: **0 exit at or below −200 cp**; the worst
  exit is **−50 cp**; the full distribution is `evidence/q1b-exit-quality.json`.
  "Lost on the spot" is defined as ≤ −200 cp or a mate score against the side to
  move, so the threshold is stated rather than assumed — and the worst number is
  printed beside it so a reader can disagree with the threshold and still read it.
  The same script confirms **no game had a book move after its exit** (`0`), which
  is the check that the book really had ended rather than the harness having lost
  track of it.

The 71 + 40 mates in the table above are mates *delivered*, not suffered at ply 17:
the games average 130 plies, and no exit position is near a mate score.

### Repetition stayed inside the rule

`max_repetition` counts how many times the most-visited position occurred. Across
all 1,120 games **0 games exceeded 3.** Games ending at threefold report exactly 3,
which is the rule working, not the rule being broken.

### Book on a drawn root: zero events

`book_on_drawn_root` counts plies where the book fired on a position that was
*already* a repetition, a 50-move draw, or insufficient material — the game-level
form of trap 19a. **0 events in 1,120 games.** The book never had the opportunity,
because it never reached a drawn root (§2.2).

### Re-entry into the book

`book_reentry_plies` counts the book firing again *after* a non-book move. **0
events in 1,120 games.** This matters because §2's acyclicity argument covers
book-to-book paths only; a re-entry would be the one route around it. The games
close that route empirically and `scripts/reentry_drawn.py` closes most of it
structurally — see §7, which is where the honest limit is.

---

## 4. `Book Depth` high and low: the gate moves, the data does not

The brief asked whether book play at high or low `Book Depth` produces a
repetition or 50-move draw while still in book, which would interact with the
drawn-root bail.

**Measured: it cannot, and the reason is structural rather than statistical.**

| `Book Depth` | games | exit ply | book plies | repetitions in book | 50-move in book |
|---|---|---|---|---|---|
| 0 | 200 | **0, all** | **0, all** | **0** | **0** |
| 6 (`Book Variety` 100) | 200 | *(running)* | *(running)* | **0** | **0** |
| 30 (default) | 320 | **16, all** | 16, all | **0** | **0** |
| 100 (max) | 200 | **16, all** | 16, all | **0** | **0** |

Raising `Book Depth` from 30 to 100 changed **nothing**: still 16 plies, still 53
distinct opening lines, still 0 drawn roots. That is the expected result once §2
is known — the gate was never the binding constraint, the data was — and it is
asserted rather than assumed so a future book with deeper entries cannot quietly
change the picture.

Lowering it to 0 disables book play entirely (the gate `game_ply(board) < 0` is
never true), which is the correct reading of the option and makes that arm a
**working negative control**: `exit_ply = 0` and `book_plies = 0` in all 200 games
is what the harness must report if it is not inventing book play. It does.

### Why no 50-move draw can arise in book, independent of the games

The halfmove counter starts at 0 in every game and increments only on reversible
moves. A 50-move draw needs the counter to reach 100. **The longest book line is
16 plies**, so the counter can be at most 16 when the book plays. No number of
games can change that, and no `Book Depth` setting can either.

---

## 5. Book versus the engine's own choice at depth 18

This is the question where a careless answer would have been wrong, so the method
is described before the number.

### Two separate questions, kept separate

1. **Does the book move concede material?** Judged by a capture-resolving material
   search (`scripts/q3_book_vs_search.py`), not by the engine's evaluation.
2. **Does the engine call the book move worse?** Judged at **depth 18**, as the
   brief requires (`scripts/q3b_depth18_verdict.py`).

A gambit answers "yes" to (1) and "no" to (2). **Only (2) can condemn a book
move**, and the brief says so explicitly.

### Part 1: material, on the moves games actually played

589 distinct `(position, book move)` pairs, taken from the 320 `default` games —
i.e. moves the book really played, not the book's own catalogue.

| measure | value |
|---|---|
| pairs examined | 589 |
| book move equals the depth-18 top choice | 327 |
| book move differs from the depth-18 top choice | 262 |
| book move concedes material vs the depth-18 choice | **13** |

### Part 2: the depth-18 verdict on those 13

`evidence/q3-depth18-verdict.json`.

| measure | value |
|---|---|
| concession moves re-asked at depth 18 | 13 |
| **noise floor** (same position, same command, twice) | **max 18 cp, mean 5.0 cp** |
| largest gap between the engine's top choice and the forced book move | **51 cp** |
| gaps at or under a pawn (100 cp) | **13 of 13** |
| **condemned as defects** | **0** |

The gap distribution is `-4, 2, 9, 13, 14, 23, 28, 30, 34, 34, 39, 39, 51` cp.
One book move scores *better* than the engine's top choice (−4). Five are inside
the measured noise floor. **The worst is half a pawn and is a deliberate gambit**,
not a defect.

### The case that shows why the two questions must be separate

`f3e5` in `r1bqk1nr/pppp1ppp/2n5/2b1p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w` concedes
**−200 cp of material** (a knight for a pawn after `Nc6xe5`). The material judge
flags it. At depth 18 the engine evaluates the position at **+2 cp** and the gap to
its own top choice is small — the sacrifice is sound. **Reporting the material
number as a defect would have been exactly the error the brief forbids.**

### The noise floor, and what it is a floor *of*

Measured by running the identical `go depth 18` command twice on the same position
and taking the absolute score difference: **max 18 cp over 13 positions, mean 5.0
cp.** That is this engine's depth-limited determinism on these positions, and it is
the number any claim of "the book move is worse" has to beat. Every one of the 13
does not.

### A stated limit on the depth-18 arm

The forced-move score comes from `go depth 18 searchmoves <move>`, and `searchmoves`
is known to perturb search order (findings §6: it changed the reported best move in
5 of 15 at depth 12, and the effect grows with depth). Here both arms are the *same
position* compared against itself, and the reported figure is a gap rather than an
absolute, so the perturbation is bounded by the measured floor rather than assumed
away. **It is not a claim that the forced score equals the score the engine would
report with the move unrestricted**, and no such claim is made anywhere above.

---

## 6. `Book Depth` was not re-litigated

The brief says the diagnosis is correct and must not be patched. It was not
patched, and no measurement here bears on how the depth is derived. The one
thing this audit adds is the observation that `Book Depth` **≥ 16 is
indistinguishable from 30 or 100** because the book has no entries past ply 16 —
a fact about the data, not about the derivation, and not a criticism of it.

---

## 7. Clock gate: the book fires from the opponent's clock alone, and games behave

### The probe

`scripts/q4_clock_gate.py`, both builds, 5 s window, every position **asserted**
against the book graph before use. `evidence/q4-clock-{lock,patched}.json`.

**Control runs first and the run is void if it fails**: the both-clocks form must
answer. It did.

| case | lock | patched |
|---|---|---|
| book position, White, both clocks | books `c2c4`, 0.000 s | books `c2c4`, 0.000 s |
| book position, White, **only `wtime`** | books `e2e4`, 0.000 s | books `e2e4`, 0.000 s |
| book position, White, **only `btime`** | **no bestmove in 5 s** | **books `c2c4`, 0.000 s** |
| book position, Black, both clocks | books `c7c5`, 0.000 s | books `e7e5`, 0.000 s |
| book position, Black, **only `btime`** | books `e7e5`, 0.000 s | books `c7c5`, 0.000 s |
| book position, Black, **only `wtime`** | **no bestmove in 5 s** | **books `c7c5`, 0.000 s** |
| **no-book** position, White, both clocks | search, 0.421 s | search, 0.398 s |
| **no-book** position, White, **only `btime`** | **no bestmove in 5 s** | **search, 0.399 s** |
| **no-book** position, White, **only `wtime`** | search, 0.429 s | search, 0.394 s |

So on the patched build the asymmetry is gone: **both colours book whichever
single clock is supplied**, and — the row that matters, because a book reply
returns before the time manager is consulted — a **no-book position with only the
opponent's clock now answers in 0.399 s** where the lock is unbounded.

### The games, played that way

The `patched` arm plays 200 games on the patched build with the same clock form.
Its termination and book-exit numbers are in §3 and `evidence/games-patched-summary.json`;
they match the lock arms. **Playing from the opponent's clock alone changes nothing
about how the book behaves**, which is the expected result — the patch changes how
the budget is read, not what the book plays.

### Two probe positions I had to fix, which is why they are now asserted

My first version of this probe used two guessed FENs and **both were wrong**:

* the "no-book" FEN actually had a book entry (it booked `g1f3`), so its row
  measured book behaviour while claiming to measure search;
* "startpos with Black to move" is not a position reachable by legal play and has
  no book entry, so its row measured a search that could never book.

The script now derives every position by legal move play and **fails loudly** if
its own precondition (in book / not in book) does not hold. A probe whose
precondition is a guess measures nothing.

---

## 8. What I had to withdraw

Each of these was a defect in **my own measuring apparatus**, not in the engine.
They are listed because a number produced before the fix was wrong, and because
the shape of each mistake is reusable.

### 8.1 "45 book moves lose material" — withdrawn, apparatus bug

Measured material after one reply ply, so a capture was seen but never the
recapture. Every move that allowed any capture scored exactly −100 / −300 / −900,
a piece value, which is what a one-ply error looks like. Fixed by a
capture-resolving quiescence search. The count fell from 45 to 13.

### 8.2 "27 book moves lose material" — withdrawn, apparatus bug

The replacement negamax recursed on `-side` where `side` is a python-chess `Color`
— **a bool**, so `-True == -1` was never a colour. Every gap came out as exactly
100 or 300 cp. Fixed; the count fell from 27 to 13.

### 8.3 "77 re-entry repetitions" — withdrawn, apparatus bug

The script built each book "line" from a **FEN**, which carries no move history, so
the ancestor indices it compared against were meaningless and the 77 "hits" were
phantoms. Found by checking one hit against the position it claimed to repeat,
which did not match. Rewritten to carry the move list.

### 8.4 A threefold claim that could never have fired

The same FEN habit meant the engine was asked repetition questions with **no key
history**, so it could never report a repetition. Any "not drawn" answer from that
version was vacuous. Every repetition question is now asked with
`position startpos moves ...`. A control (a hand-built threefold on startpos with
the book on) now has to reproduce trap 19a's signature — book move, no
`info depth` — or the run is void.

### 8.5 A book decoder that produced moves the engine rejects

The book stores castling as king-takes-rook (`e1h1`). python-chess accepts that
form; **the engine does not** — it answers `info string illegal move e1h1`. My
decoder passed the stored form through, so a move list built from it was refused
outright. Fixed to emit `e1g1`/`e1c1`/`e8g8`/`e8c8`.

**This did not affect the 1,120-game result**: the game harness compares the
engine's own `bestmove` string against its own `info string book move` string, so
both sides use the same encoding. Checked directly: 42 games contain a
king-takes-rook UCI move, **all at ply 37 or later**, well after the ply-16 book
exit, and **0 inside the book region**.

### 8.6 Four fixtures that were not legal positions

Hand-written FENs for the material-judge self-test included adjacent kings, a side
already in check, and a castling right that cannot exist. Each made a test pass or
fail for a reason unrelated to the judge. All fixtures are now **derived by legal
play from startpos**, and the test refuses to run a case whose fixture is invalid.
Two further expectations were themselves wrong (`exd5` is met by `Qxd5`;
`b7a8q` also captures a rook) — the judge was right and my expectation was not.

### 8.7 A search that could not finish, reported as a null

The first re-entry search walked all legal moves, exceeded its own timeout, and
printed nothing; the second hit a node cap and reported the cap as a clean result.
**Neither is evidence.** The current version reports a bounded null *as* bounded
and says so in the same sentence (§9).

---

## 9. Limits, stated as limits

* **The re-entry route is only partly closed structurally.** I found that a book
  position *can* be reproduced after leaving the book (the book's last move can be
  undone), which means the acyclicity argument does not by itself exclude trap 19a
  in play. `scripts/reentry_drawn.py` shows that for **122 of 199 book leaves** the
  set of returnable earlier positions is **empty** — an irreversible move (pawn
  move, capture, or castling-rights change) separates them forever — which is a
  complete result at any depth. For the other 77 leaves its search is **bounded**
  and is labelled bounded. **The unbounded evidence for those 77 is the 1,120
  games, which produced 0 drawn-root book events and 0 re-entries.**
* **Games are a finite sample.** 1,120 games is not a proof; it is a large,
  diverse sample (63 distinct 16-ply opening lines in one arm alone) with an
  exhaustive structural argument behind it for the repetition question.
* **Book `Book Variety` is the only diversity control.** The book RNG is seeded
  from the clock inside the engine and is not exposed, so per-process seeding was
  not available. Recorded in `play_games.py` as a limit rather than papered over.
* **Depth 18 is the depth used for every "is this move bad" question**, and the
  noise floor (max 18 cp) is printed beside every such number.
* **The `depth0` and `depth6var100` arms** were still running when this file was
  written; `STATUS.md` carries their final numbers and the summary JSONs hold the
  raw records.
