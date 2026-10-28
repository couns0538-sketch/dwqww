metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| S13 | SW | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | -0.16 [-0.59, +0.26] | -0.50 [-1.00, -0.01] | -0.37 [-1.17, +0.44] | +0.17 [-0.31, +0.64] | not met | -0.70 [-1.76, +0.37] |
| S13 | OPT | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +0.18 [-0.53, +0.90] | +0.13 [-0.20, +0.47] | -0.37 [-1.17, +0.44] | +0.17 [-0.31, +0.64] | not met | -0.10 [-1.40, +1.22] |

files: 3; runs with a node-rule or exit failure: 0
