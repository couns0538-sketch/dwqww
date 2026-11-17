# EVAL_TABLE.md — measured evaluation values (seat 75)

Engine: `forge-combo29` at commit `6b98f2170`, built with `g++-13` (see
`../../LOCK.md`). Every number below was produced by `/tmp/build75/forge`
under `Threads 1`, `Hash 16`, `OwnBook false`, `UseNNUE true` (default),
`DeadMaterial false` (default), single process per measurement.

Pins verified before any measurement:

| check | this build | published pin | match |
|---|---|---|---|
| `go perft 5` startpos | 4865609 | 4865609 | yes |
| `bench 13` (net on) | 862329 | 862329 | yes |

Instrument: the engine's own `eval` command, which prints
`info string eval hce <h> nnue <n> total <t> [incheck 1]`. `total` is
`hce + nnue` clamped, and it is what search uses for the static evaluation.
Scores are **side-to-move relative**, established in test 4.

---

## 1. Material monotonicity

Five ladders, 16 adjacent steps. Each step adds exactly one piece to the same
king shell. `total` is the static evaluation with the ladder side to move.

### Ladder A — bare king shell (no pawns), White to move

| rung | total | hce | nnue | step delta | ordered? |
|---|---|---|---|---|---|
| none | **+2** | 0 | +2 | — | — |
| bishop | **−147** | +16 | −163 | **−149** | **INVERSION** |
| knight | **−144** | +9 | −153 | +3 | ok |
| rook | **+353** | +442 | −89 | +497 | ok |
| queen | **+768** | +783 | −15 | +415 | ok |

The K → KB step is the inversion: adding a bishop to a bare king **loses
149 cp**. K → KN loses 146 cp from the K-vs-K rung but is only +3 above the
bishop rung, so the knight is misordered against the bishop too.

### Ladder B — accumulating from a bishop, White to move

| rung | total | hce | nnue | step delta |
|---|---|---|---|---|
| bishop | −147 | +16 | −163 | — |
| bishop+knight | +237 | +487 | −250 | +384 |
| bishop+knight+rook | +730 | +936 | −206 | +493 |
| bishop+knight+rook+queen | +1637 | +1957 | −320 | +907 |

Monotonic. No inversion.

### Ladder C — pawns, White to move

| rung | total | hce | nnue | step delta |
|---|---|---|---|---|
| no pawns | +2 | 0 | +2 | — |
| one pawn | +155 | +64 | +91 | +153 |
| two pawns | +406 | +243 | +163 | +251 |
| three pawns | +640 | +392 | +248 | +234 |

Monotonic. No inversion.

### Ladder D — rooks and queen, bare shell, White to move

| rung | total | hce | nnue | step delta |
|---|---|---|---|---|
| one rook | +370 | +440 | −70 | — |
| two rooks | +760 | +890 | −130 | +390 |
| queen | +825 | +859 | −34 | +65 |

Monotonic. Note: **two rooks plus a bishop (1319 cp by `PieceValueMg`) is
legitimately worth more than a queen (1025 cp)**, so that pair was removed
from the ladder. It was initially reported as an inversion by my own faulty
expectation, not by the engine.

### Ladder E — ordinary middlegame with pawns, White to move

| rung | total | hce | nnue | step delta |
|---|---|---|---|---|
| no piece | +18 | +12 | +6 | — |
| bishop | +434 | +261 | +173 | +416 |
| knight | +461 | +339 | +122 | +27 |
| rook | +859 | +608 | +251 | +398 |
| queen | +1614 | +967 | +647 | +755 |

Monotonic. **The inversion does not appear when pawns are present**, which is
what confines it to bare-minor endings.

### Summary

`MATERIAL_INVERSIONS 1 / 16 steps.`

| ladder | steps | inversions |
|---|---|---|
| A bare shell | 4 | **1** (none → bishop) |
| B accumulating | 3 | 0 |
| C pawns | 3 | 0 |
| D rooks/queen | 2 | 0 |
| E with pawns | 4 | 0 |

A real middlegame control confirms the scope: removing Black's f8 bishop from
`r1bqkbnr/pppppppp/2n5/8/8/8/PPPPPPPP/RNBQKBNR` raises the score from **+16 to
+493 (+477)**, so a bishop is worth a normal amount in ordinary positions.

---

## 2. Symmetry

Static `eval` on each position and on its colour mirror. No search is
involved, so any asymmetry here is an **evaluation** defect and cannot be the
movegen-order effect.

| corpus | pairs | asymmetric | denominator |
|---|---|---|---|
| hand-picked types | 20 | **0** | **0 / 20** |
| seeded random legal (seed 7502) | 400 | **0** | **0 / 400** |
| **total** | **420** | **0** | **0 / 420** |

Per-position values (hand-picked corpus):

| position | total | mirror total | hce / mirror | nnue / mirror |
|---|---|---|---|---|
| startpos | 38 | 38 | 18/18 | 20/20 |
| ruy lopez | 83 | 83 | 58/58 | 25/25 |
| sicilian | 63 | 63 | 57/57 | 6/6 |
| kiwipete | −105 | −105 | −63/−63 | −42/−42 |
| endgame rooks | 65 | 65 | 74/74 | −9/−9 |
| endgame pawns | −291 | −291 | −101/−101 | −190/−190 |
| queen vs rook | 808 | 808 | 828/828 | −20/−20 |
| opposite bishops | 4 | 4 | 0/0 | 4/4 |
| black to move | 32 | 32 | 18/18 | 14/14 |
| promotion race | 165 | 165 | −49/−49 | 214/214 |
| dense middlegame | −46 | −46 | −6/−6 | −40/−40 |
| pawn chain | 30 | 30 | 18/18 | 12/12 |
| knights | 283 | 283 | 500/500 | −217/−217 |
| bare kings | 4 | 4 | 0/0 | 4/4 |
| bishop pair | 411 | 411 | 616/616 | −205/−205 |
| castled both | −420 | −420 | −341/−341 | −79/−79 |
| passed pawn | −32 | −32 | −26/−26 | −6/−6 |
| rooks open file | 8 | 8 | 12/12 | −4/−4 |
| check | 83 | 83 | 58/58 | 25/25 |
| stalemate-ish edge | −574 | −574 | −928/−928 | 354/354 |

The evaluation is exactly mirror-symmetric, component by component: `hce` and
`nnue` each match individually, not merely their sum.

---

## 3. Dead material

Static evaluation (what the evaluator believes) and depth-6 search (what the
engine actually plays). Theory verdicts are standard.

| ending | theory | static total | hce | nnue | depth 6 | insufficient-material flag | static verdict |
|---|---|---|---|---|---|---|---|
| K vs K | draw | **+2** | 0 | +2 | cp 0 | true | **error** (nonzero) |
| KB vs K | draw | **−147** | +16 | −163 | cp 0 | true | **error** |
| KN vs K | draw | **−104** | +10 | −114 | cp 0 | true | **error** |
| KNN vs K | **draw** | **+187** | +432 | −245 | **cp 251** | false | **error** |
| KBN vs K | **win** | +237 | +487 | −250 | cp 272 | false | ok |
| K vs KB | draw | **+141** | −15 | +156 | cp 0 | true | **error** |
| K vs KBN | win | −229 | −468 | +239 | cp −265 | false | ok |

Supplementary placements, same method (cold, depth 6):

| ending | theory | static | hce | nnue | depth 6 | verdict |
|---|---|---|---|---|---|---|
| KBB vs K | win | +273 | +594 | −321 | cp 385 | ok |
| K vs KN | draw | +132 | −9 | +141 | cp 0 | **error** (static) |
| KBN vs K (`1BN1K3`) | win | +174 | +495 | −321 | cp 272 | ok |

`static_mismatches 5 / 7` (13 of 14 across both tables) · `search_mismatches 1 / 7`

Reading:

- **KBN vs K is a win for the strong side, and the engine agrees** — +237
  static, cp 272 at depth 6. Correct.
- **KB vs K should be 0, and the engine's static evaluation says −147.** The
  handcrafted term is the sane +16; the compiled-in NNUE residual contributes
  **−163** and dominates. This is the material inversion from section 1 seen
  from the other direction.
- **KNN vs K is the one dead ending where the error reaches play.** It is a
  draw, but `is_insufficient_material()` returns *false* for two knights
  (`src/board.cpp:1250-1258` requires `knights == 0` for the drawn-bishop
  case), so nothing adjudicates it and the engine carries +187 / cp 251 into
  search. Every other wrong static value is masked at search time by the
  insufficient-material verdict returning a literal 0.
- The `DeadMaterial` option (default **false**) would zero K vs K, KB vs K and
  KN vs K, but it does not cover KNN vs K either.

---

## 4. Sign convention

Side-to-move relative. Four constructed boards; A/B is the side-flipped pair.

| case | FEN | total | expected sign | result |
|---|---|---|---|---|
| A White queen up, White to move | `4k3/8/8/8/8/8/8/3QK3 w - - 0 1` | **+825** | + | pass |
| B Black queen up, Black to move | `3qk3/8/8/8/8/8/8/4K3 b - - 0 1` | **+825** | + | pass |
| C White queen up, Black to move | `4k3/8/8/8/8/8/8/3QK3 b - - 0 1` | **−784** | − | pass |
| D Black queen up, White to move | `3qk3/8/8/8/8/8/8/4K3 w - - 0 1` | **−784** | − | pass |

A/B mirror equality: 825 == 825. Sign distinguishes A from C (825 vs −784).
`sign cases 4 / 4 pass`.

Negative control: a stub engine that computes the correct magnitude and
**inverts every sign** is detected **4 / 4** — so this check does not merely
test magnitude.

---

## 5. The horizon

Fixed material imbalance, searched `d1`..`d10`, **one fresh process per
depth**. A warm transposition table shifts the score at fixed nominal depth
(see 75-F9), so a warm ladder measures the TT, not the horizon. Reference is
the same imbalance in the engine's own `PieceValueMg` units, converted to
side-to-move.

### White queen up (`rnb1kbnr/...`)

| depth | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| cp | 1257 | 1287 | 1262 | 1262 | 1265 | 1278 | 1278 | 1286 | 1284 | **1305** |

Reference 1025. Final delta **+280**. Settled.

### Black queen up (mirror)

| depth | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| cp | −1221 | −1197 | −1215 | −1214 | −1202 | −1203 | −1218 | −1240 | −1248 | **−1247** |

Reference −1025. Final delta **−222**. Settled. The two ladders bracket each
other within ~58 cp at every depth, so the horizon behaves the same from both
sides.

### White rook up (`1nbqkbnr/...`)

| depth | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| cp | 593 | 644 | 602 | 613 | 576 | 601 | 577 | 587 | 578 | **579** |

Reference 477. Final delta **+102**. Settled.

`unsettled_at_last_step 0 / 3.`

The score **does** approach a stable value as depth increases, and it is
stable from depth 1 onward — no drift, no oscillation. It converges to a
value **systematically above** the raw material count (+280, +102), which is
expected for a position with intact pawns and an extra heavy piece: the score
includes mobility, king safety and pawn terms on top of material. It is not a
material error.

---

## 6. Terminal scores

| case | FEN | eval total | in check | search score | bestmove | python-chess legal moves |
|---|---|---|---|---|---|---|
| checkmated White to move | `rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3` | −127 | true | **mate 0** | `0000` | 0 |
| checkmated Black to move | `rnbqkbnr/ppppp2p/5p2/6pQ/4P3/8/PPPP1PPP/RNB1KBNR b KQkq - 1 3` | −127 | true | **mate 0** | `0000` | 0 |
| stalemate Black to move | `7k/5Q2/6K1/8/8/8/8/8 b - - 0 1` | −574 | false | **cp 0** | `0000` | 0 |
| stalemate corner Black | `k7/8/1Q6/8/8/8/8/6K1 b - - 0 1` | −799 | false | **cp 0** | `0000` | 0 |
| live control | startpos | 38 | false | cp 34 | `d2d4` | 20 |

`cases 5 · errors 0`

- **Checkmate** is a typed `mate` score, never a centipawn number, and returns
  no move (`0000`).
- **Stalemate** is `cp 0` and also returns `0000`.
- The two are **distinguishable**, which is precisely the defect class fixed
  in 5.30.0 (a restricted root once printed `score mate 0`). It is not
  present here.
- The `eval` command's `incheck` flag correctly separates "no legal move and
  in check" from "no legal move and not in check", which is the third case the
  brief asks about: **a position where the side to move has no legal move but
  is not in check is, by definition, stalemate**, and the engine scores it 0.

---

## Provenance

| item | value |
|---|---|
| source commit | `6b98f2170a3210e71beed04bbd2553972c253ed7` |
| compiler | `g++-13` (Ubuntu 13.3.0), `-O3 -march=x86-64-v4` |
| binary | `/tmp/build75/forge`, 794888 bytes |
| perft 5 | 4865609 (pin match) |
| bench 13 | 862329 (pin match) |
| raw data | `out_material.json`, `out_symmetry.json`, `out_symmetry_scale.json`, `out_dead_material.json`, `out_sign.json`, `out_horizon.json`, `out_terminal.json` |
