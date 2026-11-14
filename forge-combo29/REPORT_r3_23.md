# r3-23 SoundMatePruning

## Where the idea comes from

Audit finding 4 on `audit/lock-source` at `302a08a272fbe8e8c4463731f3b9cd72d72d3f48`, in `forge-combo29/AUDIT_lock_source.md`. The position and the depth-8 / depth-9 search are the ones in `forge-combo29/tests_audit/proof_pruning_mating_and_check.cpp` on that commit. The finding is that move-loop pruning in `Worker::search` still runs on a principal-variation node, while in check, and when alpha is already a mate score. A skipped move can hide a faster mate, and the node can still be stored as an exact transposition score.

The option, the guard, and this note were written for this tree. No search constants or tables were taken from another engine. The proof keeps that position.

## What changed

`SoundMatePruning` is a UCI check option, printed by `uci`, default `false`. `setoption name SoundMatePruning value true` or `false` sets it. Any other value is rejected and the flag stays put. Changing the flag clears the search state, so a later search does not keep transposition scores or histories built under the other setting.

The move-loop block is unchanged when the option is off: not the root, not a mate-search, half-move horizon under 100, a score already better than a fastest loss, the side has non-pawn material, and bare-king mode is off. When the option is on, that block is also skipped if the node is a PV node (`beta - alpha > 1`), the side to move is in check, or `is_mate_score(alpha)`.

## Default pins

Threads 1, Hash 16, OwnBook false, every other option left at default. Printed before the edit, and again on the final binary:

- `bench 11`: 312866
- `bench 13`: 862329
- `go perft 5` from the start position: 4865609

The same three numbers were printed by a clang 18 build of the same sources (`-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`). On this machine `/usr/bin/c++` is clang and does not see the libstdc++ headers, so the g++ 13 binary was configured with `-DCMAKE_CXX_COMPILER=g++`, and the clang binary was given the libstdc++ include path explicitly.

## Proof position

`kbK5/pp6/1P6/7p/8/7P/7B/1R6 w - - 0 1`

The audit text calls `1.Ra1` mate in 3 and gives `1...a6 2.Rxa6 bxa6 3.Kxb8#`. That king capture is illegal: the white king would move from c8 to b8, next to the black king on a8. A full-width legal-move search finds no forced mate in 6 plies or fewer. The shortest forced mate is 7 plies, score `32000 - 7 = 31993`, which UCI prints as `mate 4`. One such line is `h2c7 h5h4 c7b8 a7a6 b1a1 a6a5 a1a5`. Replaying it is checkmate. The same distance count puts `h2b8`, `h2c7`, and `b1a1` on that minimum, and longer mates on other moves (`b1h1` and `b1b2` in 9 plies, `h2g1` in 11).

`SoundMatePruning=false`, fresh search, Hash 16, one thread:

- depth 8: `h2b8`, score 31991 (`mate 5`), 890 nodes, PV `h2b8 h5h4 b1b4 a7a6 b4h4 a6a5 b8d6 a5a4`. Replaying that PV does not checkmate.
- depth 9: `h2b8`, score 31991, PV through `h4a4`. That longer line does checkmate (9 plies, `mate 5`).

`SoundMatePruning=true`:

- depth 8 and depth 9, exclusive table and a depth-8 shared table: `h2b8`, score 31993, PV `h2b8 h5h4 b1a1 a7a6 a1a6 b7a6 b6b7`. Replaying the PV is checkmate, and `32000 - 7 = 31993`.
- A fresh UCI `go depth 8` prints `score mate 4`, 3088 nodes, the same PV, `bestmove h2b8`.
- Turning the option off again and searching depth 8 returns the original `mate 5` line and 890 nodes. `bench 11`, `bench 13`, and `perft 5` in that same process are the three pins above.
- The proof program passed again under address and undefined-behavior sanitizers.
- The clang binary, option left off, matches the g++ depth-8 line (`mate 5`, 890 nodes). With the option on it matches the g++ mate (`mate 4`, 3088 nodes, the same PV).

## Follow-up

Replaying one principal variation is not treated as proof that the mate is forced. `forge-combo29/tests_r3fu_23/mate_and_arms.cpp` walks every legal defender reply. A full-width legal-move search of `kbK5/pp6/1P6/7p/8/7P/7B/1R6 w - - 0 1` finds no forced mate in 5 or 6 plies and a forced mate in 7 (41041 prover nodes, 6801 defender replies). With the option off, depth 8 still returns 31991 (`mate 5`) for `h2b8`. With the option on, depth 8 and 9 return 31993. After `h2b8`, every black reply (`h5h4`, `a7a6`, `a7a5`, `a7b6`) still loses within the remaining plies.

The three cases are separate arms. `FollowOption` tracks the UCI check, so the default option is unchanged. Forcing one arm at a time, depth 8 on the proof position: the PV arm alone and the mate-alpha arm alone each return 31993, and the in-check arm alone stays at 31991. On a fixed set of positions at depth 8, with tracing enabled and every arm off, the search records PV prunes, in-check prunes, mate-alpha prunes, and quiet checks skipped after an earlier quiet had already been skipped (33 such quiet checks: 3 on PV nodes, 1 on a mate-alpha node). Turning on only that arm drops its counter to zero, including its quiet-check bucket, and changes the node total. No quiet check after a quiet failure was observed while the side to move was already in check: direct checks are ordered first there, and futility does not set the quiet skip while in check. The in-check arm still changes the tree (in-check prunes go from 41 to 0).

Owner build (`x86-64-v4`, PEXT and AVX-512 on, no `FORGE_*` override). Option off: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

The UHO screen uses `tests_r3fu_23/uho_screen.cpp` at 50000 nodes, Threads 1, Hash 16. Option-on is the first player in each color-swapped pair. Book `UHO_Lichess_4852_v1.epd`, sha256 of the zip `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`. Owner binary sha256 `c9173950c8336f1d5edf39078bf32321e4f1da2fbbd4b1ef5ac8482cd73f45bd`. Bench 13, five alternating runs, option on first: nps 936397, 923264, 950929, 918348, 1398584. Option-off node totals in those runs stayed 862329. Option-on bench 13 nodes were 980408.

Chunk 1, openings 0-399, 800 games: W-L-D 195-224-381 for option-on. Elo -12.600, 95% interval -30.071 to 4.808, LOS 0.078019. Pentanomial LL LD WL/DD WD WW = 18 108 176 81 17.

Slice 2, openings 400-799, 800 games: W-L-D 189-212-399. Elo -9.992, 95% interval -27.075 to 7.043, LOS 0.125172. Pentanomial 13 117 168 84 18.

Slice 3, openings 800-1199, 800 games: W-L-D 203-224-373. Elo -9.122, 95% interval -26.751 to 8.459, LOS 0.154596. Pentanomial 20 94 184 91 11.

Slice 4, openings 1200-1599, 800 games: W-L-D 205-231-364. Elo -11.296, 95% interval -29.116 to 6.465, LOS 0.106312. Pentanomial 17 112 160 102 9.

Slice 5, openings 1600-1999, 800 games: W-L-D 202-213-385. Elo -4.778, 95% interval -22.144 to 12.565, LOS 0.294575. Pentanomial 14 104 172 99 11.

Cumulative through 4000 games: W-L-D 994-1104-1902. Elo -9.557, 95% interval -17.361 to -1.762, LOS 0.008125. Pentanomial 82 535 860 457 66. PGNs and summaries are under `tests_r3fu_23/screen/`. Later slices are appended the same way.

## What was not verified

Playing strength was not measured. This position was not searched with more than one thread. No separate position was used to show the in-check arm by itself: in the proof, the node where the shorter mate is kept is not in check, and the option changes the result because alpha is already a mate score. The PV-node arm is the same predicate, but it was not isolated on its own position. The plain `cmake` line with `/usr/bin/c++` does not configure on this machine until the compiler can see libstdc++.
