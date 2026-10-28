metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| AA | AA | 2 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | -0.45 [-2.18, +1.30] | -0.96 [-2.38, +0.48] | — | — | n/a | +0.06 [-0.66, +0.77] |
| AA | AA_REBUILD | 2 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | -1.62 [-3.45, +0.23] | +1.69 [-2.42, +5.97] | -0.45 [-2.18, +1.30] | -0.96 [-2.38, +0.48] | not met |  |

files: 2; runs with a node-rule or exit failure: 0
