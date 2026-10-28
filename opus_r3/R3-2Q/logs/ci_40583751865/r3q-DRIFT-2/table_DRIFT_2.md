metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs (a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRIFT | SW | 2 | Intel(R) Xeon(R) 6973P-C (AVX-512) | d16 yes; d20 yes | -0.63 [-2.87, +1.65] | +0.43 [-2.57, +3.52] | +3.18 [+0.93, +5.47] | +1.23 [-0.12, +2.59] | not met | -0.72 / +0.48 | 8.9 / 13.5 | H3DRIFT -4.61 [-5.20, -4.01] (base_h3 vs base) |

files: 2; runs with a node-rule or exit failure: 0
