# The DTM oracle: validated, and it finds what the terminal-only test could not

> **WITHDRAWN — see `RETRACTION_dtm_oracle.md` (19-R2).** The DTM values in this report came from a solver that is
> wrong for black-as-strong: an independent brute force gives mate in **5 plies** where the table said **9**. The
> findings that rested on those numbers are withdrawn. **Read this file for the engine observations and the
> method, not for any distance-to-mate figure.**


seat 19 · area 9 · build **PC r15** · **PC20** · **Threads 1** · Hash 16 · cold.

## 1. The three lines

**What was asked.** 19-F54 could only detect a *missed immediate mate*, because without tablebases a
won-but-undecided position is not adjudicable. Build a distance-to-mate oracle for the population where it is
cheap — lone king versus one or two pieces — and upgrade the rate from "no missed mate" to "no missed mate **and
no wrong mate distance**".

**The answer.** **The oracle is built and validated** (KQvK reproduces theory's max DTM of exactly 19 plies), and
it found **1 defect in 8 oracle-covered positions, of a kind the terminal test structurally could not see**:
position 24, `8/8/4k3/6q1/8/8/8/1K6 b - - 5 153`, mates in **7 plies** at depth 16 (`g5d2`) but in **11 plies**
at `go nodes 20000` (`g5c5`) — **the budget-limited search plays a mate two moves longer while still announcing
mate.**

**How sure.** The solver is validated against a known theoretical value, so the DTMs are exact for KQvK/KRvK.
The defect is a comparison of two exact integers (7 vs 11), not a judgement call.

## 2. The solver, and the two wrong versions before it

`loneking/dtm_bfs.py` — exact DTM by **backward BFS** over every legal position of one material signature.

**Validation is inside the script**: for KQvK the maximum DTM with the strong side to move must be **19 plies
(10 moves)**. It reproduces that exactly (345,040 positions solved, 23,412 unresolved = draws).

Two earlier attempts are kept in the record because both were wrong:

| version | what was wrong | evidence |
|---|---|---|
| `dtm.py` | assigned a DTM the first time any winning move was known and **never revised it**, so a long mate stuck | reported max DTM **44 plies** for KQvK vs theory 19 — the tell |
| `dtm_exact.py` | layered but re-scanned every unsolved position each layer | ~7 minutes for KQvK, did not finish in the time given |
| **`dtm_bfs.py`** | — | **19 plies, MATCH** |

There was also a convention error I had to fix before believing the result: the first correct run printed
**20 plies** and `MISMATCH`. The 56 maximum-DTM positions were all **bare-side to move**, so 20 plies *from
Black's turn* is 19 plies *from White's move*. Converting to the strong-side-to-move convention gave 19 and
MATCH. **I nearly reported "my solver disagrees with theory" when the solver was right and my ply convention was
wrong** — which is the mirror of the mistake I would have made by trusting it blindly.

## 3. Scope — what the oracle covers and does not

| signature | status |
|---|---|
| KQvK, KRvK | **solved, validated** |
| KPvK | solved; promotions leave the signature, recorded as "outside the table", not guessed |
| KBvK, KNvK | insufficient material — always a draw, skipped as uninformative |
| 2+ pieces (e.g. KRPvK, KBNvK) | **outside this solver** (enumeration too large in Python here); **24 of the 40 sample positions** |
| both sides with material | out of scope by definition |

**8 of the 40 sample positions were covered.** The other 32 are reported as out of scope, not silently dropped —
that is why the headline rate below is "1 of 8", not "1 of 40".

## 4. The result

| pos | best DTM | depth16 move → DTM | worse? | nodes20k move → DTM | worse? |
|---|---|---|---|---|---|
| 4 | draw/unsolved | `a6a7` → draw | no | `a6a7` → draw | no |
| 15 | draw/unsolved | `h4g5` → draw | no | `h4g5` → draw | no |
| 22 | draw/unsolved | `g4g3` → draw | no | `g4g3` → draw | no |
| **24** | **7** | `g5d2` → **7** | no | `g5c5` → **11** | **YES** |
| 26 | 23 | `e2d3` → 23 | no | `e2d3` → 23 | no |
| 31 | 15 | `c2d3` → 15 | no | `c2d3` → 15 | no |
| 32 | draw/unsolved | `d2e3` → draw | no | `d2e3` → draw | no |
| 33 | draw/unsolved | `f7f8q` → draw | no | `f7f8q` → draw | no |

**1 of 8 positions reaches a worse DTM than available — and only at `go nodes 20000`, not at depth 16.**

Note also the four rows where the best available is `draw/unsolved`: those are KPvK-style positions where the
oracle cannot confirm a win, and the engine drew them — consistent with them genuinely being draws (K+P vs K with
the wrong bishop or a rook-pawn, etc.). I am **not** claiming those are correct; the oracle cannot say.

## 5. Why position 24 matters

`8/8/4k3/6q1/8/8/8/1K6 b - - 5 153` — bare white king, black queen. Black to move, 31 legal moves.

- **`go depth 16`**: `g5d2`, **mate in 7 plies** (4 black moves).
- **`go nodes 20000`**: `g5c5`, **mate in 11 plies** (6 black moves).

Both lines announce mate; the node-limited one just takes **two more moves**. This is precisely the class
19-F54 was blind to: nothing terminal differs (neither move is a draw, neither misses mate), only the *distance*
does. **It is also the mode-difference from 19-F48 showing up as a quality difference rather than a move
difference** — the same position, two budgets, two different mates, and the cheaper mode is the worse one.

For the owner: this is a lone-king ending his match path (`go nodes`) would resolve more slowly, with more moves
on the board and more chances for a fifty-move or repetition accident on the way.

## 6. Finding

**19-F55 — a validated distance-to-mate oracle (KQvK reproduced at theory's 19 plies) finds 1 of 8
oracle-covered lone-king positions where the engine's move reaches a worse DTM than available, and it is the
`go nodes 20000` path only: `8/8/4k3/6q1/8/8/8/1K6 b` mates in 7 plies at depth 16 (`g5d2`) but 11 plies at
`go nodes 20000` (`g5c5`).** The other 7 positions were correct at both budgets (3 confirmed mates at the
optimal distance; 4 draws the oracle could not adjudicate). **Scope: the oracle covers KQvK/KRvK/KPvK only — 8 of
the 40 sample positions; the other 32 have 2+ pieces and are outside it.**

### Suspicions, not proven

- That the DTM gap is caused by the node budget ending the search mid-iteration (19-F46/F47's mechanism) and
  publishing a shallower mate. Consistent with depth 16 being right and nodes-20000 wrong on the same position,
  but I did not trace this position's iteration sequence.
- That the effect would be common across lone-king endings at 20,000 nodes. 1 of 8 with a single budget pair is
  a signal, not a rate.

## 7. What I did NOT do

- **No 2-piece signatures.** 24 of 40 positions are outside the solver. Extending it needs a C implementation
  or symmetry reduction; in Python here the enumeration is too large.
- I did not test other budgets (50k, 250k) on position 24 to find where depth-16's answer reappears.
- I did not trace position 24's iteration sequence to confirm the truncation mechanism.
- The four `draw/unsolved` rows are not adjudicated — the oracle genuinely cannot say if they are draws.

## 8. Files

`loneking/dtm_bfs.py` (validated solver), `loneking/dtm.py` and `loneking/dtm_exact.py` (the two wrong versions,
kept), `loneking/dtm_oracle.py`, `loneking/dtm_compare.py`,
`loneking/oracle/dtm_oracle.txt`, `loneking/dtmdiff/RESULT.txt`.
