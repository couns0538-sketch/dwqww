# T5 endgame tables: PC-specific ideas for the crew

1. **Regression check.** Run `t5_gen_fens.py` (new seed) + `tb_probe` + `t5_fathom_batch` + `t5_compare.py` after
   any change to `src/syzygy.inc` or `src/tablebase.inc`. 50k positions take ~30 s here at Idle.
2. **Cursed / 50-move cases.** The random set has halfmove 0. Add positions with halfmove > 0 and cursed / blessed
   WDL, as the P6 check50.py does, to cover `Syzygy50MoveRule`.
3. **6-piece WDL.** 67.8 GiB (syzygy-tables.info). In search only WDL is needed; DTZ (81.4 GiB) only at the root. No
   drive has room now (C: ~48, D: ~47, F: ~54 GB free). Plan it with the owner before any download, and put it on the
   SSD the gates read from.
4. **Probe cost in search.** Forge's probe is ~1 us vs Fathom ~0.55 us. If profiling ever shows TB probes in endgames
   (T3-style trace of a TB gate), look at Fathom's capture-resolution loop (MIT; it may be studied and copied with its
   notice).
5. **Gate setting.** The crew's P6 line has `SyzygyProbeDepth`. A 3-4-5 set changes few positions at 10+0.1, so expect
   small Elo. Only a gate can tell; this trial makes no Elo claim.
