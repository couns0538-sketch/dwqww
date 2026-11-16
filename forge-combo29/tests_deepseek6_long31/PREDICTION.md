long 31 prediction (recipe R on LmrFine ALONE; R4 = kimi5's job-11 runs) -- own commit before the first counted run

My build = clean 6b98f217 + LmrFine.patch.txt (f7bf3f43... verified this session three times).

1. R2 pins on my build: 312866 / 862329 / 3024920 / 4865609 (long 4/19/21 verified the same
   binary; re-run for this item). The uci list shows the ten options with kimi5's defaults
   (LmrFine 0, LmrFineHistory 0, LmrRoundF 512, the six F weights at their 1024/2048 values).
   Kill: any differing pin or default.
2. R3/R4 -- all fourteen of kimi5's job-11 runs reproduced on my build and compared position by
   position with its rows jsons (nodes AND bestmove; its jsons carry both):
   i1_def (O,G; defaults), i2_s14 (O,G), i3_fine (O,G; LmrFine 1/FH 0/RoundF 0),
   i4_s14fine (O,G), c1_s14fine_tt1025 (O; must DIFFER from i2 -- its sum 13,036,988),
   c2_s14fine_tt1023 (O; must EQUAL i2 -- 9,500,069), t1_s14fh (O,G; = my T1, 10,170,054),
   t2_s14fh_r0 (O,G; = my T2, 11,915,365).
   Kill: any differing row or sum in any of the fourteen.
3. R5: the planted fault is reported (ASan, exit 1); the clean sanitizer build over O at the T1
   setting gives 0 sanitizer lines. Kill otherwise.
