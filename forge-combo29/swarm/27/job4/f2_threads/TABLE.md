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

## Why `bench` and perft are immune to the Threads spread (checked, not assumed)

`bench` does NOT use the user's `Threads` setting. It constructs its own searcher
(`forge::Searcher bench_searcher(16);`, uci.cpp:612), i.e. one thread, and runs the eight
position searches on it. So a pinned bench total is a Threads 1 statement by construction,
whatever `setoption name Threads` says. Measured:

```
$ for t in 1 8; do printf "uci\nisready\nsetoption name Threads value $t\nisready\nucinewgame\nisready\nposition startpos\nbench 13\n" | ./forge | grep "bench depth 13 nodes"; done
Threads 1: bench depth 13 nodes 862329
Threads 8: bench depth 13 nodes 862329     <- identical
```

`go perft` is a plain recursive count in the UCI thread and never consults Threads or the table.

## The rule for everyone else

Every pinned node total in this repository is a **Threads 1** statement: bench 11/13/16, perft 5, and
the brief's known sums (O d12 9,500,069 / G d12 18,466,239 / O d14 21,812,100 / G d14 43,345,893).
They must be compared only against **Threads 1** runs. A Threads 2 or greater run is not comparable to
them and cannot be pinned at all: five Threads 2 runs of one position gave 18,993-34,983 nodes (1.8x).

## My own tables

Checked with `git grep` across my whole folder: no table of mine ever placed a Threads > 1 number next to a
known sum, and my honesty runs never set `Threads` at all (`honesty.sh` sends no Threads line), so every
honesty number I reported is a default-Threads (1) statement.
