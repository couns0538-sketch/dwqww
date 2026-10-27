# S21 int16 range study + research-only clipped export

**RESEARCH ONLY.** There is no int16 engine path and no engine patch. AL1 inference is float with exact
accumulation; an int32 port is safe (CR's table); this study measures what an **int16** accumulator would face.

```sh
# range study: nets x positions (.pos files, or "FEN | ..." text)
python -I -B forge_sol_S21_int16range.py study --nets <13 .inc files> --pos t00000.pos t01000.pos t02000.pos t03000.pos --out study.json
# research export: W1/B1 rescaled so every accumulator fits int16, with its float-parity loss
python -I -B forge_sol_S21_int16range.py export --net net.inc --pos <...> --mode bound|observed --out net_int16clip.inc
# check the Python forward against the engine's forge::nnue (builds the archive's nnue_check.cpp per net)
python -I -B forge_sol_S21_engine_parity.py --nets <.inc> --fens sample.txt --lock-tree <AL1 tree> --harness nnue_check.cpp --work <dir> --out parity.json
```
Run with the NNUE venv python (numpy) and `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`.

- **Accumulator:** per perspective `acc = B1 + Σ W1[f]` (int units of 1/4096) over the active features
  `f = (rel·6 + type)·64 + sq'` (`rel` = piece colour ≠ perspective, `sq' = sq ^ 56` for black), as in the
  trainer's `features()` and `forge::nnue`. Network cp = `(W2[:256]·clamp(acc_stm/4096,0,1)² + W2[256:]·clamp(acc_opp/4096,0,1)² + B2) / 4096 · 400 / 2.25`.
- **study:** min/max/max|acc|, quantiles (exact histogram, bins of 64), values / positions / lanes with
  `|acc| > 32767`, positions whose output changes under int16 *wrapping* arithmetic, and CR's weight-only bounds
  (`max|w1|`, `|b1| + top-32|w1| + 4·max|w1|`, `|b1| + Σ|w1|`).
- **export:** `a = 32767 / bound`; `W1' = round(a·W1)`, `B1' = round(a·B1)` (half away from zero); W2/B2 unchanged;
  activation `clamp(acc'/(4096·a), 0, 1)²`. `bound`: the 32-feature worst case (guaranteed for any legal position);
  `observed`: the largest |acc| on the given positions (not guaranteed). The `.inc` starts with `#error`, so the
  engine cannot be built with it; its float-parity loss (network cp vs the original net) is written into the file
  and into `<out>.json`.
- **Deterministic:** integer accumulation, fixed order, float64 outputs.

Tests: `python -I -B test_forge_sol_S21_int16range.py` (`S21_NETS_DIR` = the lock archive's
`5_nnue/nets/history_all_CR_passed` for the CR-table check).
