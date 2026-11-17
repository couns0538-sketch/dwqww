# MultiPV output audit — forge-combo29 @ `6b98f217`

**Seat:** MultiPV OUTPUT (cost was already measured; this seat measures what a client
*receives*). **Base:** `6b98f2170a3210e71beed04bbd2553972c253ed7` ("Checkpoint standalone NNUE
v3 work and evidence"). **Deliverable root:** `forge-combo29/swarm/multipv/`. **Engine source:
unmodified.** This seat adds a harness, evidence, and a report. No patch is proposed and no file
under `src/` or `include/` is touched.

---

## 0. The one-paragraph version

MultiPV output is **structurally sound and behaviourally surprising, in different places.**

Ordering and score monotonicity are **perfect** — `0` emission-order violations and `0`
index-order violations across `1920` depth blocks — but only because the engine sorts before it
prints, so those two properties are true by construction and tell a client nothing.

Completeness is **perfect at fixed depth** (`0` incomplete blocks over `1920`) and **routinely
violated under a budget**: `32,32,32` of `40` on a node budget, and `35,35,31` on a wall-clock
budget over three repeats — a range, because a movetime stop is not reproducible. `N > legal
moves` is handled correctly and never over-claims.

**PV length monotonicity — the standard expectation — is violated in `116` of `160` final
blocks**, and in `80` the *first* line is not the longest. A GUI that sizes its PV pane from
line 1 silently truncates the best line.

**The multipv-1 line equals `bestmove` in every search checked** but equals the *single-PV
search's answer* in only `22` of `40` positions. In the `18` that differ, a deeper search
**confirms the single-PV answer `9` times**, confirms the MultiPV answer `3` times, and **picks
a third move `6` times** — the position is simply unsettled, and a depth-only control changes
the move in `12` of `40` positions without MultiPV being involved at all.

**The book path emits zero `multipv` lines at MultiPV 2, 3 and 6** (trap 19c confirmed), and the
**drawn-root bail emits exactly one line per depth, always `multipv 1`** (confirmed). Both need
client-side handling, and the book case is worse than documented because it **pre-empts the
drawn-root bail** when the FEN's fullmove counter is below `Book Depth`.

---

## 1. Honesty pins first — the build is the lock's build

Every number below is worthless if the binary is not the one the report describes, so the pins
run first and gate the rest (`scripts/00_build_and_pins.sh`, `evidence/pins.json`).

Build: `/usr/bin/c++` on this image is clang 18 with a broken header path, so the compiler is
pinned to `/usr/bin/g++` with `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`.

| pin | want | got |
|---|---|---|
| bench 11 | 312866 | `312866` |
| bench 13 | 862329 | `862329` |
| bench 16 | 3024920 | `3024920` |
| perft 5 startpos | 4865609 | `4865609` |

`true` is not 0, so all four match. Binary sha256
`e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`.

Threads 1 and an explicit `Hash 16` on every search; `OwnBook false` unless the case is the
book.

**Two pin counts appear in this report and they are different sets, not a stale figure** — the
same warning the findings doc raises in rule 20a0. The **four honesty pins** above are bench
11/13/16 plus perft 5. This seat does not re-measure the **11-document pins** (five depths × two
net settings plus perft 5); that set belongs to the drawn-root seat and is not in scope here.

---

## 2. The corpus, and what the FEN gate removed

`tests_r3fu_12/positions.txt` — a random-walk opening corpus already in the tree. Every FEN is
round-tripped through python-chess before it is sent, because an illegal FEN makes this engine
search the **previous** position and answer normally (findings §1b).

- Lines in file: 10,000. `471` dropped — every one
because python-chess rewrites a **stale en-passant field**, not because the board is illegal.
Dropping them rather than sending them matters: the engine would parse the board and search a
position the sender did not mean.
- Eligible after the gate: `9529`.
- Used: `40` positions, seed 20261117, `12` plies.

`160` fixed-depth searches at MultiPV 2/3/4/6, giving `1920` depth blocks and `7116` info lines.

**Determinism control** (`audit.determinism`): at Threads 1, MultiPV 1 against itself is
identical in `10` of `10` pairs, and MultiPV 4 against itself in `10` of `10`. Time-stripped,
every field including `nodes` and `seldepth` matched. So a difference seen later is a difference
of configuration, not of run.

---

## 3. What the checkers are, and the proof they can fail

`scripts/check_multipv.py` holds the property checks as pure functions over parsed blocks.
`python3 check_multipv.py --selftest`:

```
selftest: 26 checks over 13 planted faults, 0 failures
```

`scripts/wire_control.py` does the same against **real captured output**: it takes a live block,
mutates exactly one property, and asserts the named checker goes from clean to firing.

```
wire control: 43 assertions, 0 blind, 1 captures already dirty
```

**Zero blind checkers.** The one "capture already dirty" is not a checker fault — it is the
engine already violating that property on unmodified output, which is §5. It is reported
separately rather than folded into "blind" precisely so a real defect cannot be filed as a
harness bug.

Two faults are worth naming because they are the ones a naive checker passes:

- **Mate ordering.** `mate 3` prints a **larger number** than `mate 1` but is a **worse** score. A
checker comparing printed integers calls a correct block mis-ordered and a broken block clean.
The comparator lifts mates clear of cp and inverts distance; `--selftest` asserts both
directions, and asserts that the naive rule cannot separate them.
- **Emission order vs index order.** These look identical in a sorted table and are different bugs.
Fault B on the wire is a block printed in perfect score order whose `multipv` **indices** are
bound to the wrong scores: a client rendering wire-order is right, a client keying on `multipv`
is wrong, on the same bytes. Both are checked.

---

## 4. Property 1 — line ordering. **0 violations, and that is not a compliment**

`multipv 1..N` must arrive in non-decreasing score order for the side to move.

| check | violations | denominator |
|---|---|---|
| emission order (wire order) | `0` | `1920` blocks |
| index order (sorted by `multipv`) | `0` | `1920` blocks |

**Both are zero because the code sorts before printing.** `search.cpp` collects the primary line
plus one excluded-root line per alternate, then `std::stable_sort` by exact score descending,
then emits in that order with `pv_index = i + 1`. Ordering and score-monotonicity are therefore
**one guarantee, not two**, and neither is evidence of anything except that the sort is present.

The sort's tie rule is worth knowing: `stable_sort` keeps the **primary line first** among
equals. So a client can rely on "line 1 is the primary search's line when scores tie" but
**not** otherwise — see §8.

A related field a GUI may show: **`hashfull` decreases inside a block in `847` of `1920`
blocks**, because each alternate reports its own cleared table. At MultiPV 1 `hashfull` is
monotone in `40` of `40` searches. A GUI drawing a "hash fill" bar per line will see it drop
line to line; that is correct behaviour and not a stall.

---

## 5. Property 2 — PV lengths. **The largest defect in this seat**

Two separate questions, and they answer differently.

### 5a. PV length is NOT monotone in multipv index

The standard expectation is `len(pv_1) >= len(pv_2) >= ...`.

| measure | count | denominator |
|---|---|---|
| final blocks violating PV-length monotonicity | `116` | `160` |
| final blocks satisfying it | `44` | `160` |
| **increasing adjacent pairs** across all blocks | `1410` | `7116` lines |

**In `80` of `160` final blocks the FIRST line is not the longest** (it is in the other `80`).
So line 1 is never merely unlucky: when it is not the longest it is strictly shorter than a line
a client is being told is worse.

Concrete wire capture, `go depth 12`, MultiPV 4, FEN
`r1bqk2r/ppp1n2p/3p1n2/3Pp2P/2P2pp1/4P3/P4PP1/RN1QKBNR w kq - 0 15` — line 1 has 15 plies, line
2 has **16**:

```
info depth 12 multipv 1 score cp -76  seldepth 27 nodes 66108  hashfull 32 pv e3f4 c7c6 ...
info depth 12 multipv 2 score cp -168 seldepth 23 nodes 106347 hashfull 21 pv b1c3 f4e3 ...
info depth 12 multipv 3 score cp -186 seldepth 21 nodes 141953 hashfull 15 pv d1d2 f4e3 ...
info depth 12 multipv 4 score cp -191 seldepth 20 nodes 196482 hashfull 23 pv d1d3 b7b5 ...
```

**Why, from the source and then measured.** The primary line is the ordinary iterative-deepening
search, whose PV is truncated wherever a transposition-table hit ends the line. Each alternate
is a **fresh worker with its own table, cleared before it runs** (`alt_shared->tt.clear()`), so
its PV runs to the nominal depth plus extensions. Measured (`audit.pvlen_mechanism`, `40` final
blocks with ≥2 lines):

- line 1 is the **longest** in `16` of those
`40`
- line 1 is the **shortest** in `8`
- line 1 is **shorter than at least one alternate** in
`24`
- line 1's PV is **below its own seldepth** in `40`

So this is **not** random jitter: the primary line is systematically the truncated one, and its
own `seldepth` says so. **A client that sizes its PV display by line 1 loses moves from the best
line, not from the worst.**

### 5b. PV length vs the depth printed on the line

`2829` of `7116` lines have a PV **longer than the depth field on that same line**. Restricted
to the **final** block, where a client's last render comes from: `441` of `593` lines.

**This needs its control, and the control says it is not a MultiPV defect.** At MultiPV 1 the
same thing happens in `289` of `480` blocks — **more often, proportionally, than at MultiPV>1**.
Extensions make a PV longer than nominal depth; that is what `seldepth` is for.

Against **`seldepth`** the answer is a clean bill, and it is a **different measurement** from
the row above — the earlier wording compared a violation count with a clean count and could be
read as a defect. Both arms use the one predicate

```
violation  <=>  len(pv) > seldepth
```

and the denominators are lines, not blocks:

| arm | MultiPV settings | lines | violations `len(pv) > seldepth` | lines where `len(pv) <= seldepth` |
|---|---|---|---|---|
| MultiPV 1 | 1 | `480` | `0` | `480` |
| MultiPV > 1 | 2, 3, 4, 6 | `7116` | `0` | `7116` |

(`evidence/seldepth_check.json`, `scripts/seldepth_check.py`; measured over the same `40`
positions at depth `12`.)

**Does any line have `len(pv) > seldepth`? No.** `0` violations across all `7596` lines, at
every MultiPV setting measured, and the worst margin `len(pv) - seldepth` is `0` — the bound is
reached exactly, never exceeded. So **`480` of `480` at MultiPV 1 was a clean bill, not 480
violations**, and the same holds for the `7116` lines above MultiPV 1.

The contrast is the point: against `depth` the same corpus has `3118` lines with `len(pv) >
depth`, and against `seldepth` it has none. **`seldepth` bounds a PV; `depth` does not.** That
is the whole claim, and it is a guarantee rather than a tendency — a client can rely on it.

---

## 6. Property 3 — score monotonicity at fixed depth. **0 violations, same caveat as §4**

Scores are non-increasing in `multipv` index in every block examined — `0` violations, the same
guarantee as §4 produced by the same `stable_sort`. Reported separately because a reader will
ask, but it is **one property, checked twice**, and neither check is independent evidence that
the scores are *right* — only that they are *ordered*. §8 is where the values themselves get
questioned.

Ties are common and legal: `22` of `40` positions have line 1's score exactly equal to the
single-PV score.

---

## 7. Property 4 — completeness

### 7a. At fixed depth: complete. 0 missing lines.

| measure | count |
|---|---|
| missing / duplicated / extra indices at any block | `0` over `1920` blocks |
| final block with fewer lines than `min(N, legal moves)` | `0` over `160` |
| `bestmove` ≠ multipv-1 `pv[0]` | `0` over `160` |

Every index `1..N` appears exactly once per block, every block, at fixed depth.

### 7b. Under a budget: routinely incomplete, and it is the *final* block that is short

With `go movetime 200` and `go nodes 20000`, MultiPV 6, `40` positions, **`3` repeats per budget
kind** (`evidence/budget_stability.json`). A wall-clock budget stops at an instant, so which
line an iteration dies on depends on machine load.

| budget | short-final per repeat | stable across repeats | `bestmove` always agrees |
|---|---|---|---|
| `go movetime 200` | `35,35,31` | `false` | `true` |
| `go nodes 20000` | `32,32,32` | `true` | `true` |

**Read the wall-clock row as a range, not a count.** The **node** budget is stable to the
position because it stops on a counter. The **movetime** budget is not: the same three passes on
the same binary gave three different totals, so a report quoting one movetime pass would be
quoting the load of the machine that happened to run it. `32` of `40` is the single-pass figure
from `audit.py`, which mixes both budget kinds — it is **the number not to trust** of the three,
and it is quoted elsewhere in this document only because it is the pass whose per-search rows
are in `evidence/audit.json`.

**What does not move under either budget:** `bestmove` always agrees with the printed `multipv
1` `pv[0]`, and the *shape* of the truncation is identical.

**The shape matters and is a client trap.** The engine does not drop lines silently from a
finished iteration; it **starts a new depth block, emits some of its lines, and is stopped
mid-block**. From `evidence/audit.json`, one `go movetime 200` reply ends:

```
info depth 11 multipv 1 ... multipv 2 ... multipv 3 ... multipv 4 ... multipv 5 ...
<bestmove — no multipv 6>
```

A client that redraws on every `info depth` therefore **loses lines 6 first, and loses them
last**: the final state on screen is the truncated one. This is the opposite of the usual
failure (a stale answer), and it is *correct* engine behaviour — an unfinished iteration must
not invent lines. **The client-side rule is: on `bestmove`, render the last block that was FULL,
or show the short block as explicitly incomplete.** `bestmove` itself was never wrong under a
budget (0 mismatches).

### 7c. N greater than the legal move count

Five sparse positions with known legal counts 1–5, MultiPV 2 and 6, both `go depth 8` and `go
movetime 200` (`evidence/fastpaths.json`). **The engine never emits an index above the legal
move count** — overflow count `0`:

| legal moves | MultiPV asked | lines at final depth |
|---|---|---|
| 1 | 2, 6 | `1` |
| 2 | 2, 6 | `2` |
| 3 | 2, 6 | `2` or `3` (budget-dependent) |
| 4 | 2, 6 | `2` or `4` (budget-dependent) |
| 5 | 2, 6 | `1`, `4` or `5` (budget-dependent) |

**A client asking for 6 lines on a 2-move position gets 2 and must not wait for 4 more.** There
is no end-of-block marker; the only signal is that the block ends and `bestmove` arrives. The
same is true of `searchmoves` narrowed to one move at MultiPV 3: `evidence/fastpaths.json` shows
exactly one line, index `[1]`.

---

## 8. Property 5 — does multipv 1 equal the single-PV answer? **Often not.**

`22` of `40` positions are identical across all three of (single-PV answer, printed multipv-1
line, `bestmove`).

| measure | count | denominator |
|---|---|---|
| `bestmove` differs from the MultiPV 1 search's bestmove | `18` | `40` |
| line-1 score differs | `18` | `40` |
| `bestmove` ≠ the printed multipv-1 `pv[0]` | `0` | `160` searches |

**The last row is the one a GUI depends on, and it holds: `bestmove` always agrees with the
arrow drawn from `multipv 1`.** The disagreement is between the whole MultiPV reply and what a
MultiPV 1 reply would have said.

### 8a. The mechanism, from the source

The printed block is the primary search's line **plus** one excluded-root line per alternate,
then sorted by score. So the entry printed as `multipv 1` **need not be the move the primary
search chose**: when an alternate outscores it, a *different* move takes rank 1 and is returned
as `bestmove`. Measured (`audit.promotion`):

- printed line 1 **is** the primary move: `22`
- printed line 1 **is an alternate that was promoted**: `18`
- of those, the alternate's score was higher in every case: `18`
- the primary's own move is **still listed** further down, never dropped: `18`
- the printed line-1 score did **not** reproduce under an independent re-search:
`18` of `18`

**The promoted move is genuinely better *at that depth* — the primary search does not see it
because its window and history were set by a different aspiration path.** That is the engine
working as designed, and it is exactly what MultiPV is for.

### 8b. Was the promoted move the right move? A deeper search says usually not.

Judge: a **full-width MultiPV 1 search four plies deeper** on the same position
(`scripts/judge.py`). Not `searchmoves` — see §8c for why. Over the `18` positions where the
move changed:

| deeper search plays | count |
|---|---|
| the **MultiPV** printed move | `3` |
| the **single-PV** move | `9` |
| **neither** — a third move | `6` |

**And the control decides how to read it.** The same comparison on MultiPV 1 alone, depth `12`
against depth 16, with no setting involved: the move changes in `12` of `40` positions (`30.0`).
MultiPV's rate is `45.0`.

**So: MultiPV>1 changes the move `45.0`% of the time, more thinking alone changes it `30.0`% of
the time, and when MultiPV changes it a deeper search backs the single-PV move over the MultiPV
move by 9 to 3.** The honest statement is not "MultiPV is wrong". It is:

> **A GUI user who flips the MultiPV spinner gets a different arrow in nearly half of positions,
> and that arrow is more often the one a deeper search would reject than the one it would confirm.
> The 6-in-18 third-move rate says most of these positions are simply unsettled at 12 plies.**

This matches findings §3 ("MultiPV does not rescue an unsettled position") and extends it from
*move instability* to *the direction the answer flips*.

### 8c. The judge I threw away, and why — a noise floor worth recording

The first judge was a `searchmoves <move>` re-search at the same depth. It is **not a neutral
referee**: restricting the root changes the aspiration sequence and the table context.
`scripts/agreement.py` measures that bias directly — on the *same move at the same depth*, the
restricted search differs from the full-width one in `12` of `12` pairs, with the per-gap
histogram `0cp:4 10cp:3 20cp:2 30cp:3`.

**A judge with a 12/12 disagreement rate on the identity case cannot adjudicate a 20–40 cp
difference.** It was replaced by the deeper full-width search in §8b. The number is kept here
rather than deleted because the next seat will reach for the same shortcut.

---

## 9. Property 6 — the two fast paths at MultiPV > 1

### 9a. The book path: **zero `multipv` lines, confirmed at MultiPV 2, 3 and 6**

`go movetime 300` on startpos, `OwnBook true`, at MultiPV 1/2/3/6 — the entire reply is **two
lines** (measured over `3` arms at MultiPV>1, against `4` `OwnBook false` controls):

```
info string book move e2e4
bestmove e2e4
```

| MultiPV | `info depth` lines | `multipv` tokens |
|---|---|---|
| 1 | `0` | `0` |
| 2 | `0` | `0` |
| 3 | `0` | `0` |
| 6 | `0` | `0` |

Every cell above is one counter, so the four rows are the same measurement repeated: the maximum
over all MultiPV>1 arms. That is deliberate — a per-MPV table built from a single counter cannot
quietly disagree with itself.

**Control:** the same position and the same `go movetime 300` with `OwnBook false` searches —
`16` or more `info depth` lines per reply — so the difference is the book gate and not the
position or the budget.

**Why it matters more than "no multipv lines".** There is **no `info depth`, no score, no node
count** either. A client that waits for an `info depth` line times out on every book move (trap
21), and one that waits for `multipv 1` waits forever regardless of the spinner. The only
structured signal is the `info string book move <uci>`, and `bestmove` matches it.

### 9b. The drawn-root bail: **exactly one line per depth, always `multipv 1`, confirmed**

Four distinct drawn shapes at MultiPV 1/2/3/6, `go depth 6`:

| case | `info depth` lines | distinct depths | `multipv` indices | `pv` empty | `nodes` 0 |
|---|---|---|---|---|---|
| insufficient material | 6 | 6 | `[1]` | yes | yes |
| stalemate | 6 | 6 | `[1]` | yes | yes |
| checkmate | 6 | 6 | `[1]` | yes | yes |
| fifty-move | 6 | 6 | `[1]` | yes | yes |

**At MultiPV 2, 3 and 6 the maximum index emitted is `1`**, over `12` arms, of which `0` emitted
an index above 1. One line per depth, and `multipv 1` only — the setting is silently degraded,
exactly as findings §1b describes. The empty `pv` is the guaranteed discriminator: it is the
only field that says no search happened.

**The four shapes are NOT alike and a client that handles one has not handled the others:**

| case | `bestmove` | how a client must read it |
|---|---|---|
| checkmate | `0000` with `score mate 0` | game over — correct, **not** an error |
| stalemate | `0000` with `score cp 0` | game over |
| insufficient material | a **legal move**, `cp 0`, empty `pv` | **do not play it** |
| fifty-move | a **legal move**, `cp 0`, empty `pv` | **do not play it** |

So the blanket "treat `0000` as an error" rule is wrong for the first two, and the blanket
"accept a legal `bestmove`" rule is wrong for the last two. **Both halves are required** — the
same conclusion findings §1b reached, re-measured here rather than assumed.

### 9c. New: the book **pre-empts** the drawn-root bail, and the gate is the fullmove counter

Findings trap 19a says the book pre-empts the bail. Confirmed, and the gate is narrower than "it
is in the book":

`Book Depth` defaults to 30 and is compared against `game_ply(board)`, which is derived from the
FEN's **fullmove counter** — not the halfmove clock, and not the history. So the **same board
with a 100-ply halfmove clock** books or bails depending only on the fullmove field:

| FEN | `OwnBook` | reply |
|---|---|---|
| `.../4P3/... b KQkq - 100 1` | true | **`info string book move c7c5` + `bestmove c7c5`** — booked, game is drawn |
| same | false | `64` `info depth` lines, `bestmove a7a6`, `cp 0`, empty `pv` — bailed |
| `.../4P3/... b KQkq - 100 16` | true **or** false | 64 `info depth` lines, `bestmove a7a6` — bailed either way |

`precedence_booked_not_bailed` is `true`, and `past_book_depth_bails_regardless_of_ownbook` is
`true`.

**A client cannot detect this:** the booked reply is a normal-looking book reply, so a GUI shows
a scored-0.00 move for a game that is over. **This is findings trap 19a, sharpened: the
predicate to add is not "is the root drawn" alone but "is the root drawn, before the book gate
is consulted" — and the gate is a fullmove field a FEN author can get wrong.** That is why 19b's
advice not to patch `game_ply` stands: the derivation is correct; the interaction is the
problem.

---

## 10. What a client should do — the actionable list

1. **Ordering and score monotonicity are free — rely on them.** Do not re-sort; do not validate.
2. **Size the PV pane from the longest line in the block, never from `multipv 1`.** Line 1 is not
the longest in half the blocks, and it is the line whose moves a user most wants to read.
3. **Use `seldepth`, never `depth`, to bound a PV.** `len(pv) > depth` is normal and happens in
`3118` of `7596` lines measured; `len(pv) > seldepth` happens in `0` of them. `seldepth` is a
real bound, `depth` is not. (Full measurement and predicate: §5b.)
4. **On `bestmove`, fall back to the last FULL block.** A budget stop truncates the *final* block, so
the last thing on screen is the incomplete one.
5. **Handle `N > legal moves` by accepting the short block without waiting.** No marker exists; the
only signal is `bestmove`.
6. **On a book move, expect two lines and no score.** Key on `info string book move`. Never wait for
`info depth` or for `multipv`.
7. **On a drawn root, expect `multipv 1` only** and read the empty `pv` as "nothing was searched".
Distinguish `mate 0` (checkmate) from `cp 0` (stalemate or bail); treat a legal `bestmove` with
an empty `pv` as "do not play".
8. **Do not treat the MultiPV-1 line as the engine's considered answer.** It is the best of the lines
*this setting* searched, and a deeper single-PV search contradicts it more often than it
confirms it. The `multipv 1` == `bestmove` guarantee holds, so the arrow is at least
self-consistent.

---

## 11. Limits — what this seat did NOT establish

- **One build, one binary.** `ecf97f8c…`, the four honesty pins matched. The findings doc's own
warning applies: a Linux rebuild is not the Windows lock exe. Every result is about *this*
build.
- **Threads 1 only.** Nothing here is a statement about Threads > 1, where no result is reportable
at all (findings §3).
- **One depth (`12`), one extension depth (16).** §8b's judge is a 4-ply lookahead. A
16- or 20-ply judge would move the 9/3/6 split; it would not change the direction of the
finding, because the third-move rate is the signal that most of these positions are unsettled.
- **The `40` positions are opening random walks.** Sparse endgames and tactical middlegames are
represented only by the five hand-built sparse cases in §7c.
- **`go movetime 200` / `go nodes 20000` are the only budgets tested.** No clock play, no
increment, no `movestogo`; findings §8 and the clock seat own that.
- **No patch is proposed.** §9c names the predicate a repair would need but this seat did not write
or test one; the drawn-root seat's patch and its two controls are the right home for it.
- **Property 2's monotonicity has a defensible reading I did not establish:** whether a *standard
client* truly needs `len(pv_1) >= len(pv_2)`. What is measured is that the conventional
expectation is violated in 116 of 160 blocks, and that line 1's PV is truncated by design (TT
hits) while alternates' are not (cleared tables). The convention's force is a client question,
not an engine one.

---

## 11b. Hand spot-checks of the rendered figures

Three headline numbers were re-derived by hand from the raw rows, not from the counters the
report quotes, on the principle that a placeholder filled with `0` by a missed lookup is the
same defect wearing a number. All three agree.

| claim in §0 | counter | recomputed from |
|---|---|---|
| PV-length monotonicity violated in `116` of `160` | same | the `160` raw `depth_span` rows, re-checking `pv_lens` non-increasing |
| multipv-1 == single-PV in `22` of `40` | same | the `40` `agreement_rows`, re-checking move, score and PV equality |
| book emits `0` multipv lines at MultiPV > 1 | same | the `3` `OwnBook true` arms, against `4` controls |

The first is the one that matters most, because it is the report's largest claim: `160` rows
hand-checked, `116` violate, and the first three are visible as `[15,16]`, `[15,16,14]` and
`[15,16,14,13]` — line 2 longer than line 1 in each.

---

## 12. Reproducing

```bash
cd forge-combo29
./swarm/multipv/scripts/00_build_and_pins.sh .     # build + 4 pins, must print PINS MATCH
./swarm/multipv/scripts/run_all.sh build/forge     # ~8 min, writes evidence/*.json
```

`run_all.sh` runs the self-tests **before** the measurements, prints each stage's counters, and
ends with `verify_counts.py`, which resolves every double-bracket counter marker in this file
from the JSON and fails on any mismatch. A figure that cannot be traced to `evidence/` is a bug
in this report.
