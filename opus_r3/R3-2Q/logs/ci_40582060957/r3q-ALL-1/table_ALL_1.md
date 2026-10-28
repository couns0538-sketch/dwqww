metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| ALL | SW | 1 | Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz (AVX-512) | d16 yes; d20 yes | +3.84 [+3.56, +4.11] | +3.80 [+3.57, +4.03] | +0.02 [-0.28, +0.31] | +0.13 [-0.00, +0.27] | MET |  |

files: 2; runs with a node-rule or exit failure: 0
