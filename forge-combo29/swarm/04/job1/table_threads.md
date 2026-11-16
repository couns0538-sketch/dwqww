# thread axis, hang FEN 5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1, depth 12, S14, Hash 16
# every run a FRESH process with ucinewgame before position (seat 10 cold-start rule)
# produced by: python3 job1/hang_repro.py <exe> /tmp/hang <tag> --runs N --threads T --depth 12 --limit 90

| threads | runs | hangs | median s | max s | nodes min | nodes max |
|---|---|---|---|---|---|---|
| 1 | 10 | 0 | 0.03 | 0.03 | 79980 | 79980 |
| 2 | 8 | 0 | 0.47 | 0.72 | 1504120 | 6400704 |
| 3 | 8 | 0 | 0.62 | 17.58 | 2949761 | 235660536 |
| 4 | 20 | 0 | 0.77 | 69.30 | 2739824 | 1252499786 |
| 5 | 8 | 0 | 1.51 | 36.74 | 3167300 | 575436075 |
| 8 | 8 | 0 | 66.50 | 103.89 | 5627158 | 1953875466 |

depth axis at Threads 4 (same FEN, same flags):

| depth | runs | median s | max s | nodes max |
|---|---|---|---|---|
| 10 | 8 | 0.10 | 0.19 | 2739439 |
| 11 | 8 | 0.17 | 1.40 | 25173385 |
| 12_20 | 20 | 0.77 | 69.30 | 1252499786 |
| 13 | 8 | 2.15 | 46.40 | 812344815 |
