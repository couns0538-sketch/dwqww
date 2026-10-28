metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs (a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LAZY | SW | 3 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | +1.96 [-0.83, +4.84] | -1.84 [-3.81, +0.17] | +0.30 [-0.59, +1.20] | +1.43 [-2.05, +5.05] | not met | +0.78 / -1.65 | 14.0 / 8.8 | +4.36 [+2.92, +5.81] |
| LAZY | OPT | 3 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | +0.29 [-1.40, +2.01] | +1.66 [-0.77, +4.15] | +0.30 [-0.59, +1.20] | +1.43 [-2.05, +5.05] | not met | +0.04 / +0.93 | 6.4 / 7.0 | -1.05 [-2.52, +0.44] |

files: 3; runs with a node-rule or exit failure: 0
