metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs (a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| INT16 | SW | 4 | AMD EPYC 9V74 80-Core Processor (AVX-512) | d16 yes; d20 yes | -0.95 [-1.40, -0.50] | -0.66 [-1.01, -0.30] | -0.08 [-0.66, +0.51] | +0.06 [-0.88, +1.01] | not met | -1.15 / -0.46 | 1.7 / 1.9 | +1.79 [+0.70, +2.89] |
| INT16 | OPT | 4 | AMD EPYC 9V74 80-Core Processor (AVX-512) | d16 no (tree changes: NPS only); d20 no (tree changes: NPS only) | -7.61 [-8.34, -6.88] | -12.32 [-12.99, -11.65] | -0.08 [-0.66, +0.51] | +0.06 [-0.88, +1.01] | not met | -7.76 / -12.14 | 2.6 / 1.7 | -8.78 [-9.88, -7.66] (tree changes) |

files: 3; runs with a node-rule or exit failure: 0
