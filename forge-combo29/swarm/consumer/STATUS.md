# STATUS — consumer seat

**State: COMPLETE.** All paths measured, 200 games played, every number in `FINDINGS.md`
traceable to a file in `evidence/`.

## Deliverable

A UCI client that speaks only documented commands (`uci`, `isready`, `setoption`, `ucinewgame`,
`position`, `go`, `stop`, `quit`), decides only from engine stdout, and is strict in exactly
one way: it never assumes a line the specification does not promise. Twenty-two assumptions,
written down before the first probe, each one a check in the client, each one exercised
against the engine's actual output.

## Headline

| | |
|---|---|
| assumptions | 22: **10 satisfied, 7 violated, 3 partial, 1 unsatisfiable by any engine output, 1 satisfied-but-dangerous** |
| games, strict client | **59 of 100 lost to a protocol failure**, all 59 independently verified as genuine threefold repetitions |
| games, naive client | 0 of 100 lost to protocol — but **36 of 40 sampled bail moves were not the move the engine's own search returns** |
| new divergences from `forge-findings.md` | 2 (trap 3aa wrong as written; the unbounded `go nodes` forms missing entirely) |

## Build and pins

```
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 \
cmake -S . -B /tmp/build-base -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/build-base -j4
```

`/usr/bin/c++` is clang 18 with a broken header path (the trap in the brief); `/usr/bin/g++`
13.3.0 with an explicit `LIBRARY_PATH` works. Host has AVX-512F + BMI2, so the CMake default
`-march=x86-64-v4` with PEXT + NNUE ZMM is the build measured.

Four honesty pins, measured on this binary **before** any assumption was tested:

| pin | expected | measured |
|---|---|---|
| `bench 11` | 312,866 | 312,866 |
| `bench 13` | 862,329 | 862,329 |
| `bench 16` | 3,024,920 | 3,024,920 |
| `go perft 5` | 4,865,609 | 4,865,609 |

## Files

| file | what it is |
|---|---|
| `FINDINGS.md` | **the report** |
| `ASSUMPTIONS.md` | the 22 assumptions, written before the first probe run |
| `client.py` | the client: documented UCI only, stdout only, every assumption a check |
| `engine.py` | bounded process driver (thread + `os.read`; never `select()`+`readline`, trap 2) |
| `games.py` | full games under a clock; `--allow-bail-play` selects the arm |
| `probe.py` → `evidence/wire-base.json` | 29 wire paths, raw output + arrival times |
| `analyse.py` | probe evidence → the verdict table |
| `selftest.py` | 31 checks proving the audit's own checks can fire |
| `bail_history.py` | rebuilds bail positions with full history (the repetition test) |
| `bail_harm.py` | move-list form vs FEN form: the bail's cost, 6 roots |
| `bail_cost.py` | what the naive arm pays, 40 sampled of 82 played bail moves |
| `verify_failures.py` | independent referee over all 59 strict-arm failures |
| `depth_ladder.py` | sec 1b's line-count claim across budget kinds |
| `go_values.py`, `trap3aa_startpos.py`, `divergences.py` | the malformed-`go` divergence |
| `unbounded.py` | the unbounded `go` forms, with an explicit window |
| `reader_trap21.py` | the depth-line reader deadlock, with a working control |
| `null_token.py`, `sm_matrix.py` | the `0000` discriminator and `searchmoves` arity |
| `bail_forfeit.py` | the mate-forfeit claim: **NOT REPRODUCED**, with the reason |
| `game_report.py` | per-arm summaries |

## Where each headline number comes from

| number in FINDINGS | evidence file |
|---|---|
| 59/100 protocol failures, 59/59 threefold | `evidence/verify-failures-strict.txt`, `evidence/games-100-strict.json` |
| 0/100 failures, 82 bail plies, 81 rep + 1 fifty | `evidence/games-100-naive.json`, `evidence/report-naive.txt` |
| 36/40 bail moves differ | `evidence/bail-cost.txt` |
| 0/6 on the hand-audited roots | `evidence/bail-harm.txt` |
| depth 64 / nodes 0 / empty pv | `evidence/depth-ladder.txt`, `evidence/verify-failures-strict.txt` |
| 0 depth lines on the book path, 0.46 ms | `evidence/wire-base.json`, `evidence/reader-trap21.txt` |
| one-sided clock bounded at 25 s | `evidence/wire-base.json` (`one_clock_missing`, `..._black`) |
| `go depth abc` = depth 1, not depth 5 | `evidence/trap3aa-startpos.txt`, `evidence/go-values-base.txt` |
| `go nodes abc` unbounded at 60 s / 118M nodes | `evidence/unbounded-60s.txt` |
| 31/31 selftest checks | `python3 selftest.py` |

## Honest limits

- Both game arms are one engine against itself: **no Elo claim**.
- `OwnBook false` was set for the games, so **0 book plies in the match**; the book path was
  measured separately and was not exercised inside a game.
- The 59% rate is a property of 50 ms/move self-play from ten short openings, not of chess.
- The mate-forfeit claim (sec 2) was **not reproduced** — the construction failed and is
  reported as such; the move-disagreement measurement stands in its place.

## One defect the selftest caught in this seat's own work

The C7 depth-inflation check originally ran only on NORMAL replies — so it could never fire on
the BAIL path, which is the only path where the engine reports a depth it did not search. The
planted fixture in `selftest.py` caught it; the check now runs on BAIL too. Recorded because a
check that cannot fire is trap 9, and this seat's own instrument had one.
