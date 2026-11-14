# EvalRule50Damp

The fifty-move rule draws a game after 100 half-moves with no pawn move and no capture. This engine already treats that clock as a draw, and treats checkmate on the hundredth half-move as a win. A static score is a claim about a conversion that still has to happen. As the clock rises, fewer quiet moves remain, so the static score a node reads should shrink toward zero. Clock 0 keeps the whole score. Each half-move already played drops one percent, so a clock near 100 keeps only a sliver (clock 90 keeps 10, clock 99 keeps 1, clock 100 keeps 0). Mate scores are not scaled: a forced mate is not a positional edge the clock can expire.

That percent is the shape asked for here. It is not a scale table taken from another engine. `Board::compute_key` hashes pieces, castling, en passant, and side to move, and does not hash the half-move clock, so one hash entry is shared by the same placement at many clocks. The raw evaluation stored in that entry stays unscaled. Each node scales it for its own clock when it reads it. A search score was built from evals already scaled for the clock that stored it, so with the option on that score is used only when the stored half-move clock matches. With the option off the extra check accepts every score the old gate accepted.

## Option

`EvalRule50Damp`, check, default false. It is printed in the `uci` answer. `setoption name EvalRule50Damp value true` turns it on and clears the hash. `false` turns it off and clears the hash. Any other value is rejected and the flag is left as it was.

The scale is `rule50_damped_static` in `forge-combo29/include/forge/search.hpp`. `Worker::qsearch` and `Worker::search` call it where the corrected static evaluation is copied into the node, and on the ply-limit return that would otherwise hand back a raw static evaluation. `ValueNone` and mate scores are returned unchanged. The hash store still writes `ss->raw_eval`, the unscaled evaluation, into the eval slot.

Source diff under `forge-combo29/src` and `forge-combo29/include`: 39 insertions, 7 deletions.

## Default pins

Threads 1, Hash 16, OwnBook false, every other option at default. Measured with

`cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`

and `cmake --build build -j`. `/usr/bin/c++` on this machine is Clang 18 and does not link, because it selects a GCC 14 libstdc++ that is not installed. The binary below was built with `CXX=g++-13` and those cmake flags.

Before the edit, and again after it with the option left off:

- `go perft 5` from the start position: 4865609
- `bench 11`: 312866
- `bench 13`: 862329

Setting the option on, then off, reproduces those three numbers. An invalid value while the option is off also leaves them in place. `go perft 5` with the option on is still 4865609. Perft does not read the evaluation.

## Option on

`bench 13` with `EvalRule50Damp` true: 1049205, repeated. That is not the default count.

On `4k3/8/8/8/8/3Q4/8/4K3 w - - 80 20`, depth 1 is 913 with the option off and 173 with it on. The hash eval slot is 821 in both searches, and 821 again for the same placement at clock 0. The stored evaluation was not scaled. Depth 4 is 880 at clock 0 on a fresh table, 141 at clock 80, and 917 at clock 0 on the table just filled by the clock-80 search. The shrunk score was not reused for the other clock. A losing depth-1 score goes from -891 to -169. Mate in one, `6k1/4Q3/6K1/8/8/8/8/8 w - - 90 40` and the same placement at clock 99, stays 31999 (`e7g7`) with the option off and on.

The same queen placement with the option on, depth 1, scores 903, 812, 675, 447, 219, 82, and 0 at clocks 0, 10, 25, 50, 75, 90, and 99. Depth 8 falls the same way: 888, 808, 669, 396, 155, 18, and 0. The hash eval slot stays 821 at every clock. A losing placement falls from -882 toward zero on that same clock list, and its stored eval stays -899. Mate in one stays 31999 at each of those clocks. Clock 99 is already a draw for the queen ending with the option off, because no quiet move remains before the hundredth half-move, so both settings score 0 there. Checkmate already on the board at clock 100, `6k1/6Q1/6K1/8/8/8/8/8 b - - 100 50`, scores -32000 with the option off and on.

## Searches under address and undefined sanitizers

`forge-combo29/tests_r3_01/eval_rule50_damp.cpp`, compiled with the engine sources, `-O2 -fsanitize=address,undefined`, and the same `FORGE_*` defines as the release build. `EvalRule50Damp` is on. Two walks of 200 games search to depth 10 from the start position: at most 18 plies (seed `0x51A7E0D5`) and at most 40 plies (seed `0xC0FFEE11`). Every fifth game has its half-move clock rewritten into 20..99. The run reports 0 illegal moves, 2 and 6 positions in check, and 40 raised clocks in each walk. AddressSanitizer and UndefinedBehaviorSanitizer print nothing and the process exits 0. The same suite exits 0 without sanitizers. A two-thread `go depth 6` with the option on from the start position returns `a2a3`.

No strength claim.

Not executed: a ply-128 node (that return calls the same scaler the tests check), and ThreadSanitizer.

option.EvalRule50Damp=true
bench 13 nodes 1049205

## Follow-up

Screen only. Same binary, `EvalRule50Damp` on versus off. Not a strength claim.

Owner build, because the machine has AVX-512F and BMI2: `CXX=g++-13 cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=x86-64-v4`, portable left at the CMake default off. Default pins on that binary: perft 5 = 4865609, bench 11 nodes = 312866, bench 13 nodes = 862329. Binary sha256 `778ba5bd02273550e7fc600768ec0f8913354b9039a3f310b59b0179eb19e9e6`. Source commit `85e0961064799c8f49f129b1d856490436b44354`. Implementation commit `40c7c468b1c64ffdcb203e4df326e6bf70a77281`.

fastchess alpha 1.8.3, tag `v1.8.3-alpha`, commit `d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75`. Book `UHO_Lichess_4852_v1.epd`, 2632036 lines, sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Neither the book nor fastchess is in the git tree.

```
/tmp/r3screen/fastchess -engine cmd=/agent/repos/dwqww/build/forge name=EvalRule50DampOn option.EvalRule50Damp=true -engine cmd=/agent/repos/dwqww/build/forge name=EvalRule50DampOff option.EvalRule50Damp=false -each proto=uci nodes=50000 option.Threads=1 option.Hash=16 option.OwnBook=false -openings file=/tmp/r3screen/UHO_Lichess_4852_v1.epd format=epd order=sequential start=S -games 2 -rounds 500 -concurrency 3 -report penta=true -ratinginterval 100 -pgnout file=forge-combo29/tests_r3fu_01/chunk_S.pgn min=true append=false
```

Concurrency is 3, one less than 4 CPUs. Chunks use start 1, 501, 1001, and so on, up to 9 chunks or 6 hours. The first engine is the option on.

Bench 13 nodes per second, five runs off then five runs on, alternating in one process. Node counts stayed 862329 off and 1049205 on.

| run | option | nodes | nps |
| --- | --- | ---: | ---: |
| 1 | off | 862329 | 1823105 |
| 2 | on | 1049205 | 1983374 |
| 3 | off | 862329 | 1933473 |
| 4 | on | 1049205 | 2073527 |
| 5 | off | 862329 | 1891072 |
| 6 | on | 1049205 | 2025492 |
| 7 | off | 862329 | 1834742 |
| 8 | on | 1049205 | 2045233 |
| 9 | off | 862329 | 1891072 |
| 10 | on | 1049205 | 2049228 |

Cumulative score, option on first. Elo is fastchess logistic Elo with the printed 95% interval. LOS is the fastchess figure for the option-on side. Pentanomial order is Ptnml(0-2): LL, LD, DD/WL, WD, WW.

| chunk start | games | W-L-D on | Elo | LOS | Ptnml(0-2) |
| --- | ---: | --- | --- | --- | --- |
| 1 | 1000 | 216-319-465 | -35.91 +/- 14.11 | 0.00% | 31, 161, 206, 84, 18 |

Cumulative after start 1: 216-319-465, Elo -35.91 +/- 14.11, LOS 0.00%, Ptnml 31, 161, 206, 84, 18. Further chunks are still running.
