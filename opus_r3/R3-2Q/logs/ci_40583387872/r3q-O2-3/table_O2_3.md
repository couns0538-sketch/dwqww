metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs (a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| O2 | SW | 3 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +2.96 [+2.27, +3.66] | +2.80 [+2.23, +3.36] | -0.05 [-0.75, +0.66] | -0.22 [-0.78, +0.35] | MET | +2.70 / +3.05 | 2.9 / 1.8 | +0.13 [-0.24, +0.51]; d20 -0.05 [-1.23, +1.15] (other head +3.04 [+2.15, +3.94]) |

files: 2; runs with a node-rule or exit failure: 0
