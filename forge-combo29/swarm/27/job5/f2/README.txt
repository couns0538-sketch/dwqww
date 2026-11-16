VERIFICATION of what the f1 run actually measured (my prediction P1 was WRONG).

Finding out, not assuming: f1 reported "12 of 12 searches finished" for a `go depth 24` that should take
seconds. The reason is that `setoption` calls stop_search() before it applies anything (src/uci.cpp:259),
so the resize never overlapped a live search -- my P1 hypothesis (a resize racing the workers) is dead,
because the UCI layer serialises it.

Measured directly on the release build, startpos, `go depth 20`, stdin held open:

  A: `go depth 20` alone                      -> 20 `info depth` lines (all depths reached)
  B: same, plus `setoption name Hash value 64` sent 100 ms into it
                                              -> 14 `info depth` lines, then `bestmove e2e4`

So a `setoption` during a search TRUNCATES that search, and the bestmove is the one from the last
completed iteration. That is intended-looking (every option change needs a consistent table), but it is
observable and worth recording: a GUI that sends `setoption` mid-search loses the search it had running.

Raw: setoption_midsearch.raw.txt (B). Command to show it again:

  { printf 'uci\nisready\nucinewgame\nisready\nposition startpos\nisready\ngo depth 20\n'; sleep 0.1; \
    printf 'setoption name Hash value 64\n'; sleep 8; printf 'quit\n'; } | ./forge | grep -c '^info depth'
