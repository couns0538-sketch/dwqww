metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs (a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| INT16 | SW | 3 | AMD EPYC 9V74 80-Core Processor (AVX-512) | d16 yes; d20 yes | -0.40 [-1.68, +0.89] | +0.03 [-1.30, +1.38] | +0.29 [-0.03, +0.61] | -0.12 [-1.54, +1.32] | not met | +0.08 / -0.28 | 3.4 / 4.3 | +1.79 [+0.70, +2.89] |
| INT16 | OPT | 3 | AMD EPYC 9V74 80-Core Processor (AVX-512) | d16 no (tree changes: NPS only); d20 no (tree changes: NPS only) | -6.92 [-7.63, -6.19] | -12.32 [-13.27, -11.35] | +0.29 [-0.03, +0.61] | -0.12 [-1.54, +1.32] | not met | -6.95 / -12.47 | 6.3 / 4.0 | -8.78 [-9.88, -7.66] (tree changes) |

files: 3; runs with a node-rule or exit failure: 0
