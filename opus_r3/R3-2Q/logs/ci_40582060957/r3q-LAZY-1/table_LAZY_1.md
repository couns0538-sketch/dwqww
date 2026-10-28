metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| LAZY | SW | 1 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | -0.31 [-1.47, +0.86] | +0.21 [-0.86, +1.30] | -0.06 [-0.67, +0.55] | +0.25 [-0.50, +1.00] | not met | +4.36 [+2.92, +5.81] |
| LAZY | OPT | 1 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +0.13 [-0.58, +0.84] | -0.40 [-1.27, +0.47] | -0.06 [-0.67, +0.55] | +0.25 [-0.50, +1.00] | not met | -1.05 [-2.52, +0.44] |

files: 3; runs with a node-rule or exit failure: 0
