metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs (a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| O2 | SW | 5 | INTEL(R) XEON(R) PLATINUM 8573C (AVX-512) | d16 yes; d20 yes | +3.27 [+2.62, +3.93] | +2.35 [+2.08, +2.62] | +0.14 [-0.50, +0.77] | -0.26 [-0.98, +0.46] | MET | +3.35 / +2.32 | 2.8 / 1.7 | +0.13 [-0.24, +0.51]; d20 -0.05 [-1.23, +1.15] (other head +3.04 [+2.15, +3.94]) |
| O2 | SW_V4 | 5 | INTEL(R) XEON(R) PLATINUM 8573C (AVX-512) | d16 yes; d20 yes | +4.06 [+3.53, +4.59] | +3.95 [+3.10, +4.81] | +0.14 [-0.50, +0.77] | -0.26 [-0.98, +0.46] | MET | +3.80 / +3.98 | 2.1 / 3.2 |  |

files: 3; runs with a node-rule or exit failure: 0
