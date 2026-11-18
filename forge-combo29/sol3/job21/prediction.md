# Job 21 prediction

The planned G1 run uses plain r15d, PC20 with synthetic net768,
one thread, Hash 16, and one fresh engine per game. Each search
uses the 2,000 soft target and 8,000 hard cap.

| Quantity | Predicted range |
| --- | ---: |
| Final consumed nodes after the last finished iteration, share of all final nodes | 16–30% |
| Searches whose final count exceeds last-info nodes, share of all searches | 9–21% |
| Capped searches' go-to-bestmove wall time after last info time, share of all wall time | 13–35% |

K1 found 22.76% of final nodes beyond the last finished iteration
and 14.04% of searches with a positive final-minus-info difference.
G1 uses different starts, so both shares can move with the game
paths. I use a wider range for time because cost per node can
vary across the search and the engine's last time is reported
in integer milliseconds.
