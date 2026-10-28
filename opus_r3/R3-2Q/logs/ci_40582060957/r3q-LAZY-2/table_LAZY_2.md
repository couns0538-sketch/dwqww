metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| LAZY | SW | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +0.31 [-0.34, +0.96] | +0.11 [-0.42, +0.64] | +0.52 [-0.26, +1.31] | +1.08 [+0.03, +2.15] | not met | +4.36 [+2.92, +5.81] |
| LAZY | OPT | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +0.03 [-0.57, +0.64] | +0.07 [-0.66, +0.80] | +0.52 [-0.26, +1.31] | +1.08 [+0.03, +2.15] | not met | -1.05 [-2.52, +0.44] |

files: 3; runs with a node-rule or exit failure: 0
