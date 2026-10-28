metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| PROF | SW | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | -1.47 [-2.72, -0.20] | -1.55 [-2.16, -0.94] | -0.11 [-0.67, +0.46] | -0.20 [-0.55, +0.16] | not met | -7.24 |
| PROF | OPT | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | -1.07 [-2.05, -0.08] | -0.82 [-1.53, -0.11] | -0.11 [-0.67, +0.46] | -0.20 [-0.55, +0.16] | not met | -1.10 [-2.02, -0.17] |

files: 3; runs with a node-rule or exit failure: 0
