# S44 idea sources

- **Spec:** `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 26 and Sol's inventory (`jobs[]` id S44, spec line 231):
  every net gate as an unpooled effect-size point, data size from the settings dumps, gate-row citations, the
  e64/e96-vs-more-data advice with a range. Resume rework: "add G120/G120c and bias-corrected Elo; keep conc 5 and
  conc 7/8 apart".
- **S30** (branch `opus-sol-S30`): per-run holdout b0.6 lines, settings-dump data sizes, the fixed-data epoch curve
  `L(E) = Linf + A E^-alpha` (alpha grid 0.1..3) and the e48 data curve `b06 = c + s ln(positions)`; reused and
  refit here (L64 reproduced to 1e-12).
- **fastchess 1.8.2 SPRT:** the normalized-Elo GSPRT on pentanomial pairs. Its LLR is the exact log-likelihood ratio
  of the constrained MLEs (Michel Van den Bergh's "normalized Elo" note; fishtest `LLRcalc.MLE_tvalue` and
  `secular`), reproduced here to the printed rounding on all 23 net gates. The Gaussian approximation is up to
  0.1 off at H1 stops.
- **Bias of estimates after a sequential test:** J. Whitehead, "On the bias of maximum likelihood estimation
  following a sequential test", Biometrika 73 (1986): the bias-adjusted estimate solves
  `E_theta[estimate at stop] = observed`. The verdict-conditional bias ("winner's curse") is the quantity of Sol's
  S48; both are reported here.
- **Exponential tilting** of the observed pentanomial profile to a target mean: the maximum-entropy member of the
  profile's family with that mean, a standard way to simulate "the same match at another true strength".
- **Gate data:** the PC's own RESULT.md / RUN_INFO.json per gate (read-only copies), the 13:35 snapshot rows, and
  `LATEST_GATE_FACTS_20261026.md` for gates after the snapshot.
