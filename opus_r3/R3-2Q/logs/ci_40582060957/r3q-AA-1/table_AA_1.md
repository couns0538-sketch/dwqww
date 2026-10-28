metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| AA | AA | 1 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | +0.02 [-0.56, +0.60] | +0.38 [-2.13, +2.94] | — | — | n/a | +0.06 [-0.66, +0.77] |
| AA | AA_REBUILD | 1 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | +0.32 [-0.95, +1.60] | +0.34 [-1.39, +2.10] | +0.02 [-0.56, +0.60] | +0.38 [-2.13, +2.94] | not met |  |

files: 2; runs with a node-rule or exit failure: 0
