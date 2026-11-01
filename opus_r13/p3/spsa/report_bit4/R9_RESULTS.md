# R13 P3 SPSA bit 4 (Sf26LmrGap on)

Run `C:\o13\p3\spsa\run_bit4`: 80 batches, 160 game pairs = 320 games (2026-11-01 09:56:57 .. 2026-11-01 10:44:55), tc 5+0.05, engine `C:\o13\handoff\p3_sf26\forge_ltopgo_sfs.exe`, planned pairs 160, 2 pairs per batch.
Results of plus vs minus: +44 -44 =232 (draws 72.5%), per-game result variance v = 0.275; terminations {'normal': 320}.

| parameter | start | end | end (int) | move | move / c_end | noise sigma | z | halves | verdict |
|---|---|---|---|---|---|---|---|---|---|
| Sf26LmrAlphaGap | 260 | 310.63 | 311 | +50.63 | +1.27 | 34.83 | +1.45 | mixed | noise |

0 of 1 parameters moved beyond 2 sigma (expected by chance: about 0.1).
Changed integers: 1.

Fastchess options of the tuned side (all changed parameters):

`option.R9Tune=true option.Sf26LmrAlphaGap=311`

Only the likely-real ones:

`option.R9Tune=true`

QA gate line (tuned options vs the same exe at defaults):

`-engine name=r9_tuned cmd=forge_ltopgo_sfs.exe (029d58e8) option.R9Tune=true option.Sf26LmrAlphaGap=311 -engine name=r9_default cmd=forge_ltopgo_sfs.exe (029d58e8)`

