metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs (a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NOZERO | SW | 3 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +1.22 [+0.76, +1.68] | +2.03 [+1.02, +3.05] | -0.21 [-0.83, +0.42] | +0.06 [-0.48, +0.61] | not met | +1.40 / +2.08 | 1.4 / 2.3 | -4.16 [-4.60, -3.72]; d20 -4.39 [-4.95, -3.82] |

files: 2; runs with a node-rule or exit failure: 0
