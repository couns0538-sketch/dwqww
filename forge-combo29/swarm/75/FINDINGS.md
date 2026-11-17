# FINDINGS.md — is the Forge evaluation SANE? (seat 75)

Scope: the **evaluation only**. The build-independence of evaluation across the
base and PC builds and the move-generation-order explanation of the
colour-mirror search asymmetry are treated as established context and are not
re-tested here.

Engine: `forge-combo29` at `6b98f2170`, built `g++-13`, pins matched
(`perft 5 = 4865609`, `bench 13 = 862329`). Settings for every number:
`Threads 1`, `Hash 16`, `OwnBook false`, one process per measurement.

**Verdict in one line: the evaluation is sane on symmetry, on sign and on
terminal scores, and it is NOT sane on material ordering in bare-minor
endings, where adding a bishop to a bare king lowers the score by 149 cp.**

---

## 75-F1 (MATERIAL INVERSION, confirmed) — in a bare-minor ending, adding a bishop LOWERS the score

The headline of the assignment was "a queen must beat a rook must beat a
bishop". Two of those three relations hold; the bottom rung does not.

| position | FEN | static total | hce | nnue |
|---|---|---|---|---|
| K vs K | `4k3/8/8/8/8/8/8/4K3 w - - 0 1` | **+2** | 0 | +2 |
| **KB vs K** | `4k3/8/8/8/8/8/8/2B1K3 w - - 0 1` | **−147** | +16 | **−163** |
| KN vs K | `4k3/8/8/8/8/8/8/1N2K3 w - - 0 1` | **−144** | +9 | −153 |
| KR vs K | `4k3/8/8/8/8/8/8/R3K3 w - - 0 1` | +353 | +442 | −89 |
| KQ vs K | `4k3/8/8/8/8/8/8/3QK3 w - - 0 1` | +768 | +783 | −15 |

**Inversion:** `K vs K = +2` but `KB vs K = −147`, a step of **−149 cp** for
adding a bishop. `KN vs K = −144` is likewise below the empty board.

Attribution is not ambiguous: the handcrafted term is positive and correct
(`hce = +16` for the bishop, `+10` for the knight), and the compiled-in NNUE
residual term is strongly negative (`nnue = −163 / −114`) and dominates the
sum. Confirmed by `setoption name UseNNUE value false`, under which the same
boards return `0 / +16 / +10` — sane.

Not a fixture artefact. The bishop square was swept over `a1, c1, d4, h8, b6,
e3` and scores **−127 to −159** at every one, so it is the piece, not the
placement. Every FEN in this table was validated against python-chess and the
engine's position reply was scanned for `invalid FEN` (see 75-F7).

Not a global material failure — the scope is precise:

- With pawns on the board the same ladder is cleanly monotonic:
  `18 → 434 → 461 → 859 → 1614` (none/bishop/knight/rook/queen).
- In a real middlegame, removing Black's f8 bishop from
  `r1bqkbnr/pppppppp/2n5/8/8/8/PPPPPPPP/RNBQKBNR` moves the score from
  **+16 to +493, a normal +477 for a bishop.**

Mechanism, from the source: `scale_factor()` (`src/eval.cpp:389-412`) returns
`0` or `12` when the stronger side has no pawns and leads by at most a bishop,
which almost annihilates the handcrafted term. For K vs K the handcrafted term
is 0 and the NNUE residual is +2, so the empty board reads slightly positive;
adding a minor keeps the handcrafted term tiny but flips the residual strongly
negative. The scale-factor rule and the residual disagree about what a bare
minor is worth, and the residual wins.

Impact: low in practice, because search adjudicates KB vs K and KN vs K as
draws (75-F3). It still matters because the score is wrong in the direction
that *discourages* a minor-piece ending, and because nothing adjudicates the
sibling case that does reach play (75-F2).

---

## 75-F2 (SEARCH-REACHABLE ERROR) — KNN vs K scores +251 in search, but it is a draw

Of the five dead endings the brief named, exactly one wrong value survives
into search.

| ending | theory | static | search d6 | `is_insufficient_material()` |
|---|---|---|---|---|
| K vs K | draw | +2 | **cp 0** | true |
| KB vs K | draw | −147 | **cp 0** | true |
| KN vs K | draw | −104 | **cp 0** | true |
| **KNN vs K** | **draw** | **+187** | **cp 251** | **false** |
| KBN vs K | win | +237 | cp 272 | false |

`Board::is_insufficient_material()` (`src/board.cpp:1250-1258`) returns true
for `minor_count <= 1`, then requires `knights == 0` before accepting the
same-colour-bishop case. Two knights therefore fall through to `false`, so the
draw is never adjudicated and the +187 static error is carried into the
search as **+251 cp**.

This is the material inversion's practical consequence: the engine believes a
drawn KNN vs K is a quarter-pawn-plus win, and will steer toward it. It is not
a false *mate* score and it is not a crash, but it is a genuinely wrong
evaluation of a position the engine can reach in play.

The `DeadMaterial` option (default **false**) would zero K vs K, KB vs K and
KN vs K — but it does **not** cover KNN vs K either, so enabling it does not
fix this.

KBN vs K is the control that proves the tests can tell a win from a draw: it
is a real win, and it scores +237 static / cp 272 at depth 6. Correct.

---

## 75-F3 — dead-material verdict table against theory

`static_mismatches 5 / 7`, `search_mismatches 1 / 7`.

| ending | theory | static | verdict |
|---|---|---|---|
| K vs K | draw | +2 | error (nonzero) |
| KB vs K | draw | −147 | **error** |
| KN vs K | draw | −104 | **error** |
| KNN vs K | draw | +187 | **error** |
| KBN vs K | win | +237 | ok |
| K vs KB | draw | +141 | **error** |
| K vs KBN | win | −229 | ok |

Supplementary placements, same cold method: KBB vs K (win) +273 ok;
K vs KN (draw) +132, static error; KBN vs K with the other placement +174 ok.
Across all 13 dead-material readings, **9 static values are wrong and 1 search
value is wrong**.

Every "win" is scored as a win and every "draw" is scored *nonzero*, but the
sign is not reliably the strong side's: KB vs K is **−147** (wrong side of
zero), while K vs KB is **+141** (also wrong, because the side to move is the
weak side). The engine is not consistently pessimistic or optimistic about
bare minors — it is inconsistent, which is what a residual/handcrafted
disagreement looks like.

At search time all of these except KNN vs K collapse to a correct `cp 0`.

---

## 75-F4 (CLEAN) — the evaluation is exactly colour-mirror symmetric

This is the assignment's question 2, and the answer is unambiguous.

| corpus | compared | asymmetric |
|---|---|---|
| hand-picked position types | 20 | **0** |
| seeded random legal positions (seed 7502) | 400 | **0** |
| **total** | **420** | **0 / 420** |

Measured on the static `eval` command, so **no search and no move generation
is involved**. Any asymmetry here would have been an evaluation defect
distinct from the known movegen-order search effect. There is none.

The symmetry is exact **component by component**, not merely in the sum:
`hce` and `nnue` each match their mirror individually on all 420 pairs.

**The evaluation is therefore not the source of the colour-mirror asymmetry.**
That confirms the context the assignment supplied: the asymmetry is a
move-generation-order effect.

---

## 75-F5 (CLEAN) — the sign convention is correct, and it is genuinely side-to-move relative

A magnitude-only checker passes a sign bug, so this was tested with explicit
sign assertions and a planted-inversion control.

| case | total | expected |
|---|---|---|
| White queen up, White to move | **+825** | + |
| Black queen up, Black to move | **+825** | + |
| White queen up, Black to move | **−784** | − |
| Black queen up, White to move | **−784** | − |

`4 / 4` correct, mirror-equal in pairs, and sign distinguishes the
side-to-move flip (825 vs −784). Negative control: a stub engine with a
correct magnitude and an **inverted sign** is detected **4 / 4**, so the check
is not a magnitude test in disguise.

---

## 75-F6 (CLEAN) — the horizon is stable, and terminal scores are correct

**Horizon** (fixed imbalance, `d1..d10`): all three ladders settle —
`unsettled_at_last_step 0 / 3`. The queen ladder is stable from depth 1
onward (1257 … 1305) with no drift or oscillation, and the Black ladder
mirrors it (−1221 … −1247), bracketing within ~58 cp at every depth. Scores
sit above raw material (+257, +108) which is expected, since mobility, king
safety and pawn terms are on top of material.

**Terminal scores:**

| case | search score | bestmove | legal moves |
|---|---|---|---|
| checkmated, White to move | **mate 0** | `0000` | 0 |
| checkmated, Black to move | **mate 0** | `0000` | 0 |
| stalemate, Black to move | **cp 0** | `0000` | 0 |
| stalemate in corner | **cp 0** | `0000` | 0 |
| live control | cp 34 | `d2d4` | 20 |

`cases 5 · errors 0`. Checkmate is a typed `mate` score and never a
centipawn number; stalemate is `cp 0`; the two are **distinguishable**. That
is exactly the defect class repaired in 5.30.0 (`score mate 0` from a
restricted root) and it is **not** present. The brief's third case — no legal
move but not in check — is by definition stalemate, and is scored 0.

---

## 75-F7 (HARNESS DEFECTS, found and fixed) — three ways this audit could have produced a fake finding

The brief's warning about the `invalid FEN` diagnostic was correct and it bit
in a place I did not expect. Each of these was caught by the falsification
proof (`prove_harness.py`), and each would have corrupted the material study.

1. **The `invalid FEN` scan was in the wrong layer.** My first harness scanned
   the position reply inside `set_position()`, but the `sync()` barrier did
   not scan at all. Any direct engine call therefore consumed the diagnostic
   silently and left the engine holding the previous board. Fixed by moving
   the scan into `sync()`, so no caller can bypass it. Both streams are
   scanned: the position reply (when `isready` follows) and the `go` output.
2. **`chess.Board()` is not a validator.** It silently pads a five-field FEN
   to six and happily constructs positions that are illegal. A guard built on
   the board object alone passes a broken fixture. Fixed with `parse_fen()`,
   which validates the **raw text** (six fields), then `is_valid()`, then
   checks the canonical round-trip.
3. **A guard encoded a wrong expectation.** One test asserted that
   python-chess should reject a padded FEN; it legitimately normalises it. The
   test was replaced with the assertion that actually protects the study —
   that the board measured is not the previous one.

Additional defences in the harness, all exercised by the planted cases:

- every refusal (`invalid FEN`, `illegal move`, `invalid value for option`,
  `searchmoves restriction has no legal root moves`) **raises** rather than
  returning a number, because a refusal means the engine scored a different
  board;
- each `position` is independently confirmed by the engine's own `incheck`
  flag against python-chess, so a silently stale board is detected even when
  no diagnostic appears;
- every search is drained to `bestmove` or raises on timeout — no search is
  ever left open;
- every material step is asserted to **move** before it is recorded, so a
  silently refused FEN is reported as a fixture fault rather than as a
  material inversion.

Three material fixtures of mine were wrong and were caught this way (a
five-field FEN, two malformed rank strings, and one `.replace()` that deleted
*both* queens and left a zero balance). None reached the reported numbers.

---

## 75-F9 (MEASUREMENT DEFECT, found and fixed) — a warm transposition table changes fixed-depth scores

Search scores are **not** reproducible when several positions are searched in
one engine process. The same KBN-vs-K board returned:

| how measured | depth-6 score |
|---|---|
| 3rd search in a shared process | cp 293 |
| 2nd search in a shared process | cp 285 |
| 1st search in a shared process | cp 274 |
| fresh process, three separate runs | **cp 272, 272, 272** |

The TT carried from the previous search changes move ordering, which changes
which reductions and prunings fire, so a fixed *nominal* depth does not mean a
fixed *effective* search. The horizon ladder drifted the same way: warm
`1257…1282` against cold `1257…1305`.

Fixed by adding `cold_search()` / `cold_eval()` to the harness and using them
for every number that is reported as data: **one fresh process per
measurement**. The dead-material and horizon results in this report are cold
and reproducible.

This matters for the audit's own conclusions — a warm-TT comparison could
have manufactured a depth trend that does not exist, or hidden one that does.

---

## 75-F8 (MY OWN ERROR, withdrawn) — "two rooks and a bishop outrank a queen" is not an inversion

My first material run reported 2 inversions. The second was mine, not the
engine's: `PieceValueMg` is `{0, 82, 337, 365, 477, 1025, 0}`, so two rooks
plus a bishop is **1319 cp** against a queen's **1025 cp**. The engine
correctly prefers the two rooks and bishop. The pair was removed from the
ladder rather than reported, and the remaining 16 steps contain **1**
inversion.

Recorded because a withdrawn finding is the most useful evidence that the
other one was checked.

---

## Answers to the six questions

| # | question | answer |
|---|---|---|
| 1 | material monotonicity | **1 inversion / 16 steps.** K vs K +2 → KB vs K −147. Confined to bare-minor endings; monotonic with pawns present. |
| 2 | symmetry | **0 asymmetric pairs / 420.** `hce` and `nnue` each symmetric individually. Evaluation is not the asymmetry source. |
| 3 | dead material | KBN vs K **win, correct** (+237/272). KB vs K should be 0, engine says **−147**. KNN vs K should be 0, engine says **+187 static / +251 search**. `5/7` static, `1/7` search mismatches (9 of 13 static readings wrong across all placements). |
| 4 | sign convention | **Correct, side-to-move relative, 4/4.** Inverted-sign control detected 4/4. |
| 5 | horizon | **Stable, 0/3 unsettled (cold).** Converges above raw material as expected; Black mirrors White. |
| 6 | terminal scores | **Correct, 0 errors / 5 cases.** mate 0 / cp 0 / cp 0 distinguishable, `0000` bestmove. |

**Is the evaluation sane?** Symmetric, correctly signed and correctly
terminated — and materially misordered in bare-minor endings, with one case
(KNN vs K) that reaches search. Not a systemic failure; a specific, localised
one.
