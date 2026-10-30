# R9 sanity run 3: LmrQuietBase started at 250 (lock 85)

Run `F:\opus_scratch\r9\runs\sanity3`: 120 batches, 240 game pairs = 480 games (2026-10-30 00:13:22 .. 2026-10-30 00:53:10), tc 4+0.04, engine `F:\opus_scratch\r9\build\forge_r9_c.exe`, planned pairs 240, 2 pairs per batch.
Results of plus vs minus: +62 -60 =358 (draws 74.6%), per-game result variance v = 0.254; terminations {'normal': 480}.

| parameter | start | end | end (int) | move | move / c_end | noise sigma | z | halves | verdict |
|---|---|---|---|---|---|---|---|---|---|
| LmrQuietBase | 250 | 189.29 | 189 | -60.71 | -2.02 | 40.99 | -1.48 | mixed | noise |
| HistoryMalusPercent | 100 | 76.92 | 77 | -23.08 | -1.92 | 12.30 | -1.88 | same way | noise |

0 of 2 parameters moved beyond 2 sigma (expected by chance: about 0.1).
Changed integers: 2.

Fastchess options of the tuned side (all changed parameters):

`option.R9Tune=true option.LmrQuietBase=189 option.HistoryMalusPercent=77`

Only the likely-real ones:

`option.R9Tune=true`

QA gate line (tuned options vs the same exe at defaults):

`-engine name=r9_tuned cmd=F:\opus_scratch\r9\build\forge_r9_c.exe option.R9Tune=true option.LmrQuietBase=189 option.HistoryMalusPercent=77 -engine name=r9_default cmd=F:\opus_scratch\r9\build\forge_r9_c.exe`

