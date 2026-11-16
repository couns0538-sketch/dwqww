# Threads reproducibility, 5 fresh processes per setting, startpos, depth 10, Hash 16
# each run is its own process (paced_session.py, waits for bestmove)

| setting | run | nodes | bestmove |
|---|---|---|---|
| Threads 1 | 1 | 13102 | d2d4 |
| Threads 1 | 2 | 13102 | d2d4 |
| Threads 1 | 3 | 13102 | d2d4 |
| Threads 1 | 4 | 13102 | d2d4 |
| Threads 1 | 5 | 13102 | d2d4 |
| Threads 2 | 1 | 25249 | e2e4 |
| Threads 2 | 2 | 27508 | d2d4 |
| Threads 2 | 3 | 18993 | e2e4 |
| Threads 2 | 4 | 27138 | e2e4 |
| Threads 2 | 5 | 34983 | d2d4 |
