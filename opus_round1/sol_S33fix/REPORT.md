# S33fix — S33-1: every advice table labelled "approx model", only fastchess figures quoted — DONE

Branch `opus-sol-S33fix` = `d4f4312` + CI baseline (cherry-pick 0b1f29bd) + f58b3124 (job folder only; tool-only diff empty).
Sol's S33 files are unchanged; v2 files are new. Advice only. Machine exclusive: no.

## Acceptance
| line | result | evidence |
|---|---|---|
| label every advice table "approx model" | DONE: advice_net/search/speed v2 (tables and every model number labelled); 630-cell plan table v2 rendered from Sol's CSV (data rows byte-identical; label in title, caption and headers; CSV gains model_label) | forge_sol_S33_*_v2_20261027.*; test_render_keeps_numbers_and_adds_labels |
| quote only fastchess figures | DONE: gate figures appear only as printed in RESULT.md (G119 Elo 9.50 +/- 8.84, LLR 1.72; never the Gaussian 1.727094) | checker rule 2 |
| checker (render + check) | Sol's advice_net table and plan table FAIL (unlabelled); the 4 v2 docs PASS | logs/check_sol_original_docs.log, logs/check_v2_docs.log |
| cross-check: approx model vs exact fastchess 1.8.2 GSPRT stopping rule (same G119 shape and tilt, 20,000 runs per cell) | P(H1) exact minus approx: [0,10]/1500 -0.0032, /2500 -0.0102, /3000 -0.0034, [0,5]/4000 -0.0090, true+20 [0,10]/1500 +0.0005. V1 true+9.5: exact P(cap) 0.82865 vs approx 0.8177 (cap most likely in both) | logs/approx_vs_exact_v2.json; table in advice_net v2 |
| tests | 11 OK | logs/tests_v2.log |
| planted bugs | 4/4 caught | logs/mutants_v2.log |

## Findings
- The Gaussian approximation is slightly optimistic for H1 (by up to about 1 point) on these cells; the advice holds under both models.
- Exact GSPRT reproduces the printed LLRs (G119 1.72, G100r 2.22, G95 -0.56).

## Left / UNVERIFIED
- Planner code unchanged (its JSON already says exact_fastchess false); future tables should go through `render`.
- scipy-based analytic parts not run on the PC (no scipy in the venv).
- Exact cross-check covers 6 cells, G119 shape only.
