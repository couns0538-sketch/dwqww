long 47 prediction (the root restriction: plain vs searchmoves-all vs MultiPV) -- own commit before the counted runs

On the first 50 of O, under S14, depth 12:
1. (c) MultiPV 1 set explicitly is IDENTICAL to (a) plain on every position (the option's
   explicit value changes nothing). Kill: any differing row.
2. (b) `go depth 12 searchmoves <all legal moves>` DIFFERS from (a) on most positions: my own
   long-6 work (the prior run) measured the mechanism (a restricted root stores no TT entry, so
   from the second iteration the root has no hash move and IIR applies there). I predict (b)
   differs from (a) on at least 40 of the 50 positions and (b)'s SUM is the larger (the IIR tax
   at the root makes the tree bigger). Kill: identical everywhere, or (b) <= (a) in sum.
3. (d) MultiPV 2 differs from (a) on every position and its sum is roughly 1.8-2.2x (a)'s.
   Kill: identical, or outside that band.
4. The per-position direction table (which of the 50 differ and by how much) is the item's
   deliverable; the direction counts are committed.
