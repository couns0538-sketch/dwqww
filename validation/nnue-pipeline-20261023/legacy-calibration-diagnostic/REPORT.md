# Legacy training-label calibration diagnostic

Actual diagnostic and immutable full native probe both exited 0 with empty stderr. This is a descriptive **legacy TRAINING-ONLY** label-agreement result; it does not authenticate the unknown producer or establish calibration, validation performance or playing strength.

Exactly 1,000 physical rows were selected from each of nine files, at stride 1,500 with a per-file offset from `Random(20261023)` over sorted source paths. All nine complete source SHA256 hashes matched the existing inventory during the single streaming selection pass; original line bytes and FEN counters are retained. There were 718 rows outside the predeclared absolute 1,000-cp teacher-score cap. Only the remaining 8,282 FENs were sent to the original shipped-network probe, with thread limits 1. No game IDs, new split, holdout, de-duplication, training or model selection were introduced.

Pure teacher probability is `sigmoid(scoreSTM * 2.25 / 400)`, with float64 diagnostic arithmetic and no game-result mixing. HCE is the actual native uncached HCE. The shipped hybrid adds the native integer NNUE correction and clamps the combined score to ±31,871 cp; native inference already truncates and clamps its correction to ±30,000 cp.

| Subset | Positions | HCE MSE | Shipped hybrid MSE | Relative sample MSE reduction |
|---|---:|---:|---:|---:|
| Score capped | 8282 | 0.005167876101 | 0.004979462879 | 3.645854% |
| Score capped + conservative quiet filter | 1350 | 0.004046881167 | 0.003955952792 | 2.246875% |

The conservative filter rejects any position in check, terminal under the FEN-observable probe rules, or having any legal capture, promotion or checking move. Among score-capped sampled positions, 6,932 had a tactical legal move; none was in check or terminal. This leaves 1,350 eligible positions. Filter counts can overlap in the general protocol.

| Source | Offset (0 based) | Capped | Quiet eligible | Quiet HCE MSE | Quiet hybrid MSE | Relative quiet sample reduction |
|---|---:|---:|---:|---:|---:|---:|
| forge_selfplay_003_head.txt | 518 | 915 | 137 | 0.004625354 | 0.004047398 | 12.4954% |
| forge_selfplay_004_head.txt | 541 | 906 | 145 | 0.003982113 | 0.003474353 | 12.7510% |
| forge_selfplay_005_head.txt | 413 | 926 | 156 | 0.003703937 | 0.003711602 | -0.2070% |
| forge_selfplay_006_head.txt | 1092 | 935 | 147 | 0.006282169 | 0.006458530 | -2.8073% |
| forge_selfplay_007_head.txt | 722 | 911 | 154 | 0.003557066 | 0.003445434 | 3.1383% |
| forge_selfplay_008_head.txt | 492 | 908 | 126 | 0.002224604 | 0.002614497 | -17.5264% |
| forge_selfplay_009_head.txt | 1173 | 932 | 178 | 0.004053111 | 0.004418956 | -9.0263% |
| forge_selfplay_010_head.txt | 751 | 934 | 146 | 0.004138975 | 0.004026721 | 2.7121% |
| forge_selfplay_013_head.txt | 46 | 915 | 161 | 0.003708598 | 0.003225768 | 13.0192% |

The shipped hybrid has lower sample probability MSE in 7/9 sources on the score-capped subset and 5/9 sources after the conservative filter. These heterogeneous per-source results are preserved rather than treated as independent-game evidence.

The target correction is `teacher_cp_stm − native_HCE_cp_stm`. On the score-capped subset it has mean 0.518 cp, median −3 cp, population standard deviation 93.103 cp, 5th/95th percentiles −127.95/+138 cp, and range −884..+1,018 cp. On the conservative subset it has mean −14.254 cp, median −7 cp, standard deviation 102.344 cp, 5th/95th percentiles −164.1/+106.1 cp, and range −692..+763 cp. Full distributions, remaining error after correction and per-source distributions are in `RESULT.json`. Percentiles use linear interpolation.

Unknown search depth, original evaluator calibration and game identity remain unresolved. Label/static-evaluator agreement cannot resolve those provenance questions. No confidence interval is claimed because authentic game clusters are absent. These numbers do not prove generalization or Elo and do not constitute a gate for accepting a trained network.

Preserved evidence: `diagnose.py`; `INPUTS.json`; complete-source SHA/stat receipts; exact selected original lines per file; source-line and original-line hash bindings; original probe stdin/stdout/stderr and process receipt; all per-row scores/probabilities/losses/filter flags; per-source metrics and residual distributions. The diagnostic rehashed its script, original probe, shipped include, probe source and relevant engine sources after execution. All remained unchanged.
