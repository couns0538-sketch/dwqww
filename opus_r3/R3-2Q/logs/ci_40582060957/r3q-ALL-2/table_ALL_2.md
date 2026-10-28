metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| ALL | SW | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +4.64 [+3.38, +5.91] | +2.50 [+1.24, +3.78] | -0.15 [-1.25, +0.97] | +0.35 [-0.38, +1.10] | not met |  |

files: 2; runs with a node-rule or exit failure: 0
