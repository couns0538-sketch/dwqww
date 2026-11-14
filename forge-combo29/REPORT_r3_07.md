# NullSeeVeto

`NullSeeVeto` is one UCI check option. It defaults to false. With it left off, null-move pruning is the same search as before.

The rule comes from this task, not from another engine. Null-move pruning cuts a node off when the side to move can pass and the position still fails high. That cutoff is refused when the opponent already has a legal capture of a dearer piece by a cheaper one, and this engine's static exchange evaluation does not call that capture a material loss (`see_ge` at threshold 0). A piece can be attacked by a cheaper piece and still be safe: if the exchange loses material for the capturer, the cutoff stays allowed. The prices are this engine's `SeePieceValue`. Knights and bishops share that price, so one taking the other is not a cheaper-for-dearer capture. The king is ranked above the queen because `SeePieceValue` stores 0 for the king as a sentinel inside the exchange walk, not as a material price. No table, constant, or routine was copied from another engine.

The check runs only when a null-move cutoff would otherwise be attempted, and only when the option is on. The board is restored before search continues. Turning the option off does not call the check.

## Default pins

Threads 1, Hash 16, OwnBook false, every other option at its default. Measured on the release build (`cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`) before the source change, and again after it.

Before the change, at `e04556dd`:

- bench 11: 312866
- bench 13: 862329
- `go perft 5` from the start position: 4865609

After the change, option off (also after turning the option on and then off, and again on a Clang address/undefined build):

- bench 11: 312866
- bench 13: 862329
- `go perft 5` from the start position: 4865609

An invalid `setoption name NullSeeVeto value maybe` leaves the option off. The next bench 13 stayed 862329.

## Option on

`setoption name NullSeeVeto value true`, then bench 13: 929140 nodes. Same count on the Clang sanitizer binary. That is a different tree from 862329, so the option is live. This is not a strength result.

## Tests

`forge-combo29/tests_r3_07/null_see_veto_test.cpp` checks the predicate on constructed positions, including a loose queen taken by a knight, a rook defended by a pawn whose exchange still wins for the knight, and a rook on the promotion rank whose recapturing pawn promotes and whose exchange loses. The last of those must not veto. Equal captures, a bishop taking a pawn, a pinned capture, and an en-passant position must not veto either. Each of 200 searches to depth 10, with the option on, Hash 16, and one thread, returned a best move that was in the legal list. Every move of the returned principal variation was legal in sequence. The positions are a deterministic walk from the start position.

The same test was built with Clang 18.1.3 `-fsanitize=address,undefined -fno-omit-frame-pointer` against objects built the same way, and run with halt-on-error for both sanitizers and leak detection on. It printed `positions ok`, `searches 200 legal`, and `NullSeeVeto tests passed`, and exited 0 with no sanitizer diagnostic. An earlier g++ 13.3.0 build with the same sanitizers also exited 0 on 200 depth-10 searches of this search code.

Engine diff against `e04556dd`: 39 insertions and 4 deletions in `include/forge/search.hpp`, `src/search.cpp`, and `src/uci.cpp`. `CMakeLists.txt` was not changed.

Repeated at 14:01 UTC and again at 14:37 UTC on the same release binary: bench 11 was 312866, bench 13 was 862329, and start-position perft 5 was 4865609, both before `NullSeeVeto` was enabled and after it was set back to false. bench 13 with the option on was 929140 on both repeats. The Clang address/undefined test printed `searches 200 legal` with exit 0 and no sanitizer diagnostic on both repeats.

Not verified: playing strength, match score, or whether 929140 is better or worse than 862329. No games were played.

option name NullSeeVeto type check default false

bench 13 with NullSeeVeto on: 929140

## Follow-up screen

Equal-node screen of one owner binary. The CPU has AVX-512F and BMI2, so the build is plain Release with no `FORGE_*` override (`-march=x86-64-v4`, the CMake default). Default pins on that binary: bench 11 = 312866, bench 13 = 862329, start-position perft 5 = 4865609. `NullSeeVeto` on still changes bench 13 to 929140 nodes.

Both sides are that same binary. Threads 1, Hash 16, OwnBook false, `go nodes 50000`. Openings are sequential color-reversed pairs from UHO_Lichess_4852_v1.epd (sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`). Engine sha256 `58d52fb7ff960bf14d3191a5a90b064eda0347948fb306fb996617ffdd97593d`. Compiler: Ubuntu clang version 18.1.3. Id: Chess Engine Forge 6.4.24 candidate. This is a screen, not a strength claim. Equal nodes are not equal time: the on side makes a null move and generates captures on every null-move try.

bench 13 nodes per second, five alternating runs, off then on:

| run | off nps | on nps |
| --- | --- | --- |
| 1 | 1251566 | 1540862 |
| 2 | 1275634 | 1493794 |
| 3 | 1614848 | 1376503 |
| 4 | 1620919 | 990554 |
| 5 | 1409034 | 1378545 |

Mean off 1434400 nps, mean on 1356052 nps. Each bench is under a second, so the rate moves around. Node counts did not: every off run was 862329 and every on run was 929140. Raw lines are in `forge-combo29/tests_r3fu_07/bench13_nps.txt`.

Chunk 1, openings 0 through 199, 400 games. Command: `/tmp/screen_match /tmp/build-owner/forge /tmp/uho/UHO_Lichess_4852_v1.epd 0 200 4 forge-combo29/tests_r3fu_07/chunk_0001.pgn forge-combo29/tests_r3fu_07/chunk_0001_summary.txt`

W-L-D option on first: 87-99-214. Elo 95%: -10.43 [-30.73, 9.88]. LOS: 0.1570. Pentanomial pair points 0, 0.5, 1, 1.5, 2: 6, 53, 94, 41, 6. The interval includes zero. PGN and the summary text are `forge-combo29/tests_r3fu_07/chunk_0001.pgn` and `forge-combo29/tests_r3fu_07/chunk_0001_summary.txt`.

Chunk 2, openings 200 through 599, 800 games. Command: `/tmp/screen_match /tmp/build-owner/forge /tmp/uho/UHO_Lichess_4852_v1.epd 200 400 4 forge-combo29/tests_r3fu_07/chunk_0002.pgn forge-combo29/tests_r3fu_07/chunk_0002_summary.txt`

W-L-D option on first: 203-198-399. Elo 95%: 2.17 [-14.07, 18.41]. LOS: 0.6034. Pentanomial: 23, 92, 160, 107, 18. PGN and summary: `forge-combo29/tests_r3fu_07/chunk_0002.pgn` and `forge-combo29/tests_r3fu_07/chunk_0002_summary.txt`.

Cumulative after 1200 games (600 pairs): W-L-D option on first 290-297-613. Elo 95%: -2.03 [-14.79, 10.74]. LOS: 0.3778. Pentanomial: 29, 145, 254, 148, 24. The interval includes zero. Not a strength result.

Chunk 3, openings 600 through 1099, 1000 games. Command: `/tmp/screen_match /tmp/build-owner/forge /tmp/uho/UHO_Lichess_4852_v1.epd 600 500 4 forge-combo29/tests_r3fu_07/chunk_0003.pgn forge-combo29/tests_r3fu_07/chunk_0003_summary.txt`

W-L-D option on first: 237-254-509. Elo 95%: -5.91 [-19.79, 7.97]. LOS: 0.2021. Pentanomial: 20, 135, 208, 116, 21. PGN and summary: `forge-combo29/tests_r3fu_07/chunk_0003.pgn` and `forge-combo29/tests_r3fu_07/chunk_0003_summary.txt`.

Cumulative after 2200 games (1100 pairs): W-L-D option on first 527-551-1122. Elo 95%: -3.79 [-13.18, 5.60]. LOS: 0.2144. Pentanomial: 49, 280, 462, 264, 45.

Chunk 4, openings 1100 through 1499, 800 games. Command: `/tmp/screen_match /tmp/build-owner/forge /tmp/uho/UHO_Lichess_4852_v1.epd 1100 400 4 forge-combo29/tests_r3fu_07/chunk_0004.pgn forge-combo29/tests_r3fu_07/chunk_0004_summary.txt`

W-L-D option on first: 202-167-431. Elo 95%: 15.21 [1.03, 29.39]. LOS: 0.9823. Pentanomial: 7, 90, 175, 117, 11. This chunk's interval is above zero. It does not override the combined screen. PGN and summary: `forge-combo29/tests_r3fu_07/chunk_0004.pgn` and `forge-combo29/tests_r3fu_07/chunk_0004_summary.txt`.

Cumulative after 3000 games (1500 pairs): W-L-D option on first 729-718-1553. Elo 95%: 1.27 [-6.59, 9.14]. LOS: 0.6246. Pentanomial: 56, 370, 637, 381, 56.

Chunk 5, openings 1500 through 1899, 800 games. Command: `/tmp/screen_match /tmp/build-owner/forge /tmp/uho/UHO_Lichess_4852_v1.epd 1500 400 4 forge-combo29/tests_r3fu_07/chunk_0005.pgn forge-combo29/tests_r3fu_07/chunk_0005_summary.txt`

W-L-D option on first: 194-202-404. Elo 95%: -3.47 [-18.38, 11.43]. LOS: 0.3239. Pentanomial: 17, 96, 175, 102, 10. PGN and summary: `forge-combo29/tests_r3fu_07/chunk_0005.pgn` and `forge-combo29/tests_r3fu_07/chunk_0005_summary.txt`.

Cumulative after 3800 games (1900 pairs): W-L-D option on first 923-920-1957. Elo 95%: 0.27 [-6.68, 7.23]. LOS: 0.5308. Pentanomial: 73, 466, 812, 483, 66. The interval includes zero. Individual chunks move around that zero. Not a strength result. Play stopped here; the cap was 6 or 9 hours and was not used up.
