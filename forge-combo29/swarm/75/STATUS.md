# STATUS — seat 75, evaluation sanity audit

Branch `for-fable-and-opus/swarm-75`, folder `forge-combo29/swarm/75/`.
Base commit `6b98f2170a3210e71beed04bbd2553972c253ed7`.

## Deliverables

| file | contents |
|---|---|
| `FINDINGS.md` | 75-F1..F9, answers to all six questions |
| `EVAL_TABLE.md` | every measured number, with denominators |
| `STATUS.md` | this file |
| `harness.py` | synchronized UCI harness |
| `prove_harness.py` | falsification proof for the harness |
| `test1_material.py` | material monotonicity, 5 ladders / 16 steps |
| `test2_symmetry.py` | symmetry, 20 hand-picked positions |
| `test2b_symmetry_scale.py` | symmetry, 400 seeded random positions |
| `test3_dead_material.py` | dead material vs theory, static + search |
| `test4_sign.py` | sign convention + inverted-sign control |
| `test5_horizon.py` | depth ladder d1..d10, three imbalances |
| `test6_terminal.py` | checkmate / stalemate / no-legal-move |
| `prove_symmetry_can_fail.py` | negative control for test 2 |
| `prove_tests_3_5_6_can_fail.py` | negative controls for tests 3, 5, 6 |
| `out_*.json` | raw measurements |

## Headline

**Material inversion confirmed:** K vs K scores **+2**, KB vs K scores
**−147**. Adding a bishop to a bare king costs **149 cp**. Cause: the NNUE
residual term (−163) overwhelms the handcrafted term (+16); `scale_factor()`
almost annihilates the handcrafted term for bare minors.

**Dead-material error that reaches search:** KNN vs K is a draw but scores
**+187 static / +251 at depth 6**, because `is_insufficient_material()`
returns false for two knights. The other wrong bare-minor statics are masked
at search time by the insufficient-material adjudication.

**Clean:** symmetry **0 / 420**, sign **4 / 4**, horizon **0 / 3 unsettled**,
terminal **0 errors / 5 cases**, KBN vs K correctly a win.

## Build and pins

Built with `g++-13` (`clang++` cannot find `libstdc++` in this image).
Pins matched before any measurement: `perft 5 = 4865609`, `bench 13 = 862329`.

## Method notes

- Static numbers come from the engine's own `eval` command
  (`hce` / `nnue` / `total`), so material, symmetry and sign are measured
  without search or move generation interfering.
- Every reported search number is **cold: one fresh process per measurement**.
  A warm TT changes fixed-depth scores (75-F9: cp 274/285/293 warm against
  272 cold, three times identically).
- Every FEN validated as raw text (six fields) and by python-chess
  `is_valid()`, then confirmed by the engine's own `incheck` flag.
- Both the position reply and the `go` output are scanned for `invalid FEN`.
- Every search drained to `bestmove`; timeout is an error, never a score.
- Threads 1, Hash 16, OwnBook false.
- Every test proven able to fail by a planted-defect stub engine:
  harness guards 11/11, symmetry 3/3, sign 4/4, tests 3/5/6 all caught.

## Honest limits

- The "reference" in the horizon ladder is the engine's own `PieceValueMg`,
  not a ground truth; bare chess has no oracle for the value of a queen up.
  Deviations are reported, not asserted away.
- Symmetry was measured on 420 positions, not exhaustively. It is evidence,
  not proof.
- The KNN vs K finding is a wrong *score*, not a demonstrated game-level loss
  of Elo. No SPRT was run and none is claimed.
- Only the evaluation was audited. Search, movegen, time management and
  pondering are out of scope by assignment.

## Next natural steps

1. Ask whether `scale_factor()`'s bare-minor branch should suppress the NNUE
   residual as well as the handcrafted term — that is the shape of 75-F1.
2. Ask whether two knights should be added to `is_insufficient_material()` or
   to `dead_material_score()` — that is 75-F2. Care needed: KNN vs K is
   drawn but KNN vs KP is not always, so the test must be material-complete.
