# T06C candidates (every candidate: idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict)

| # | idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict |
|---|---|---|---|---|---|---|
| 1 | Re-fit the HCE table under the frozen residual net (Texel loss on HCE + net, net fixed) | Ethereal b552e36 https://github.com/AndyGrant/Ethereal/commit/b552e36f88 | GPL-3.0 ideas only | STC +6.75+-4.22 (10+0.1s, 10,240 g, [0,4]) / LTC +7.06+-3.88 (60+0.6s, 8,464 g) after a residual pawn-king net (513a93c) | tuner tools/tune/texel.cpp has no per-row net term; lock search.cpp:620 sums HCE + net | CARD T06C-01 |
| 2 | Alternate: retrain / fine-tune the residual net on the re-fitted HCE (.hce regenerated) | Ethereal 8d02577 https://github.com/AndyGrant/Ethereal/commit/8d02577b5f | GPL-3.0 ideas only | net retrained after the HCE re-tune: STC +4.72+-3.63 (14,640 g, [0,5]) / LTC +2.71+-2.17 (29,072 g) | residual loss uses a fixed per-row .hce (skill forge-nnue-data) | CARD T06C-02 |
| 3 | Fit the non-linear HCE parts (king-danger unit weights, scale factor) by gradient instead of fixed integers | Clockwork 753f884 https://github.com/official-clockwork/Clockwork/commit/753f88460c | AGPL-3.0 ideas only | king-safety sigmoid STC +9.59+-4.45 (7,940 g) / LTC +9.78+-4.37 (7,320 g), HCE-only engine | include/forge/eval_params.hpp:68-79 KingSafetyWeights are fixed ints (texel.cpp --king-safety sets, never fits) | CARD T06C-03 (one-line) |
| 4 | Full re-tune on new own self-play data (no net) | Ethereal 6771685 https://github.com/AndyGrant/Ethereal/commit/6771685315 ; Clockwork 2844edc | GPL-3.0 / AGPL-3.0 ideas only | Ethereal +10.51+-5.37 / +12.75+-5.34; Clockwork +6.67+-3.62 / +11.88+-4.80 (HCE-only engines) | table from 61,536 games / 4.67M positions at 10k nodes (eval_params_table.inc:1) | evidence for T06C-01 (data); standalone HCE re-tune with the old net = double correction, dropped |
| 5 | Texel's original method (qsearch score, game result, K fitted) | https://www.chessprogramming.org/Texel%27s_Tuning_Method | CC BY-SA 3.0 text | Texel 1.03 series +99.6 total over 7 steps, 32,000 games each at 1+0.08, no error bars | Forge has it (tools/tune/texel.cpp, Adam + coefficient trace) | EXISTS - no card |
| 6 | Re-tune search margins after an eval re-tune | Ethereal c495be4 https://github.com/AndyGrant/Ethereal/commit/c495be4918 | GPL-3.0 ideas only | STC +4.66+-3.22 (15,600 g) / LTC +2.49+-1.90 (31,232 g) | SPSA tooling exists (skills forge-o30-spsa, forge-spsa-tuning) | step inside T06C-01 test plan, no card |
| 7 | Classical-eval re-tune in a switch-hybrid (classical used only in imbalanced positions) | Stockfish e0bafa1, 767b4f4 https://github.com/official-stockfish/Stockfish/commit/e0bafa1911 | GPL-3.0 ideas only | e0bafa1 tested NNUE=False (STC ~+6.4 / LTC ~+1.3, classical only); 767b4f4 STC 252,696 g / LTC 48,184 g (~+0.9 / ~+2.6) | Forge is a residual sum, not a switch | dead end (other hybrid form) |
| 8 | Second small augmenting net for one material class (R+P endgames) | Ethereal 3112e84 https://github.com/AndyGrant/Ethereal/commit/3112e84ccb | GPL-3.0 ideas only | STC +5.46+-3.91 (11,072 g) / LTC +3.36+-2.55 (18,176 g) | 30-Oct round already covered a small second net | dropped (already reported) |
| 9 | Drop / limit the HCE beside a strong full-board net (switch hybrid) | Ethereal 5e25d42 https://github.com/AndyGrant/Ethereal/commit/5e25d42142 | GPL-3.0 ideas only | HCE path disabled: STC +11.06+-6.70 (5,216 g) / LTC +8.46+-5.60 (7,024 g); HCE only for psqtmat > 2000: +0.22+-1.90 (62,056 g, [-3,1]) | Forge is a residual sum (search.cpp:620); standalone nets are a separate line (skill forge-nnue-v3) | risk evidence only, not this sub-track |
| 10 | Joint fit inside the net trainer (HCE table as a trainable linear skip layer, back-propagated with the net) | one web search; no engine or paper found | - | none logged | trainer reads hce_cp as a fixed per-row constant (skill forge-nnue-data) | dead end for a card (no logged evidence); T06C-01 + T06C-02 is the logged-evidence route (alternation) |

## Answers to the brief (short)
- Logged gains of HCE weight tuning: Texel 1.03 series +99.6 over 7 steps (32,000 games each, 1+0.08, no error bars, CPW);
  Ethereal full re-tunes +3..+13 Elo each at STC and LTC (rows 1, 4, 6; 30 tuning commits mined); Clockwork data
  refreshes +2..+12 (row 4).
- Re-fit of an HCE under a residual / hybrid net: Ethereal 2020-09 (row 1): residual pawn-king net (513a93c, trained
  offset by the static eval) -> net retrain -> full HCE re-tune b552e36 (+6.75 / +7.06) -> net retrain 8d02577
  (+4.72 / +2.71, confounded). How the tuner treated the net output is not in the commit text (missing). Stockfish
  re-tuned classical terms only in a switch hybrid (row 7; one of them tested with NNUE off).
- Cost here: T06C-01 crew ~6 h + CPU ~2-4 h fit + STC/LTC SPRT; T06C-02 crew ~6 h + CPU ~10 h per 1G presentations
  fine-tune (+ .hce regeneration) + STC/LTC SPRT. Data: own self-play FPOS + .hce (licence clean).
- Risk: (a) a stand-alone re-tune shipped with the old net double-counts (dropped, row 4); (b) the frozen-net refit
  can only lower the training loss but its room is what the 768-input net left uncorrected (lock holdout b0.6:
  HCE alone 0.017059 -> HCE + net 0.014310); (c) after a net fine-tune the sum can drift back (the net re-absorbs the
  change); (d) eval-scale shift vs search margins (row 6); (e) with a strong net the HCE itself can be a liability (row 9).
