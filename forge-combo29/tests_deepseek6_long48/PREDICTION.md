long 48 prediction (the Hash sweep and the carried-TT run) -- own commit before the counted runs

1. Hash 16 = 9,500,069 EXACTLY, 200/200 rows equal to my O_S14 rows. Kill: otherwise.
2. The sums are monotone in the hash size at the small end: sum(Hash 1) > sum(Hash 4) >
   sum(Hash 16) (a thrashing table forgets and re-searches). Kill: any inversion among 1/4/16.
3. Hash 64 is within 1 percent of 9,500,069 and Hash 256 within 0.5 percent (the d12 tree's
   working set fits by then). Kill: either outside its band.
4. The one-process no-ucinewgame run (Hash 16, the first 50 of O... the item says the SAME 50
   positions for the second part? Re-reading: "Then the same 50 positions searched in ONE process
   without ucinewgame between them" -- the 50-position subset, one process, no ucinewgame): its
   sum differs from the fresh-process 50-position rows and is SMALLER (the carried entries help).
   Kill: equality with the fresh rows, or a bigger sum.
