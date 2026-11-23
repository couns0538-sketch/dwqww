# The same game records give a different dispatch-lead check at three active workers

I repeated the 360 native games of 171712Z on three simultaneous workers. All 360 game-record digests and all 47,745 raw rows matched the sequential run. Wall times changed. In the same 240 held-out games, the counts exceeding their slot’s 40-game pilot maximum plus 0%, 5%, 10%, 25%, and 50% were respectively 13, 10, 7, 2 and 1. The corresponding one-worker counts were 11, 8, 5, 2 and 0. On slot 1 the three-worker pilot maximum was 381.37 ms and the later maximum 586.79 ms.

A margin that appeared to cover this small sample at one worker missed a game at three. Retain the held-out check at the intended worker count, including packing and transfer in that rehearsal. No percentage from this machine sets the day’s margin.
