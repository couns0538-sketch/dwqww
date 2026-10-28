metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| INT16 | SW | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | -1.16 [-1.90, -0.41] | -0.90 [-1.94, +0.16] | -0.10 [-0.77, +0.56] | -0.16 [-1.02, +0.71] | not met | +1.79 [+0.70, +2.89] |
| INT16 | OPT | 2 | AMD EPYC 7763 64-Core Processor | d16 no (tree changes: NPS only); d20 no (tree changes: NPS only) | -8.52 [-9.54, -7.49] | -14.01 [-14.67, -13.34] | -0.10 [-0.77, +0.56] | -0.16 [-1.02, +0.71] | not met | -8.78 [-9.88, -7.66] (tree changes) |

files: 3; runs with a node-rule or exit failure: 0
