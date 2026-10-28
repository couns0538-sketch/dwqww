metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| SPEEDSTACK | SW | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +0.37 [-0.25, +0.99] | +1.08 [-0.41, +2.59] | -0.49 [-1.10, +0.14] | -0.82 [-1.87, +0.24] | not met | +0.59 [+0.09, +1.08] |

files: 2; runs with a node-rule or exit failure: 0
