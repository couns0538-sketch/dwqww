# job 6 - src/eval.cpp: `eval` is a pure function of the board (negative result, with controls)

`eval` is synchronous in the UCI loop (uci.cpp:575-589), so 19-F12 cannot touch it. Every parse asserts
its line; a missing line raises.

| question | measurement | result |
|---|---|---|
| is `eval` affected by anything searched before it? | same 8 FENs evaluated in a fresh process and again after a `go depth 12` search of that same FEN | **8 of 8 identical** (hce, nnue and total) |
| is `total` consistent with its parts? | `total == clamp(hce+nnue)` over 26 rows (incl. the in-check position) | **26 of 26**, 0 inconsistent |
| does `eval` change when a search-only option is flipped? | `UseNNUE false` | yes by design: nnue becomes 0 and total drops to hce (e.g. 927 -> 598). The other two option flips alone changed nothing. |
| does a position in check still evaluate? | `rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3` | `info string eval hce -68 nnue -59 total -127 incheck 1` |

Reading of `eval.cpp` (659 lines) at maximum warnings (`-Wall -Wextra -Wshadow -Wconversion
-Wsign-conversion -Wuninitialized`): **zero warnings from eval.cpp**; the only warnings in the build are the
11 already recorded in job1/warnings_search.txt plus one in board.cpp.

What this does NOT show: that the evaluation is *correct* (that needs game results), or that the hand-written
term is reached on the owner's PC (Opus file 2, rule 2: with a v3 net it is not).

Reproduce: `python3 forge-combo29/swarm/27/job6/f1_eval_stability.py /agent/repos/base/build-release/forge /tmp/o6`
