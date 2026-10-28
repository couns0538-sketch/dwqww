metric: cpu_bench NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; rule = 95% CI lower bound >= +2% at d16 AND d20

| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule | PC (R3-2) |
|---|---|---|---|---|---|---|---|---|---|---|
| NOZERO | SW | 0 | AMD64 Family 26 Model 68 Stepping 0, AuthenticAMD |  | n/a | n/a | n/a | n/a | not met | -4.16 [-4.60, -3.72]; d20 -4.39 [-4.95, -3.82] |
| INT16 | OPT | 0 | AMD64 Family 26 Model 68 Stepping 0, AuthenticAMD |  | n/a | n/a | n/a | n/a | not met | -8.78 [-9.88, -7.66] (tree changes) |
| PROF | OPT | 0 | AMD64 Family 26 Model 68 Stepping 0, AuthenticAMD |  | n/a | n/a | n/a | n/a | not met | -1.10 [-2.02, -0.17] |

files: 4; runs with a node-rule or exit failure: 0
