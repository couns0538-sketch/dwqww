metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| O2 | SW | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +2.50 [+1.42, +3.59] | +2.34 [+1.68, +3.00] | -0.50 [-1.29, +0.30] | -0.19 [-1.88, +1.53] | not met | +0.13 [-0.24, +0.51]; d20 -0.05 [-1.23, +1.15] (other head +3.04 [+2.15, +3.94]) |

files: 2; runs with a node-rule or exit failure: 0
