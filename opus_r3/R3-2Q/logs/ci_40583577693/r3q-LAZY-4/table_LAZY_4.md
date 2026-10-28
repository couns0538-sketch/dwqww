metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs (a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LAZY | SW | 4 | Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz (AVX-512) | d16 yes; d20 yes | +0.19 [-0.03, +0.41] | +0.50 [+0.33, +0.67] | +0.04 [-0.30, +0.38] | +0.08 [-0.18, +0.35] | not met | +0.19 / +0.44 | 1.2 / 0.8 | +4.36 [+2.92, +5.81] |
| LAZY | OPT | 4 | Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz (AVX-512) | d16 yes; d20 yes | -0.21 [-0.58, +0.17] | -0.17 [-0.30, -0.04] | +0.04 [-0.30, +0.38] | +0.08 [-0.18, +0.35] | not met | -0.29 / -0.14 | 1.5 / 0.4 | -1.05 [-2.52, +0.44] |

files: 3; runs with a node-rule or exit failure: 0
