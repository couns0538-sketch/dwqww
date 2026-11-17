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
| Does the book produce legal, terminating games? | **Yes.** 920 games over four completed arms, **0 illegal moves, 0 engine errors**, and 0 non-rule terminations beyond 7 harness ply-cap stops |
| Does any game leave the book into an illegal or lost-on-the-spot position? | **No.** 0 illegal moves; 0 of 63 exit positions below −200 cp (worst −50); **0 of 63 exit positions is a drawn root** |
| How deep does the book take games? | **As deep as the data goes, and no further.** At the default `Book Depth`, **520 of 520** games exit at exactly ply 16 — the book's own deepest leaf (§2). Lowering `Book Depth` to 6 or 0 caps it exactly (exit at ply 6 and 0); raising it cannot extend it. Full dose-response in §4 |
| Can book play reach a repetition or 50-move draw? | **Not inside the book** — the book's position graph is acyclic, so no book line revisits a position; worst halfmove clock at exit is 6. **But a book position can recur after leaving the book, and the engine then books a threefold root — see §9.** Not observed in 920 games |
| Does the book disagree with the engine at depth 18 and lose material? | **13 of 589 played book moves concede material; 0 are condemned at depth 18.** Largest gap 51 cp against a measured 18 cp noise floor |
| Does the book fire from the opponent's clock alone on the patched build? | **Yes** — all six clock forms answer, and a *no-book* position with only the opponent's clock answers in 0.466 s where the lock is unbounded (§7). Games on the patched build were still running, so no game-level claim is made |

**Nothing in this audit condemns the book, and nothing in it withdraws a prior
finding.** `Book Depth` was not re-litigated: it is correct and untouched (§6).

**One thing IS new and worth the coordinator's attention:** the book can be
made to fire on a genuine threefold root in real play, by re-entering it at a
position that already occurred. I reached the state and the engine reproduced
trap 19a's signature there (§9). It is reachable, not automatic — 920 games did
not produce it — and it is a policy question already on the list, not a new defect.

**And the trap-2 patch closes it, measured on identical positions** (§9): at the
threefold the lock books with zero depth lines, while the trap-2 build returns the
drawn-root bail and still books a non-drawn position. So the route §9 found is
covered by the patch that already exists.

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
   ply 16. So at the default `Book Depth` the answer is a single value, and the
   game data below reproduces it exactly (520 of 520 games at `Book Depth` 30 or
   100 exit at ply 16). At a LOWER `Book Depth` the gate binds first and the exit
   ply is that setting — measured as a dose-response in §4, not folded in here.
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

## 3. Two-sided games: 920 complete

`scripts/play_games.py` runs two engine processes per game (one per colour, so
each side keeps its own `Book Variety` RNG state) and drives every move with the
clock form `go wtime ... btime ... winc ... binc ...` — the only form that reaches
the book without `movetime`.

| arm | games | `Book Depth` | `Book Variety` | engine | status at push |
|---|---|---|---|---|---|
| `default` | **320** | 30 (engine default) | 30 (default) | lock | **complete** |
| `depth100` | 200 | 100 (max) | 30 | lock | **complete** |
| `depth0` | 200 | 0 | 30 | lock | **complete** |
| `depth6var100` | 200 | 6 | 100 (max) | lock | **complete** |
| `patched` | 200 | 30 | 30 | trap-1 patch | running |

**920 games are complete and every number in this report is drawn from them.** The
`patched` arm was still running at push time and no number here depends on it;
`STATUS.md` carries its final figures. An earlier draft of this file quoted 1,120
games before the arms had finished; that was corrected against `evidence/`, and is
recorded in §8.8.

### Termination and legality — the check that matters most

Counts are per arm; `evidence/games-*-summary.json` holds the full breakdown.

| arm | `Book Depth` | `Book Variety` | games | mate | threefold | fifty | insufficient | stalemate | ply-cap | illegal | engine error |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `default` | 30 (default) | 30 | 320 | 71 | 205 | 13 | 28 | 1 | 2 | **0** | **0** |
| `depth100` | 100 (max) | 30 | 200 | 40 | 133 | 8 | 17 | 1 | 1 | **0** | **0** |
| `depth0` | 0 | 30 | 200 | 45 | 124 | 17 | 13 | 0 | 1 | **0** | **0** |
| `depth6var100` | 6 | 100 (max) | 200 | 51 | 113 | 13 | 19 | 1 | 3 | **0** | **0** |
| `patched` | 30 | 30 | 200 | *(running)* | | | | | | **0** | **0** |

**Every game terminated by a chess rule or by mate, except 7 ply-cap stops**
(2 + 1 + 1 + 3 across the four arms). A ply-cap stop is not counted as a
termination: the engine did not end that game, the harness did at 400 plies. The
two from the `default` arm were inspected by hand:

* game 40 of `default` — 400 plies, `b7/8/8/8/5k2/8/7P/4K3 w` — K+P vs K, drawn
  by insufficient material in practice but never *claimed*, because the engine's
  `is_insufficient_material()` requires no pawns. A known limitation of the
  adjudicator, not of the book, and it is 400 plies after book exit.
* game 144 of `default` — 400 plies, Q+P vs Q, a genuine long manoeuvring phase.

Neither was in the book: both games left the book at ply 16. **The other five were
not inspected individually** — they are reported as a count, and no claim in this
report depends on them beyond the fact that they were not rule terminations.

### Book exit ply

`book_exit_ply` distribution across **all 520 book-playing games: `{16: 520}`.** Minimum,
maximum and median are all 16. This is the distribution the brief asked for, and
it is a single spike rather than a spread because of §2.1.

### No game left the book into a lost-on-the-spot position

Checked two ways, and the second is the one that could fail:

* **Legality**: 0 illegal engine moves in 920 games. Every book move and every
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

The mates in the table above are mates *delivered*, not suffered at ply 17: games
average **137 plies** (median 127), and the exit scores span **−50 to +76 cp** — no
exit position is anywhere near a mate score.

### Repetition stayed inside the rule

`max_repetition` counts how many times the most-visited position occurred. Across
all 920 games **0 games exceeded 3.** Games ending at threefold report exactly 3,
which is the rule working, not the rule being broken.

### Book on a drawn root: zero events

`book_on_drawn_root` counts plies where the book fired on a position that was
*already* a repetition, a 50-move draw, or insufficient material — the game-level
form of trap 19a. **0 events in 920 games.**

The stronger check is on the **position the engine is handed immediately after the
book stops**, because that is where trap 19a would bite. `scripts/q1c_exit_drawn.py`
tests all 63 distinct exit positions against the engine's own three drawn-root
tests, each reported separately. `evidence/q1c-exit-drawn.json`:

| test | exit positions failing it |
|---|---|
| threefold repetition (asked with `startpos moves ...`, so history exists) | **0 of 63** |
| halfmove clock ≥ 100 | **0 of 63** |
| insufficient material | **0 of 63** |

**Worst halfmove clock at any book exit: 6.** The book exits at ply 16 with a
counter that started at 0, so a 50-move root is not merely unobserved, it is
arithmetically unreachable.

The detector is shown to fire on all three kinds of drawn root by controls in the
same script (a 50-move root, a hand-built threefold, and a bare-minor position), so
the zeros above are "looked and found none", not "could not have found one".

### Re-entry into the book

`book_reentry_plies` counts the book firing again *after* a non-book move. **0
events in 920 games.** This matters because §2's acyclicity argument covers
book-to-book paths only; a re-entry would be the one route around it. The games
close that route empirically in the games, and `scripts/reentry_drawn.py` closes
most of it structurally — but **not all of it**: see §9, which is where the honest
limit is and where the reachable exception lives.

---

## 4. `Book Depth` high and low: the gate moves, the data does not

The brief asked whether book play at high or low `Book Depth` produces a
repetition or 50-move draw while still in book, which would interact with the
drawn-root bail.

**Measured: it cannot, and the reason is structural rather than statistical.**

| `Book Depth` | games | exit ply | book plies | drawn-root book events | re-entries |
|---|---|---|---|---|---|
| **0** | 200 | **0, all** | **0, all** | **0** | **0** |
| **6** (`Book Variety` 100) | 200 | **6, all** | 6, all | **0** | **0** |
| **30** (default) | 320 | **16, all** | 16, all | **0** | **0** |
| **100** (max) | 200 | **16, all** | 16, all | **0** | **0** |

**This is a dose-response, and it is the cleanest result in the audit.** The exit
ply follows the setting exactly until the setting exceeds the data: `0 -> 0`,
`6 -> 6`, and then both 30 and 100 land on **16**, which is the book's deepest leaf
(§2). `Book Depth` is being honoured precisely; above 16 there is simply nothing
left to play. 920 games, 0 illegal, 0 over threefold, 0 drawn-root book events,
0 re-entries in every arm.

Raising `Book Depth` from 30 to 100 changed **nothing**: still 16 plies and still
0 drawn roots, over **53 distinct 16-ply lines** in that arm (63 in the `default`
arm, from more games). That is the expected result once §2
is known — the gate was never the binding constraint, the data was — and it is
asserted rather than assumed so a future book with deeper entries cannot quietly
change the picture.

Lowering it to 0 disables book play entirely (the gate `game_ply(board) < 0` is
never true), which is the correct reading of the option and makes that arm a
**working negative control**: `exit_ply = 0` and `book_plies = 0` in all 200 games
is what the harness must report if it is not inventing book play. It does.

### The arms are comparable, and that is checked rather than assumed

Because the book RNG is per-process (§7), two arms played at `Book Variety 30`
could in principle be comparing two different draws rather than two settings. So
the arms' opening distributions are compared directly:

| arm | games | `e2e4` | `c2c4` | `e2e4` share |
|---|---|---|---|---|
| `default` | 320 | 178 | 142 | 0.556 |
| `depth100` | 200 | 102 | 98 | 0.510 |

Two-proportion test: **z = 1.03**, consistent with one shared distribution, and
both sit near the 0.583 single-position share measured over 24 processes in §7.
**So the arms are sampling the same book, at the size used here.** The RNG averages
out at 200+ games; it does not at one game, which is why the probe tables in §7 use
`Book Variety 0` and the game tables use many games.

(`depth0` shows `e2e4` 200 of 200 because with `Book Depth 0` **no book move is
played at all** — that "first move" is the engine's search choice, and the fact
that it is constant while the book arms are not is itself a check that the book,
not the search, was producing the variety.)

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
the measured noise floor. **The worst gap is 51 cp — about half a pawn — and no
gap reaches a pawn.** Whether a given one is a sacrifice or a small inaccuracy is
not decided here: the claim is only that none clears the depth-18 bar that the
brief sets for calling anything a defect.

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
| book position, White, both clocks | books `e2e4`, 0.000 s | books `e2e4`, 0.000 s |
| book position, White, **only `wtime`** | books `e2e4`, 0.000 s | books `e2e4`, 0.000 s |
| book position, White, **only `btime`** | **no bestmove in 5 s** | **books `e2e4`, 0.000 s** |
| book position, Black, both clocks | books `c7c5`, 0.000 s | books `c7c5`, 0.000 s |
| book position, Black, **only `btime`** | books `c7c5`, 0.000 s | books `c7c5`, 0.000 s |
| book position, Black, **only `wtime`** | **no bestmove in 5 s** | **books `c7c5`, 0.000 s** |
| **no-book** position, White, both clocks | search, 0.453 s | search, 0.468 s |
| **no-book** position, White, **only `btime`** | **no bestmove in 5 s** | **search, 0.466 s** |
| **no-book** position, White, **only `wtime`** | search, 0.463 s | search, 0.471 s |

**Every row where both builds answer now returns the SAME move**, which is what
makes this a comparison of builds rather than of two book RNG draws — see the
next subsection, which is the reason this table had to be re-run.

So on the patched build the asymmetry is gone: **both colours book whichever
single clock is supplied**, and — the row that matters, because a book reply
returns before the time manager is consulted — a **no-book position with only the
opponent's clock now answers in 0.466 s** where the lock is unbounded.

### The book RNG is nondeterministic, and my first version of this table was contaminated by it

The engine seeds the book RNG from `steady_clock::now()` **per process**
(`src/uci.cpp:161-162`), so at the default `Book Variety` of 30 the *same*
position returns *different* book moves on different runs. `scripts/q0_rng.py`,
24 fresh processes, startpos at `go wtime 1000 btime 1000`:

| `Book Variety` | distribution over 24 processes | distinct |
|---|---|---|
| 30 (default) | `c2c4` **14**, `e2e4` **10** | 2 |
| **0** | `e2e4` **24** | **1** |

That reproduces the coordinator's `14 / 10` exactly and shows `Book Variety 0`
pins the choice.

**This invalidated the first version of the table above, and the fix is in the
same commit.** Run at the default variety, the lock and patched builds returned
different book moves (`c2c4` vs `e7e5` on one row) — and both arms show zero
`info depth` lines, so "one arm searched differently" cannot rule the RNG out.
**Those differences were the RNG, not the patch.** The table above was re-run with
`Book Variety 0` and every row where both builds answer now returns the same move.
The script now sets variety 0 by default and says why in a comment at the call site.

**A control that would have caught it, and that this table now satisfies:** if two
arms differ on a book move while agreeing on every clock case they both answer,
the difference is the RNG. The re-run's lock and patched columns are identical on
all six rows where both answer, and differ only on the three rows where the lock
does not answer at all — which is the actual claim.

### The games, played that way

The `patched` arm plays 200 games on the patched build with the same clock form.
**It had not finished at push time**, so this audit makes no claim from it. The
expected result is that its book behaviour matches the lock arms, because the patch
changes how the budget is read and not what the book plays — but that is an
expectation, not a measurement, and it is labelled as one. `STATUS.md` records the
final figures.

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

**This did not affect the game result**: the game harness compares the
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

### 8.8 "1,120 games" — withdrawn, an unearned count

An early draft of this file said 1,120 games had been played when **720** had
finished; the last two arms were still running. Nothing was invented — the plan
was for 1,120 — but **a planned number is not a measured one**, and the sentence
that carried it read as a completed result.

Found by cross-checking every headline figure in this file against the JSON in
`evidence/` after the first push. Every count now in this report is a count of
records that exist: 320 + 200 + 200 + 200 = 920. The one unfinished arm is named as
running in §3 and is quoted nowhere as complete.

This is the same failure the swarm's own rules describe from the other direction:
a check that reports a confident wrong answer is worse than one that reports
nothing, because the wrong answer looks like verification.

## 9. The one route the isolation test could not see: the book's last move is undoable

This is the only place this audit found something the move-by-move soundness check
could not have found, so it gets its own section rather than a footnote.

### What the structure allows

The book graph from startpos is acyclic (§2), so play that **stays** in book cannot
repeat. But a game leaves the book, and the acyclicity argument says nothing about
where it goes afterwards. `scripts/reentry_drawn.py` asks the precise question:

> from a book leaf, can play reach a position that (a) is **in the book** and
> (b) **already occurred** on that book line?

**Yes, on all 77 leaves where it is possible at all** (122 of 199 cannot, §9.3).
A concrete case, confirmed by hand and reproduced end-to-end by
`scripts/q2b_shuffle.py` (`evidence/q2b-shuffle.json`):

```
ply 15  Black to move, bishop on f8          -- IN THE BOOK
ply 16  the book plays ...f8e7               -- White to move, bishop on e7 (a LEAF)

White plays Nf3-g5,
Black plays ...e7f8   (undoing the book's own move),
White plays Ng5-f3,

-> back at the ply-15 position exactly, which IS in the book.
```

### The state is reachable, and the engine reproduces the trap signature there

Driving that shuffle, `q2b_shuffle.py` reaches the recurring position for the
**third** time at **ply 23**, and asks the real engine there with the full move
history attached (`position startpos moves ...`):

| round | ply | at the ply-15 position | threefold | in book | engine reply | `info depth` lines |
|---|---|---|---|---|---|---|
| 1 | 19 | yes | no | yes | book `f8e7` | **0** |
| 2 | 23 | yes | **yes** | **yes** | book `f8e7` | **0** |
| 3 | 27 | yes | **yes** | **yes** | book `f8e7` | **0** |

**At ply 23 the position is a threefold, is in the book, and the engine emits
`info string book move f8e7` with zero `info depth` lines.** That is trap 19a's
exact signature — the book deciding before any draw adjudication runs — reached
through real play rather than through a hand-built FEN.

**Two controls gate this, and the run is void if either fails:**

* an ordinary book position must still book (it does: `c7c5`, 0 depth lines);
* a hand-built threefold on startpos must show the signature with the book on
  **and** the drawn-root bail (cp 0, empty pv) with it off. It does. Without this
  the harness could not be shown to detect the defect, so a clean result elsewhere
  would mean nothing.

### Why it did not happen in 920 games

Three reasons, and only the third is empirical:

1. **The shuffle needs the opponent to cooperate.** After the leaf the book has no
   entry, so both sides search — and a search does not volunteer a 3-ply
   repetition. The state is reachable but neither engine walks into it unaided.
2. **122 of 199 leaves cannot do it at all** (§9.3): every earlier position is
   separated forever by an irreversible move.
3. **0 re-entries and 0 drawn-root book events in 920 games** confirm (1)
   empirically, and that is the unbounded evidence — a bounded search cannot
   establish it.

### The limit, stated as a limit

The 77-leaf search is **bounded** (depth 6, 20 000 moves per leaf, 41 376 positions
examined) and is labelled bounded in its own output. It establishes that revisits
**exist**; it does not establish that no *other*, longer route exists. The games
are the evidence for the negative, and 920 games is a sample.

### What this does and does not mean

**It is not a defect in the book, and no book move is condemned here.** The book
contains no bad move; the route requires the book to be handed a position it
already covered. That is precisely the policy question trap 19a's own "owner's
decision" items already raise — *should a drawn root ever book?* — and the answer
may legitimately be yes (a repetition at move 12 in a forced-draw line is arguably
a book situation). **What is new is that the state is reachable in play, so that
decision now has a reachability fact behind it rather than a hypothetical.**

### The existing trap-2 patch closes it, and that is measured

`scripts/q5_trap2_closes_route.py` asks **both builds at the same frozen positions**
(the three occurrence positions, built once with python-chess, so neither column can
drift). `evidence/q5-trap2-closes-route.json`:

| build | cycle 1 (ply 19, not drawn) | cycle 2 (ply 23, **threefold**) | cycle 3 (ply 27, **threefold**) |
|---|---|---|---|
| lock | book `f8e7`, 0 depth lines | **book `f8e7`, 0 depth lines** | **book `f8e7`, 0 depth lines** |
| trap 2 | book `f8e7`, 0 depth lines | **no book; drawn-root bail** | **no book; drawn-root bail** |

The trap-2 build returns the search's own drawn-root report at the threefold —
`best a7a6`, 64 depth lines, and the **`cp 0 / nodes 0 / empty pv` bail signature**
detected programmatically — instead of a book move. Cycle 1, which is *not* drawn,
still books on both builds, and an ordinary book position still books on both. So
the fix removes the pre-emption **without removing the book**, which is the
distinction that separates a fix from a disable.

**This is the useful deliverable of §9: the route is real, it is reachable, and the
patch that is already written closes it.** No new patch is proposed; `uci.cpp` is
untouched.

**One honest note on the control design.** My first version of this test let each
build drive its own continuation, so the trap-2 column diverged at the first
non-book reply and the script crashed on an illegal move — the two columns were no
longer comparing the same position. Freezing the positions and asking both builds
at identical move lists is what makes the comparison mean anything.

---

## 10. Limits, stated as limits

* **The re-entry route is reachable on 77 of 199 leaves** — see §9. It is bounded
  there and unobserved in 920 games.
* **Games are a finite sample.** 920 games is not a proof; it is a large,
  diverse sample (63 distinct 16-ply opening lines in one arm alone) with an
  exhaustive structural argument behind it for the in-book repetition question.
* **Book `Book Variety` is the only diversity control.** The book RNG is seeded
  from the clock inside the engine and is not exposed, so per-process seeding was
  not available. Recorded in `play_games.py` as a limit rather than papered over.
  Comparisons use variety 0 (§7).
* **Depth 18 is the depth used for every "is this move bad" question**, and the
  noise floor (max 18 cp) is printed beside every such number.
* **`depth6var100` and `patched` were still running at push time.** No number in
  this report depends on them; `STATUS.md` carries their final figures.
