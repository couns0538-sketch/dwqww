metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| NOZERO | SW | 1 | Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz (AVX-512) | d16 yes; d20 yes | +1.93 [+1.70, +2.16] | +1.76 [+1.41, +2.10] | -0.03 [-0.79, +0.75] | -0.10 [-0.52, +0.33] | not met | -4.16 [-4.60, -3.72]; d20 -4.39 [-4.95, -3.82] |

files: 2; runs with a node-rule or exit failure: 0
