# S31 idea sources

- Spec: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 15 and Sol's inventory (S31, spec line 496): average the last k
  epoch nets of one run in float, export an `.inc`, check parity, score each arm on the same holdout. Resume rework:
  "accept any 2+ .pt files from one run".
- Checkpoint (weight) averaging: Polyak & Juditsky (1992) iterate averaging; Izmailov et al., "Averaging Weights
  Leads to Wider Optima and Better Generalization" (SWA, 2018). Here it is a cheap offline test on finished runs; no
  training is started.
- The quantization and text layout follow the trainer's `export_forge` (`.inc` files of the runs), checked by
  reproducing the trainer's own `.inc` md5 from one input (`.inc`, `.bin` and `.pt` paths).
- The holdout metric is the trainer's (`T.evaluate` in the archive's `eval_inc.py`), re-implemented in numpy. The
  network forward equals the engine's: S21 validated it against `forge::nnue`, and the parity step here checks it.
