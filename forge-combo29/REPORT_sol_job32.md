# Sol — Job 32 independent NullMateGuard replication

## Step 0. H pins

H from Job 28 passed eight fresh-process pins with `HistoryAgeKeep 1024` explicitly set. Defaults returned 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 returned 242796 and 656517 bench nodes, and PC20 returned 278024 and 587276. H's executable SHA-256 was `3cf1903d4713ed00acf61965bd20ef6fe01c71db994dbc34f3886faba5a4411c`, with embedded AL1 s198. [Raw H pins](sol/job32/pins/H/step0-count.raw.txt)

## Step 1. HG patch and build

I read all 4,163 bytes of Astra5's patch at commit `8ddcee2c21097c64e6dfe16d44a3b3011b9c1c11`, blob `6c581bb6662b5acadccdc34da029199e130f6fb1` and SHA-256 `2f69d8a0965d328bebf37c151e10eeaed09eb4e51a52fa7b766d7e044dfedecb`. I used strict Git apply on a byte-compared copy of the H source. All five hunks matched with offsets. Both commands exited 0. [Pinned patch](sol/job32/null_guard_r15d.patch.txt) · [Build and command receipt](sol/job32/hg-build-receipt.txt)

`git apply --check --verbose` printed the following.

```text
Checking patch include/forge/search.hpp...
Hunk #1 succeeded at 250 (offset -3 lines).
Checking patch src/search.cpp...
Hunk #1 succeeded at 243 (offset 141 lines).
Hunk #2 succeeded at 332 (offset 142 lines).
Hunk #3 succeeded at 1922 (offset 17 lines).
Hunk #4 succeeded at 2184 (offset 34 lines).
```

`git apply --verbose` printed the following.

```text
Checking patch include/forge/search.hpp...
Hunk #1 succeeded at 250 (offset -3 lines).
Checking patch src/search.cpp...
Hunk #1 succeeded at 243 (offset 141 lines).
Hunk #2 succeeded at 332 (offset 142 lines).
Hunk #3 succeeded at 1922 (offset 17 lines).
Hunk #4 succeeded at 2184 (offset 34 lines).
Applied patch include/forge/search.hpp cleanly.
Applied patch src/search.cpp cleanly.
```

HG's executable SHA-256 was `626cd562ddd9a64364d45adb92f7cd21f5bd8cbae5a24ca5908e8bd5585f8d97`. It used the same CMake Release flags, link command and embedded AL1 s198 weights as H, with GCC 14.2.0, CMake 4.2.3, libstdc++ 6.0.33, glibc 2.41 and x86-64-v4. The weights-source SHA-256 was `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. [Build receipt](sol/job32/hg-build-receipt.txt)

HG matched all four default pins and both PC20 bench pins in fresh processes. Its UCI list contains `option name NullMateGuard type spin default 0 min 0 max 2`, identical to line 4 of Astra5's A/O/Guard0 run. [HG raw pins](sol/job32/pins/HG/step0-count.raw.txt) · [Exact option readback](sol/job32/pins/HG/option.readback.txt)

## Step 2. Astra5 known-answer replays

HG with PC20, embedded AL1 s198, Threads 1, Hash 16 and HistoryAgeKeep 1024 ran `go depth 12` with `ucinewgame` and `isready` before each position, one engine process per suite and guard value.

| Guard | Suite | Astra5 reference | Compared | Exact nodes and best move | Observed nodes | Expected nodes | Last info depth 12 | Gate |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 0 | O | `zero/O.tsv` | 200/200 | 200/200 | 8,315,168 | 8,315,168 | 200/200 | PASS |
| 0 | G | `zero/G.tsv` | 353/353 | 353/353 | 17,611,204 | 17,611,204 | 353/353 | PASS |
| 2 | O | `one/O.tsv` | 200/200 | 200/200 | 8,315,218 | 8,315,218 | 200/200 | PASS |
| 2 | G | `one/G.tsv` | 353/353 | 353/353 | 17,848,355 | 17,848,355 | 353/353 | PASS |

[Four replay captures](sol/job32/raw/replay) · [Pinned Astra5 references](sol/job32/oracle-proof.txt) · [Independent line readback](sol/job32/step2-readback.txt)

## K22 and C22 controls

- **K22 PASS.** Both sides used HG with PC20, keep 1024, guard 0 and embedded AL1 s198 at 2,000 nodes per move. All 50 reversed-color pairs replayed exactly the same ordered UCI moves and scored 1–1. A went 36–36–28 in 100 games, pentanomial `[0, 0, 50, 0, 0]`. [Raw K22](sol/job32/raw/K22.pgn) · [Independent proof](sol/job32/independent-K22-published.txt)
- **C22 PASS.** With the same build and options, A at 1,000 nodes per move went 22–139–39 against B at 2,000 nodes in 200 games. Pentanomial `[46, 31, 18, 4, 1]`. The Elo was −232.79 [−281.46, −184.12], so its upper limit was below zero. [Raw C22](sol/job32/raw/C22.pgn) · [Independent proof](sol/job32/independent-C22-published.txt)

The prediction was the only file in commit `3641acf`, after both controls and before M5. [Frozen prediction](sol/job32/prediction.txt)

## Prediction grades

| Match | Forecast Elo | Observed / grade | Forecast reading | Observed / grade |
|---|---:|---|---|---|
| M5 | [-6.00, +10.00] | -1.69 / met | LEVEL | LEVEL / met |
| M6 | [-13.00, +15.00] | -0.35 / met | LEVEL | LEVEL / met |

## Job 32 matches

HG on both sides with PC20, embedded evaluation, Threads 1, Hash 16, HistoryAgeKeep 1024 and OwnBook false. A used NullMateGuard 2 and B 0. Elo and its symmetric 95% interval use complete pairs. The exact two-sided sign test is descriptive.

| Match | Nodes per move | Status | Games | A W–L–D | Pentanomial | Same moves / pairs | Better | Worse | Exact p | Elo [95%] | Reading |
|---|---:|---|---:|---|---|---:|---:|---:|---:|---|---|
| M5 | 2,000 | complete | 8,000 | 2700-2739-2561 | 28, 182, 3615, 151, 24 | 2138/4000 | 175 | 210 | 0.0829975 | -1.69 [-3.67, +0.29] | **LEVEL** |
| M6 | 20,000 | complete | 2,000 | 548-550-902 | 22, 153, 648, 159, 18 | 69/1000 | 177 | 175 | 0.957503 | -0.35 [-7.75, +7.05] | **LEVEL** |

## Descriptive comparison with Astra5

Astra5 used its r15d guard build with the same embedded weights, PC20, Guard 2 versus 0, Threads 1, Hash 16 and fixed nodes on the pinned UHO source. Its native build differs from HG. I subtract the unrounded Elo estimates and combine paired 95% halfwidths in quadrature for the disjoint samples.

| Nodes | Astra5 job / seed | Astra5 games | Astra5 Elo [95%] | Sol match | Sol Elo [95%] | Sol minus Astra5 [95%] | Shared opening keys |
|---:|---|---:|---|---|---|---|---:|
| 2,000 | 8 / M1 (7313) | 2,000 | +3.65 [-0.09, +7.39] | M5 | -1.69 [-3.67, +0.29] | -5.34 [-9.57, -1.11] | 0 |
| 2,000 | 9 / M1b (7323) | 2,000 | -0.52 [-4.01, +2.97] | M5 | -1.69 [-3.67, +0.29] | -1.17 [-5.18, +2.84] | 0 |
| 20,000 | 8 / M2 (7314) | 800 | +7.82 [-3.59, +19.22] | M6 | -0.35 [-7.75, +7.05] | -8.17 [-21.76, +5.43] | 0 |
| 20,000 | 9 / M2b (7324) | 800 | +6.52 [-5.78, +18.81] | M6 | -0.35 [-7.75, +7.05] | -6.86 [-21.21, +7.49] | 0 |
| 20,000 | 11 / M2c (7333) | 800 | +5.21 [-7.41, +17.84] | M6 | -0.35 [-7.75, +7.05] | -5.56 [-20.19, +9.07] | 0 |
| 20,000 | 11 / M2d (7334) | 800 | -4.78 [-16.66, +7.11] | M6 | -0.35 [-7.75, +7.05] | +4.43 [-9.57, +18.43] | 0 |

[Astra5 data and source hashes](sol/job32/astra5-prior32.json) · [Job 8](https://github.com/couns0538-sketch/dwqww/blob/8ddcee2c21097c64e6dfe16d44a3b3011b9c1c11/forge-combo29/REPORT_astra5_job8.md) · [Job 9](https://github.com/couns0538-sketch/dwqww/blob/8ddcee2c21097c64e6dfe16d44a3b3011b9c1c11/forge-combo29/REPORT_astra5_job9.md) · [Job 11](https://github.com/couns0538-sketch/dwqww/blob/8ddcee2c21097c64e6dfe16d44a3b3011b9c1c11/forge-combo29/REPORT_astra5_job11.md)

## Facts

- The 5,150 reserved positions are disjoint from all 119 prior Sol PGNs, 100 Job 3 starting positions and 3,597 distinct Astra5 guard-game openings. I kept all four planned seeds and regenerated the unused selections with the extra exclusions. That replaced 10 M5 positions and one M6 position before any games. [Manifest](sol/job32/openings/manifest.json) · [Independent opening proof](sol/job32/openings-independent.txt) · [Reselection receipt](sol/job32/openings-reselection.txt)
- The first M5 readback stopped at round 1481. The pinned EPD recorded `d6` as the en-passant target, and fastchess's PGN recorded `-`. The capture `e5d6` exposes the white king to the black queen. Both FENs have the same 39 legal moves. The pinned fastchess parser drops the unusable square and sends its canonical FEN to both engines. I retained the exact book, PGN and manifest and corrected the audit to compare legal en-passant rights. The canonical readback verified all 4,000 M5 opening keys and found zero overlap across all four subsets and all three archives. [Fastchess FEN parser](https://github.com/Disservin/fastchess/blob/d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75/app/third_party/chess.hpp#L3696) · [Fastchess opening decode](https://github.com/Disservin/fastchess/blob/d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75/app/src/matchmaking/match/match.cpp#L243) · [Canonical opening receipt](sol/job32/opening-ep32.json) · [Independent FEN check](sol/job32/independent-ep32.txt)
- M5's original 31,140,957-byte PGN reached the remote in two parts at 21:31:34 UTC, before the M6 wrapper started. The largest part is 19,997,976 bytes. The verified reconstruction kept all 4,000 pairs intact. [M5 archive verification](sol/job32/M5.PGN-publication.txt) · [UTC stamps](sol/job32/stamps.txt)
- I rechecked the named Astra5 reports and all six source PGNs, metadata files and Elo receipts on the later branch tip. Every input matched the pinned comparison bytes. [Astra5 branch readback](sol/job32/astra5-current-readback.txt) · [Original Elo output](sol/job32/astra5-elo-source32.txt)
- M6 finished at 21:51:44 UTC, before the 21:55:31 cutoff. Its 8,052,504-byte PGN, stdout and metadata reached the remote at 21:51:47. Both measured matches completed all scheduled pairs and both audit paths agree on the raw counts. [M5 independent tally](sol/job32/independent-M5-published.txt) · [M6 independent tally](sol/job32/independent-M6-published.txt)
- Both guard-2 comparisons read LEVEL on HG. Five of the six descriptive Astra5 difference intervals include zero. The Job 8 M1 difference at 2,000 nodes was −5.34 Elo [−9.57, −1.11]. It is one comparison across different builds. [Match and difference tables](sol/job32/readback.txt)

## Suspicions

The guard changes the move sequence more frequently at the higher node budget. There were 2,138 identical move-list pairs out of 4,000 at 2,000 nodes, compared with 69 out of 1,000 at 20,000 nodes. More search may expose different paths around the guard, and these game logs cannot count how often the guard caused the first divergent move. [M5 independent recount](sol/job32/independent-M5-published.txt) · [M6 independent recount](sol/job32/independent-M6-published.txt)

## What this check cannot see

The PC's engine (its net, its build, its other settings), node counts other than 2,000 and 20,000, the guard
together with ageing.

## What I did not do

I applied Astra5's patch only in the scratch H copy and left the tracked engine source alone. I ran the tests in Codex Cloud with no training or owner PC activity.

## What I am not sure about

The match results apply to guard 2 versus 0 on HG and these node budgets. The cross-helper contrast still includes build differences and separate opening samples, so it cannot isolate which build detail accounts for a difference.

## Reproduction

HG matches used PC20, `HistoryAgeKeep 1024`, embedded AL1 s198, Threads 1, Hash 16, one PV and OwnBook false. Fastchess `alpha 1.8.3 20261107-d7b47e8` used four workers, reversed colors and capped games at 300 moves. [Build identity](sol/job32/hg-build-receipt.txt) · [Raw UCI and match settings](sol/job32/raw)

From `forge-combo29/sol/job32`, use Python 3 and python-chess 1.11.2. The analyzer verifies and rejoins split PGNs if needed.

```sh
python3 analyze_matches32.py raw --manifest openings/manifest.json \
  --hg-sha 626cd562ddd9a64364d45adb92f7cd21f5bd8cbae5a24ca5908e8bd5585f8d97 \
  --prediction prediction.txt --astra astra5-prior32.json
```

[UTC stamps](sol/job32/stamps.txt) · [Final readback](sol/job32/readback.txt) · [Precommit tree](sol/job32/precommit-readback.txt)
