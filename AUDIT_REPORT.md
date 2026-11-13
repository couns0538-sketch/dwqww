# Forge audit on `cursor/forge-audit-f132`

Base: `fable/standalone-h512-20261111` at `efb2ff96`.
The fixes, tests and this report were introduced in `30db14b1eb10dee11633bc19f8d03c776a1ab960`. The line that records that hash is `e1c71e02`. The review follow-up (variety 0 in the book check, and `*_INIT` copies of the Clang library and header flags) is the next commit on this branch.
This work stays on this branch. It does not touch `main`, the Fable base, a lock branch, or another agent's branch.
No games were played in this session. Recorded Elo numbers below are quoted from files already on the base. They are not new results.

The machine used for every build and timing in this session is a 4-core Intel Xeon with AVX-512, GCC 13.3.0 and Clang 18.1.3. It is not the owner's PC. Container timings are not a speed or Elo claim. Bench node counts are the comparison that matters for the lock pins.

## Task status

| Task | Status | What was actually done |
|---|---|---|
| 1. UCI protocol | Done | Confirmed five protocol bugs on the pre-fix binary, fixed them, and retested with an interactive client that waits for `bestmove` before `quit`. |
| 2. NNUE incremental updates | Done | Classic accumulator updates matched a full refresh on 181 plies, including king moves, castling, en passant, promotions and a null move. No mismatch, so no accumulator fix. |
| 3. NNUE loading | Done | Compiled and ran the existing v3 loader tests, plus an empty-file case. 95,882 checks, 0 failures at 100,000 walk plies. HalfKA was not executed: the switch is off and the tree has no network file. |
| 4. Color symmetry | Done | 34 mirrored positions, 0 skipped as illegal. Hand-crafted eval and classic NNUE both matched. No reproducible asymmetry, so no eval change. |
| 5. Search profile | Profiled, no search edit | Five depth-13 benches. Nodes stayed on the pin. Time on this VM was 417–427 ms. No search-code change: the isolated candidates already measured on `f5c5efaae3f3` were noise and were not repeated. |
| 6. Move generation profile | Profiled, no movegen edit | Perft 5, five times, 23–24 ms, 4,865,609 nodes. Legal-move generation 10 ms / 200,000 calls. Make/unmake 14–15 ms / 50,000 passes. No movegen change. |
| 7. NNUE profile | Tried, not adopted | AVX2 accumulator update, default off. Bit-identical, and slower on this VM (update loop 31–32 ms versus 23–24 ms). Left at 0. |
| 8. Other agents | Partial, read-only | All 417 remote tips were enumerated. One tip changes `forge-combo29` sources relative to this base: `f5c5efaae3f3`. Its patch notes and part of the diff were read. That branch was not modified or built. |
| 9. Match / SPRT | Documented | Controls, the Elo formula, the practical game count and the recorded failure checks are below. No new match. |
| 10. Tactical suite | Done | `forge-combo29/tests/engine_checks.cpp`. Positions, sources and the moves the search played are below. |
| 11. Endgames | Done, no tablebases | Draws, mate, the 50-move rule and a KPK position were searched. There is no syzygy (or other tablebase) interface in this tree. |
| 12. Linux build | Done | GCC `-Wall -Wextra` on the edited sources: no warnings. Clang 18 links and matches the bench pins after a g++ library probe. No CPU-specific march was added. |
| 13. Branch index | Partial | 417 refs, 327 unique tips, file counts from local `git ls-tree` (not GitHub's 300-file cap). Report files were not read on every tip. |

## Protocol bugs that were confirmed, then fixed

The pre-fix binary is the g++ Release build of `efb2ff96`. Piped `go` plus `quit` was not used as evidence: `quit` calls `stop_search()` and aborts an unfinished search, which then prints the first legal move.

1. Option names were case-sensitive. `setoption name usennue value false` left the net on: `bench 11` stayed at 312,866 nodes instead of the net-off pin 375,354. Names are now compared case-insensitively, including tunables.
2. Checkbox values were case-sensitive. `OwnBook` `False` was rejected and the book still played `c2c4`. `true` and `false` are now accepted in any case. `yes` is still rejected.
3. `go depth 1 searchmoves h7h5 a7a6` printed `bestmove 0000` while startpos has legal moves. The search now returns the first legal move and does not pretend the position is terminal. A real `searchmoves a2a4` still returns `a2a4`.
4. A four-field FEN was rejected because the parser always consumed six tokens and ate the word `moves`. Four fields are padded with `0 1`, five fields with fullmove `1`. `Board::set_fen` is still strict.
5. `a7a8Q` and `E2E4` were rejected. `parse_uci` now lowercases the token. King promotions and illegal moves are still rejected.

The bestmove line also checks that the move is legal in the root, and that a ponder move is legal after that move. `0000` is kept for stalemate and checkmate.

## Tests that were run

`forge-combo29/tests/uci_protocol.py` against the fixed g++ binary: 0 failures. It covers `uci` / `isready`, lowercase `UseNNUE` against both bench-11 pins, `UseNNUE True`, rejected `yes`, lowercase `Hash`, the opening book at variety 0 (`e2e4`), `OwnBook False`, a finished depth-1 search, `stop` with no search, the four-field FEN, `a7a8Q`, `E2E4`, empty `searchmoves` (bestmove `a2a3`, not `0000`), stalemate `0000`, mate `f6g7`, promotion mate `f7f8q`, `go depth 3` with a ponder move, `go ponder` withholding bestmove until `ponderhit`, and black's clock (`btime 60` while `wtime` is 120,000). The first book sample happened to be `c2c4`. A later 20-run check at the default variety of 30 got `e2e4` 12 times and `c2c4` 8 times, so the test now sets variety to 0, which returns the highest-weight move, `e2e4`. The black-clock search returned in well under 2 seconds with `c7c5`. A separate 200 ms black budget reached depth 10 and played `e7e6` in about 12 ms of engine time. That is the soft time split of the 200 ms budget, not white's clock.

`forge-combo29/tests/engine_checks.cpp`, g++ Release, default switches: 889 checks, 0 failures.

- Perft, from the Chess Programming Wiki Perft Results page. Position 4's FEN ends in `R2Q1RK1 w kq`, not `R3K2R w KQkq`.
  - startpos depth 5: 4,865,609 in 24 ms
  - Kiwipete depth 4: 4,085,603
  - position 3 depth 5: 674,624
  - position 4 depth 4: 422,333
  - position 5 depth 3: 62,379
  - position 6 depth 3: 89,890
- Make/unmake restored FEN and zobrist across 80 random plies.
- Classic NNUE: 181 plies, 28 king moves, 4 castles, 1 en passant, 12 promotions, dirty counts 2/3/4 all hit, one null move. Maximum absolute accumulator gap versus a full refresh: 0. Eval gaps: 0. Worker incremental eval versus a fresh refresh: 0.
- Mirror: 34 positions. Doubling the mirror restores the startpos piece placement.

`h512/tools/nnue_v3_tests.cpp`, compiled with `FORGE_NNUE_V3=1`: at 100,000 walk plies, 95,882 checks, 0 failures. That includes the existing rejections (bad magic, wrong version, truncated file, extra bytes, checksum, hidden size, quantisation, flags, maps, w1/w2 range) and a new empty file, which fails with "too small" and leaves nothing loaded. Walk mismatches, kernel mismatches and eval mismatches were 0. Castling, en passant, promotions and king moves were all present in the combined walk. A 20,000-ply run failed only the per-configuration coverage check on the shortest net (0 en passant in that one 2,000-ply slice). The 100,000-ply run is the one that counts. HalfKA was not loaded.

Bench pins on the fixed g++ binary, Threads implicit, Hash 16, OwnBook off for the repeated series:

| Run | Nodes | Engine-reported time |
|---|---|---|
| depth 13, net on, five repeats | 862,329 every time | 417, 423, 426, 427, 418 ms |
| depth 11, net on | 312,866 | 157 ms |
| depth 13, net off | 907,205 | 388 ms |
| depth 11, net off | 375,354 | 159 ms |
| perft 5, five repeats | 4,865,609 every time | 24, 24, 24, 23, 24 ms wall |

Clang 18, after the CMake probe below, same pins: depth 11 net on 312,866; depth 13 net on 862,329 (407 ms on this VM); depth 13 net off 907,205. Perft 5 was 4,865,609.

## Tactical and endgame results

The oracle is a brute-force mate search in `engine_checks.cpp`. A position is accepted only when that oracle agrees, and the engine's move is then checked against the same oracle.

| Position | Source | Oracle | Search |
|---|---|---|---|
| `6k1/8/5QK1/8/8/8/8/8 w - - 0 1` | constructed queen and king versus king | mate in 1 | `f6g7`, score 31999 |
| same, halfmove 99 | 50-move rule has not yet triggered | mate in 1 | `f6g7`, score 31999 |
| `7k/5P2/6K1/8/8/8/8/8 w - - 0 1` | constructed promotion | mate in 1 | `f7f8q`, score 31999 |
| `k7/8/1K6/8/8/8/8/7R w - - 0 1` | constructed rook mate | mate in 1 | `h1h8`, score 31999 |
| same queen mate, halfmove 100 | the 50-move draw is already in force | a mating move exists | score 0, legal `f6a1` |
| `7k/6Q1/6K1/8/8/8/8/8 b - - 100 40` | checkmate on the side to move | mated | score -32000, `0000` |
| `7k/5Q2/6K1/8/8/8/8/8 b - - 0 1` | stalemate, checked by hand and by the generator | no move, not in check | score 0, `0000` |
| K vs K, KB vs K, KN vs K, same-color bishops | insufficient material | draw | score 0 |
| KNN vs K, opposite-color bishops | not insufficient | flag checked | not treated as a terminal draw |
| startpos knight shuttle back to the same position three times | repetition | `is_repetition()` true | score 0, legal `a2a3` |
| `8/8/8/8/8/4k3/4P3/4K3 w - - 0 1` | pawn ending, no tablebase to compare | not claimed | depth 8 score 164, `e1f1`, 1,434 nodes |

No syzygy, Gaviota or other tablebase code is in `forge-combo29`. The KPK score was not checked against a tablebase. Mate distance here is one ply for these constructed positions; longer endgame wins were not solved.

`scale_factor` treats an endgame score of exactly 0 as Black being the stronger side. That choice cannot change the tapered eval, because the endgame term is then multiplied by zero. The mirror suite did not find a case where the side-to-move eval differed.

## Speed

Default `FORGE_SPD_NNUE_ACC_AVX` is 0. The scalar update is the code the pins were measured on.

With the switch compiled on (`-DFORGE_SPD_NNUE_ACC_AVX=1`, AVX2, same sub-then-add per lane, unaligned loads):

- `engine_checks`: 889 checks, 0 failures, accumulator gap 0, so the values match the scalar refresh.
- Bench 13 nodes stayed 862,329. Five times: 433, 429, 426, 424, 424 ms.
- The update microbench (20,000 passes over the startpos legal moves) was 31, 31 and 32 ms, against 23, 23 and 24 ms for the scalar binary.

The vector update is bit-identical and slower on this Xeon. It is not enabled. This is not a statement about the owner's CPU.

Search and movegen were not edited. Depth-13 bench time moved by about 10 ms across five runs with identical nodes, so a change smaller than that would not have been visible here. Perft 5 moved by 1 ms. On `f5c5efaae3f3` the following isolated switches were already timed with a frozen ABBA protocol and left at default 0 because the cloud sample crossed parity. They were not repeated:

- `FORGE_SPD_CHECK_EVASION_PREFILTER` at `8c447f4e676f86ee034f82b33cd0856b00eed230`: median CPU ratio about 0.992 net-on and 0.987 net-off. Nodes matched. Called descriptive, not a speed gain.
- `FORGE_SPD_CHECK_SQUARE_PRESENCE` at `1e6c398dec7717868a740f5d322cf7434336345f`: median CPU ratio about 1.002 and 1.009. Not promoted.
- `FORGE_SPD_EVAL_BITCOUNT_PREDICATES` at `5f0a6e95ebdd49b45061cc942473f32e442869a6`: median CPU ratio about 1.003 net-on and 1.018 HCE. Unfavorable direction, not established.
- Compact pawn-cache layout at `703562d`: entry size 40 to 32 bytes is real; the bench ratios went both ways. Footprint only.

Those depth-18 node signatures (6,066,072 net on, 6,134,776 net off) belong to the older lock those notes name (`16833ecc`), not to this H512 tree's depth-13 pins.

## Match and SPRT

No SPRT tool was run. `h512/tools/match_elo.py` is a paired-opening calculator, not an SPRT:

- Each opening is two games, colors reversed, one Round.
- The unit is the pair. Score is the mean pair score divided by 2.
- Standard error is the sample standard deviation of (pair score / 2), divided by sqrt(pairs).
- Elo is `-400 * log10(1/score - 1)`. The 95% interval maps score ± 1.96 standard errors.
- Pairs with a missing game are excluded. Time losses and other abnormal endings are counted, and the notes recompute the interval without the pairs that contain them.

M9, declared in `h512/results/phase3/M9_DECLARATION.md` before the games: 2,000 games, 1,000 pairs, UHO_Lichess_4852_v1.epd, seed 2026111202, 10 s + 0.1 s, Threads 1, Hash 16, OwnBook false, NNUEArch true, concurrency 12, no adjudication, no early stop, both sides the same executable (md5 `0836190d2a2653dbbfad3904d187b446`). The declaration says 1,000 pairs resolve about 8 Elo. The pre-registered band was about -15 to +5 for the 1024-unit net. `h512/STATUS.md` records the outcome as -5.9 Elo, 95% interval -14.2 to +2.4, with 38 time losses in four resource-guard suspensions. Dropping those pairs left -5.9. That is the file's result. It was not replayed here, and it is not a claim that any change on this branch gained Elo.

M8 in the same STATUS file (+53.2 Elo at 30 s + 0.3 s, 1,000 games) is also a previously recorded PC result, with two time losses during a guard suspension. Not replayed.

Practical point from the declaration itself: a difference inside roughly ±8 Elo at 1,000 pairs is not resolved. A cloud container is the wrong place to run that match.

## Build portability

`g++ -Wall -Wextra` on the edited sources (`nnue.cpp`, `uci.cpp`, `board.cpp`, `search.cpp`): no warnings. The earlier full g++ build with the same flags, before the accumulator switch, also printed none.

Clang 18 could not configure. Two separate gaps on this image:

- The link test fails with `cannot find -lstdc++` because the unversioned library is only in GCC's private directory.
- The compile then fails with `'array' file not found` because this Clang looks for GCC 14 headers and only GCC 13 is installed.

`CMakeLists.txt` now, only when the compiler name matches Clang, asks `g++` for its libstdc++ directory and adds it to `CMAKE_EXE_LINKER_FLAGS`, `CMAKE_SHARED_LINKER_FLAGS`, and the matching `*_INIT` variables before `project()`. `project()` copies `*_INIT` into the cache. The plain variables are what this CMake 3.28.3 compiler check actually reads; without `*_INIT` that cache stays empty. A second configure does not append the directory again. If a small `#include <array>` program still does not link, the same pair of variables gets the versioned include directories from `g++ -dumpversion` and `g++ -dumpmachine`. A Clang that already compiles `<array>` is left alone. The march flag is still the existing `FORGE_MARCH` cache (default `x86-64-v4`). `FORGE_PORTABLE=ON` remains the way to drop PEXT and ZMM. Nothing here assumes the owner's CPU matches this VM.

## Other agents, without modifying their branches

Local `git for-each-ref` on `refs/remotes/origin`: 417 refs, 327 unique tips. `git merge-base` against this base, then `git diff --shortstat` limited to `forge-combo29/src` and `include`, found one tip with an engine diff: `origin/dot/review-20261110` at `f5c5efaae3f3` ("Preserve compact S11 proof, real-picker tests and diagnostic summary"). Nine files in that stat, but the tip also carries the patch series and a large test tree.

Read on that commit, not built:

- `forge-combo29/patches/dot-review/README.md`. Twenty-three patches, each switch default off. The note says performance and strength are UNPROVEN. The patches replay onto lock `16833ecc`, which is older than this H512 base.
- The four profile reviews named in the speed section.
- Parts of `board.cpp`, `book.cpp`, `eval.cpp`, and the C4, F6 and S2 patch files.

Concrete problem in `f5c5efaae3f3`, patch `C4-restricted-fallback.patch`, inside `FORGE_FIX_SMP_EXCEPTIONS`: `first_legal_fallback` walks the legal moves and returns the first one that is on the `searchmoves` list. If the list matches nothing, it returns `Move::none()`. That is `bestmove 0000` on the exception path, which is the same failure confirmed on this base for an empty restriction. The normal search path on that branch is not what I executed.

`F6-uci-case.patch` lowercases option names only when `FORGE_FIX_UCI_OPTION_CASE` is on, and still compares checkbox values to the exact strings `true` and `false`. `False` would still be rejected. That gap was confirmed on this base and is fixed here for the default build, not by enabling their switch.

I did not read the rest of that branch's test logs line by line, and I did not compile it.

## Branch census, and what was not read

An earlier local `git ls-tree -r` over all 417 tips (the count GitHub's file listing would truncate at 300) found 256 tips with more than 300 files. The largest was `forge/sol-pack31-20261025` at `17aa0cae1d36` with 22,790 files. Others in that pack series are `forge/sol-pack24-20261025` `fa469cd7de0f` (16,369), `forge/sol-jobACD-20261025` `92af902cb270` (16,264), `forge/sol-next-20261025` `dc5ff59faf02` (15,593). Those trees were counted, not read.

Tip-subject counts from the same pass, among 264 unique subjects: 48 tips share "Remove a script that deletes src and include; tablebase download scripts refuse unsafe file names". `h512/STATUS.md` on this base describes that as one ordinary commit on 57 branches, done 2026-11-12, not redone here. Five tips have only the script removal. Four have only the tablebase filename check.

Ideas, from files that were opened:

- Promising, already recorded on the owner's PC, not replayed: candidate 3 versus the lock in M8 (`h512/STATUS.md`, commit `efb2ff96` records the number). Not a change on this branch.
- Failed or not promoted: the 1024-unit net in M9, same file. The four dot-review speed switches above. The AVX accumulator update in this branch.
- Untested in this session: HalfKA file loading; any tablebase; the dot-review switches compiled on; the sol-pack trees; almost every other tip's `STATUS.md` / `REPORT.md`. Report-name occurrence across trees in the earlier count was 4,316 `REPORT.md` paths, 1,293 `STATUS.md` paths and 179 `REPORT.json` paths. That is a path count, not a reading count.

## Limitations and next steps

- No Elo and no SPRT. A match belongs on the owner's PC, with the declaration written first.
- HalfKA needs a network file and `FORGE_NNUE_HALFKA=1`. Neither was available in a way that executes on this tree.
- The tactical suite is mate-in-one positions plus draws. It will not catch a horizon bug at depth 12.
- The KPK score has no tablebase oracle.
- AVX2 update speed was worse here. Do not turn `FORGE_SPD_NNUE_ACC_AVX` on without a measurement on the target CPU, and do not treat a container timing as the decision.
- Reading every file on 327 unique tips was not done. The next useful pass is the sol-pack and research tips whose subjects are unique, starting from `STATUS.md` or `REPORT.md` at the tip, and only then a source diff when the report claims a result.
