# Re-verification of PC-path findings under GENUINELY applied PC20 (after S-W7/S-W8)
# 2026-11-17T01:09:16Z
# settings verified by check_settings_values.py: 22 options, values match canon

## S-N1 softnodes determinism - reproduced IDENTICALLY
| cell | depth | nodes | ratio |
|---|---|---|---|
| O-mid1 N=20000 | 12 | 21,812 | 1.09x |
| O-mid2 N=2000 | 7 | 2,039 | 1.02x |
| O-mid2 N=20000 | 12 | 26,844 | 1.34x |
| G-mid N=2000 | 7 | 2,303 | 1.15x |
| G-mid N=20000 | 12 | 38,996 | 1.95x |
| tactic N=2000 | 5 | 2,341 | 1.17x |
| tactic N=20000 | 9 | 23,992 | 1.20x |

8 of 8 cells deterministic; overshoot median 1.20x; all replies carried a pv.

## S-N3 label reproducibility - reproduced EXACTLY
48 of 48 cells identical across 3 fresh processes (8 FENs x 6 limits).

CONCLUSION: the settings bug affected the deep node ladders (S-C18 chain, withdrawn) but not these.
