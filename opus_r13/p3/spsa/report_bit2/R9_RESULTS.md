# R13 P3 SPSA bit 2 (Sf26NmpPrior on)

Run `C:\o13\p3\spsa\run_bit2`: 80 batches, 160 game pairs = 320 games (2026-11-01 09:07:14 .. 2026-11-01 09:56:21), tc 5+0.05, engine `C:\o13\handoff\p3_sf26\forge_ltopgo_sfs.exe`, planned pairs 160, 2 pairs per batch.
Results of plus vs minus: +57 -42 =221 (draws 69.1%), per-game result variance v = 0.307; terminations {'normal': 320}.

| parameter | start | end | end (int) | move | move / c_end | noise sigma | z | halves | verdict |
|---|---|---|---|---|---|---|---|---|---|
| Sf26NmpPriorBonus | 16 | 17.77 | 18 | +1.77 | +0.44 | 3.68 | +0.48 | same way | noise |
| Sf26NmpPriorCap | 3 | 1.93 | 2 | -1.07 | -1.07 | 0.92 | -1.16 | same way | noise |

0 of 2 parameters moved beyond 2 sigma (expected by chance: about 0.1).
Changed integers: 2.

Fastchess options of the tuned side (all changed parameters):

`option.R9Tune=true option.Sf26NmpPriorBonus=18 option.Sf26NmpPriorCap=2`

Only the likely-real ones:

`option.R9Tune=true`

QA gate line (tuned options vs the same exe at defaults):

`-engine name=r9_tuned cmd=forge_ltopgo_sfs.exe (029d58e8) option.R9Tune=true option.Sf26NmpPriorBonus=18 option.Sf26NmpPriorCap=2 -engine name=r9_default cmd=forge_ltopgo_sfs.exe (029d58e8)`

