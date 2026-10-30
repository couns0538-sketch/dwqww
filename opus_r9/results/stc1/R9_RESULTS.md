# R9 STC 8+0.08 SPSA run (16 parameters from the lock values)

Run `F:\opus_scratch\r9\runs\stc1`: 208 batches, 832 game pairs = 1664 games (2026-10-30 00:12:47 .. 2026-10-30 04:45:59), tc 8+0.08, engine `F:\opus_scratch\r9\build\forge_r9_c.exe`, planned pairs 1200, 4 pairs per batch.
Results of plus vs minus: +203 -207 =1254 (draws 75.4%), per-game result variance v = 0.246; terminations {'normal': 1664}.

| parameter | start | end | end (int) | move | move / c_end | noise sigma | z | halves | verdict |
|---|---|---|---|---|---|---|---|---|---|
| LmrQuietBase | 85 | 80.01 | 80 | -4.99 | -0.42 | 4.99 | -1.00 | mixed | noise |
| LmrQuietDivisor | 220 | 225.15 | 225 | +5.14 | +0.32 | 6.66 | +0.77 | same way | noise |
| LmrCutNode | 2048 | 2039.82 | 2040 | -8.18 | -0.03 | 106.52 | -0.08 | mixed | noise |
| LmrNotImproving | 1024 | 1092.56 | 1093 | +68.56 | +0.36 | 79.89 | +0.86 | same way | noise |
| LmrTtPv | 1024 | 1021.60 | 1022 | -2.40 | -0.01 | 79.89 | -0.03 | mixed | noise |
| LmrGivesCheck | 1024 | 1062.85 | 1063 | +38.85 | +0.20 | 79.89 | +0.49 | same way | noise |
| NmpEvalBase | 180 | 163.56 | 164 | -16.43 | -0.55 | 12.48 | -1.32 | same way | noise |
| RfpMargin | 72 | 72.79 | 73 | +0.79 | +0.11 | 2.91 | +0.27 | mixed | noise |
| FutilityBase | 100 | 98.04 | 98 | -1.96 | -0.14 | 5.83 | -0.34 | mixed | noise |
| FutilityMultiplier | 110 | 104.33 | 104 | -5.67 | -0.47 | 4.99 | -1.13 | same way | noise |
| SeeQuietMultiplier | 24 | 22.14 | 22 | -1.86 | -0.62 | 1.25 | -1.49 | same way | noise |
| ProbcutMargin | 180 | 172.79 | 173 | -7.21 | -0.45 | 6.66 | -1.08 | same way | noise |
| SingularDoubleMargin | 24 | 22.47 | 22 | -1.53 | -0.31 | 2.08 | -0.74 | same way | noise |
| HistoryMalusPercent | 100 | 105.08 | 105 | +5.08 | +0.51 | 4.16 | +1.22 | same way | noise |
| AspirationDelta | 18 | 17.30 | 17 | -0.70 | -0.28 | 1.04 | -0.68 | same way | noise |
| QuietCheckBonus | 12000 | 12330.23 | 12330 | +330.23 | +0.22 | 624.14 | +0.53 | same way | noise |

0 of 16 parameters moved beyond 2 sigma (expected by chance: about 0.8).
Changed integers: 16.

Fastchess options of the tuned side (all changed parameters):

`option.R9Tune=true option.LmrQuietBase=80 option.LmrQuietDivisor=225 option.LmrCutNode=2040 option.LmrNotImproving=1093 option.LmrTtPv=1022 option.LmrGivesCheck=1063 option.NmpEvalBase=164 option.RfpMargin=73 option.FutilityBase=98 option.FutilityMultiplier=104 option.SeeQuietMultiplier=22 option.ProbcutMargin=173 option.SingularDoubleMargin=22 option.HistoryMalusPercent=105 option.AspirationDelta=17 option.QuietCheckBonus=12330`

Only the likely-real ones:

`option.R9Tune=true`

QA gate line (tuned options vs the same exe at defaults):

`-engine name=r9_tuned cmd=F:\opus_scratch\r9\build\forge_r9_c.exe option.R9Tune=true option.LmrQuietBase=80 option.LmrQuietDivisor=225 option.LmrCutNode=2040 option.LmrNotImproving=1093 option.LmrTtPv=1022 option.LmrGivesCheck=1063 option.NmpEvalBase=164 option.RfpMargin=73 option.FutilityBase=98 option.FutilityMultiplier=104 option.SeeQuietMultiplier=22 option.ProbcutMargin=173 option.SingularDoubleMargin=22 option.HistoryMalusPercent=105 option.AspirationDelta=17 option.QuietCheckBonus=12330 -engine name=r9_default cmd=F:\opus_scratch\r9\build\forge_r9_c.exe`

