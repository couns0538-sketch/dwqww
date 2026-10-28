metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| NOZERO | SW | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +1.78 [+0.96, +2.60] | +1.21 [+0.34, +2.09] | -0.20 [-0.88, +0.48] | -0.18 [-1.03, +0.67] | not met | -4.16 [-4.60, -3.72]; d20 -4.39 [-4.95, -3.82] |

files: 2; runs with a node-rule or exit failure: 0
