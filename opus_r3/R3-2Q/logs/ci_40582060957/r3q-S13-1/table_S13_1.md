metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| S13 | SW | 1 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | -0.09 [-1.12, +0.96] | +0.26 [-0.51, +1.03] | +1.21 [-0.20, +2.65] | -0.20 [-1.27, +0.88] | not met | -0.70 [-1.76, +0.37] |
| S13 | OPT | 1 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | -0.15 [-0.88, +0.58] | +0.33 [-1.16, +1.84] | +1.21 [-0.20, +2.65] | -0.20 [-1.27, +0.88] | not met | -0.10 [-1.40, +1.22] |

files: 3; runs with a node-rule or exit failure: 0
