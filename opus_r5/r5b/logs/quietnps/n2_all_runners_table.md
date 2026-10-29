metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs (a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | median d16 / d20 | spread % d16 / d20 | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N2 | SW | 1 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +5.27 [+4.45, +6.10] | +4.57 [+3.68, +5.46] | -0.40 [-1.21, +0.40] | -0.39 [-0.90, +0.13] | MET | +5.12 / +4.87 | 2.8 / 3.0 |  |
| N2 | SW | 2 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +5.56 [+4.76, +6.36] | +5.44 [+4.47, +6.43] | +0.05 [-0.66, +0.77] | -0.01 [-0.84, +0.83] | MET | +5.44 / +4.95 | 3.9 / 4.7 |  |
| N2 | SW | 3 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +5.91 [+4.84, +6.99] | +6.32 [+4.39, +8.28] | +0.34 [-0.93, +1.64] | +0.80 [-0.15, +1.75] | MET | +6.22 / +6.22 | 6.5 / 8.4 |  |
| N2 | SW | 4 | INTEL(R) XEON(R) PLATINUM 8573C (AVX-512) | d16 yes; d20 yes | +5.93 [+4.60, +7.27] | +5.91 [+5.13, +6.70] | -0.27 [-1.25, +0.72] | +0.06 [-0.70, +0.83] | MET | +5.86 / +6.24 | 4.5 / 3.0 |  |
| N2 | SW | 5 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | +0.28 [-4.72, +5.54] | +1.68 [+0.31, +3.06] | +0.17 [-3.54, +4.01] | +0.73 [-0.63, +2.11] | not met | +2.69 / +1.80 | 28.1 / 11.7 |  |
| N2 | SW | 6 | AMD EPYC 7763 64-Core Processor | d16 yes; d20 yes | +5.71 [+4.89, +6.54] | +5.19 [+4.31, +6.09] | +0.15 [-0.47, +0.78] | -0.16 [-0.69, +0.38] | MET | +5.70 / +5.31 | 3.1 / 4.8 |  |
| N2 | SW | all (6) | 6 runners | | **+4.76 [+3.83, +5.69]** | **+4.84 [+4.41, +5.27]** | +0.01 [-0.66, +0.68] | +0.17 [-0.14, +0.48] | MET | | | |
| N2 | SW_V4 | 4 | INTEL(R) XEON(R) PLATINUM 8573C (AVX-512) | d16 yes; d20 yes | +5.94 [+5.07, +6.81] | +6.03 [+5.62, +6.43] | -0.27 [-1.25, +0.72] | +0.06 [-0.70, +0.83] | MET | +6.24 / +5.97 | 2.4 / 3.9 |  |
| N2 | SW_V4 | 5 | AMD EPYC 9V45 96-Core Processor (AVX-512) | d16 yes; d20 yes | +3.80 [+2.40, +5.23] | +4.79 [+1.64, +8.02] | +0.17 [-3.54, +4.01] | +0.73 [-0.63, +2.11] | not met | +3.92 / +4.02 | 6.2 / 10.3 |  |
| N2 | SW_V4 | all (2) | 2 runners | | **+4.86 [+4.08, +5.65]** | **+5.40 [+3.81, +7.02]** | -0.05 [-1.94, +1.88] | +0.39 [-0.33, +1.12] | MET | | | |

files: 14; runs with a node-rule or exit failure: 0
