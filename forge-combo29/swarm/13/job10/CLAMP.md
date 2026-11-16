| board | go | info lines | last depth | nodes on last line | nodes budget |
|---|---|---|---|---|---|
| mate-in-1 | go nodes 20000 | 64 | 64 | 1152 | 20000 |
| mate-in-1 | go depth 12 | 12 | 12 | 216 | n/a |
| non-mate startpos | go nodes 20000 | 10 | 10 | 13102 | 20000 |
| non-mate startpos | go depth 12 | 12 | 12 | 56720 | n/a |

VERDICT: depth 64 with a small node count means a mate was proven, not that the search went 64
plies deep. Exclude depth>=64 from any depth statistic and never gate a latency measure on depth.
