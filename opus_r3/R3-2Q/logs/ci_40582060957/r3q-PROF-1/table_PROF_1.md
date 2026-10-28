metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| PROF | SW | 1 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | -1.68 [-2.66, -0.70] | -0.56 [-1.62, +0.52] | -0.16 [-0.82, +0.50] | +0.08 [-0.62, +0.78] | not met | -7.24 |
| PROF | OPT | 1 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | -1.06 [-1.94, -0.18] | -1.52 [-2.04, -0.99] | -0.16 [-0.82, +0.50] | +0.08 [-0.62, +0.78] | not met | -1.10 [-2.02, -0.17] |

files: 3; runs with a node-rule or exit failure: 0
