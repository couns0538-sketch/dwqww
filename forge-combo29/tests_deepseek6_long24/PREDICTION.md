long 24 prediction (my own recount of glmflash5's jobs 25, 26 and 27) -- own commit before the first counted run

1. Every one of the seventeen gamelist files has exactly 2,000 game lines = 1,000 pairs; within a
   match every opening FEN appears exactly twice with the colours swapped; the cand side is named
   "cand". Kill: any file with a different line count, an opening appearing once or three times,
   or a missing cand side.
2. My pair Elo and its 95 percent interval reproduce the three reports' printed numbers to the
   digit for every match (the reports' Elo/CI are deterministic functions of the gamelists).
   Known cells to meet (from the reports): M61 -4.34 [-16.53, +7.85]; M62 -25.93 [-38.10,
   -13.77]; M64 -13.38 [-25.27, -1.49]; M69 -13.03 [-25.04, -1.03]; M76 +14.95 [+3.15, +26.74].
   Kill: any differing Elo or interval bound.
3. The five pair-outcome counts (pair scores 2, 1.5, 1, 0.5, 0) sum to 1,000 per match. Kill:
   otherwise.
4. Opening-sharing: every pair of matches across the three jobs shares ZERO distinct openings
   (the pools remove everything the earlier matches used). Kill: any nonzero sharing.
