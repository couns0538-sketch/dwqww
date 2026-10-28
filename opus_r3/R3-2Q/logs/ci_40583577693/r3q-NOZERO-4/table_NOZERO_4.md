metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs (a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NOZERO | SW | 4 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +1.33 [+0.63, +2.03] | +1.85 [+1.15, +2.55] | +0.03 [-0.81, +0.87] | +0.51 [-0.41, +1.43] | not met | +1.22 / +1.60 | 2.7 / 1.8 | -4.16 [-4.60, -3.72]; d20 -4.39 [-4.95, -3.82] |

files: 2; runs with a node-rule or exit failure: 0
