# R9 sanity run: LmrQuietDivisor started at 120 (lock 220)

Run `F:\opus_scratch\r9\runs\sanity2`: 100 batches, 200 game pairs = 400 games (2026-10-29 23:31:44 .. 2026-10-30 00:11:50), tc 4+0.04, engine `F:\opus_scratch\r9\build\forge_r9_c.exe`, planned pairs 200, 2 pairs per batch.
Results of plus vs minus: +47 -64 =289 (draws 72.2%), per-game result variance v = 0.276; terminations {'normal': 400}.

| parameter | start | end | end (int) | move | move / c_end | noise sigma | z | halves | verdict |
|---|---|---|---|---|---|---|---|---|---|
| LmrQuietDivisor | 120 | 138.63 | 139 | +18.64 | +1.24 | 14.62 | +1.27 | mixed | noise |
| HistoryMalusPercent | 100 | 111.92 | 112 | +11.92 | +0.99 | 11.70 | +1.02 | mixed | noise |

0 of 2 parameters moved beyond 2 sigma (expected by chance: about 0.1).
Changed integers: 2.

Fastchess options of the tuned side (all changed parameters):

`option.R9Tune=true option.LmrQuietDivisor=139 option.HistoryMalusPercent=112`

Only the likely-real ones:

`option.R9Tune=true`

QA gate line (tuned options vs the same exe at defaults):

`-engine name=r9_tuned cmd=F:\opus_scratch\r9\build\forge_r9_c.exe option.R9Tune=true option.LmrQuietDivisor=139 option.HistoryMalusPercent=112 -engine name=r9_default cmd=F:\opus_scratch\r9\build\forge_r9_c.exe`

