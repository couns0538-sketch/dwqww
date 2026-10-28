metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| INT16 | SW | 1 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | +1.41 [-2.99, +6.00] | +1.10 [+0.13, +2.08] | +1.39 [-1.52, +4.38] | +0.41 [-1.63, +2.48] | not met | +1.79 [+0.70, +2.89] |
| INT16 | OPT | 1 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 no (tree changes: NPS only); d20 no (tree changes: NPS only) | -7.85 [-10.13, -5.51] | -13.85 [-14.53, -13.16] | +1.39 [-1.52, +4.38] | +0.41 [-1.63, +2.48] | not met | -8.78 [-9.88, -7.66] (tree changes) |

files: 3; runs with a node-rule or exit failure: 0
