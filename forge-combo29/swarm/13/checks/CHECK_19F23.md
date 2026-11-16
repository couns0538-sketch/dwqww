# CHECK of seat 19's finding 19-F23 — seat 13, own build, own harness

## Verdict
**CONFIRMS 19-F23.**

Seat 19 claimed: `bench` is immune to the warm-state trap — five `bench 13` lines in ONE process
give 862,329 each, identical to one-per-process — and gave a mechanism in the engine's own source:
`uci.cpp:611` constructs `forge::Searcher bench_searcher(16)` and the loop calls
`bench_searcher.clear()` at `uci.cpp:617` before every one of the eight positions, with
`Searcher::clear()` at `search.cpp:2679` calling `shared_.tt.clear()`.

Both the behaviour and the cited code hold on my build.

## Evidence
`out_19f23/bench_five_one_process.txt` and `out_19f23/bench_five_separate.txt`.

**Five `bench 13` lines in ONE process** (one engine process, five bench commands piped in order):

```
bench depth 13 nodes 862329
bench depth 13 nodes 862329
bench depth 13 nodes 862329
bench depth 13 nodes 862329
bench depth 13 nodes 862329
```

**Five separate processes**, same command:

```
bench depth 13 nodes 862329   (x5, identical)
```

All ten values identical, so `bench` gives the same node count warm and cold, exactly as claimed.

## The mechanism, verified in source (not taken on trust)
I opened both files at the lines the finding names.

`src/uci.cpp:611` — the bench searcher is constructed once, outside the position loop:

```cpp
forge::Searcher bench_searcher(16);
for (const std::string_view fen : fens) {
    forge::Board bench_board;
    if (!bench_board.set_fen(fen)) continue;
    forge::SearchLimits limits;
    limits.depth = depth;
    bench_searcher.clear();
    total_nodes += bench_searcher.search(...)
```

`src/search.cpp:2679` — `clear()` wipes the table:

```cpp
void Searcher::clear() {
    shared_.tt.clear();
    for (auto& worker : workers_) worker->clear();
}
```

So every bench position starts with an empty transposition table regardless of how many `bench`
lines share a process. The finding's mechanism is correct as stated.

## The contrast that makes the finding worth having (my own measurement)
The same build, same position, `go depth 12` instead of `bench`:

| discipline | nodes | bestmove |
|---|---|---|
| one process, 1st search | 56,720 | e2e4 |
| one process, 2nd search (nothing between) | 4,951 | e2e4 |
| one process, 3rd search | 4,516 | e2e4 |
| fresh process | 56,720 | e2e4 |
| fresh process (again) | 56,720 | e2e4 |

So `go`-driven searches DO vary with state on this build while `bench` does not. That is the
boundary 19-F23 draws, and it is real.

## Why this matters to the swarm
The honesty pins are obtained with `bench` and `go perft`, both of which are state-independent on
this build:
- `bench`: proven above (and by its own `clear()` per position);
- `perft`: I proved separately that three consecutive `go perft 4` on startpos in one process all
  give `nodes 197281`, equal to a fresh process (perft does not consult the table at all).

So every seat's honesty numbers, and every perft-based result including mine, are valid whether or
not the harness reused a process — but any seat that published node counts from `go depth N`
searches across a shared process has warm numbers, and must label them so.

## Beyond the finding
Nothing beyond it. I did not test other bench depths (13 is the one the pins use).
