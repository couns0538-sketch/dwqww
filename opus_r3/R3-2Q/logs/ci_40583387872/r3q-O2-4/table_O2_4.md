metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs (a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| O2 | SW | 4 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +3.13 [+2.39, +3.88] | +3.45 [+2.42, +4.49] | -0.04 [-0.73, +0.64] | -0.30 [-0.99, +0.39] | MET | +3.13 / +3.66 | 2.4 / 3.1 | +0.13 [-0.24, +0.51]; d20 -0.05 [-1.23, +1.15] (other head +3.04 [+2.15, +3.94]) |

files: 2; runs with a node-rule or exit failure: 0
