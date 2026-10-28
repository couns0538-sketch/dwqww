metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| SPEEDSTACK | SW | 1 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | +0.64 [+0.26, +1.03] | +1.03 [-1.48, +3.60] | -0.01 [-0.29, +0.27] | -0.02 [-0.36, +0.32] | not met | +0.59 [+0.09, +1.08] |

files: 2; runs with a node-rule or exit failure: 0
