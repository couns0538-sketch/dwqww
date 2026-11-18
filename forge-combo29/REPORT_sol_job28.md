# Sol — Job 28 HistoryAgeKeep matches

## Step 0, K17 and the H build

- Step 0 passed all eight fresh-process pins on the Job 4 counting executable, SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. Defaults returned 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 returned 242796 and 656517, and PC20 returned 278024 and 587276. [Raw Job 4 pins](sol/job28/pins/job4/step0-count.raw.txt)
- K17 passed. Two Job 4 engines with PC20 and embedded evaluation at 2,000 nodes per move replayed exactly the same ordered UCI moves and scored 1–1 in all 50 reversed-color pairs. A went 33–33–34 in 100 games, with pentanomial `[0, 0, 50, 0, 0]`. [K17 PGN](sol/job28/raw/K17.pgn) · [Independent K17 check](sol/job28/independent-K17.txt)
- I built H in a scratch copy of the actual Job 4 source. The 68-line patch has Git blob `5720475c7d860448d1db07be4bae1633944a8044` and SHA-256 `b793ee1f16e4af9b095de339ddceabb86c3eb839830024ae9bca427bdfa52d95`. It adds `HistoryAgeKeep` and the quiet-history scaling at search start in `src/search.cpp` and `include/forge/search.hpp`. H's executable SHA-256 is `3cf1903d4713ed00acf61965bd20ef6fe01c71db994dbc34f3886faba5a4411c`. Job 4 and H used the same compiler and linker settings and byte-identical embedded AL1 s198 weights. [Pinned patch](sol/job28/history_age.patch.txt) · [Build command and hashes](sol/job28/h-build-receipt.txt)

## Step 2. Known answers

Explicit `HistoryAgeKeep 1024` on H passed the same eight pins in fresh processes. The three warm replays used H, PC20, Threads 1, Hash 16 and embedded AL1 s198, with Job 3 games 1–20 in order and a `ucinewgame` reset before each game. Each row checks the last `info`-line node count and the reported best move. [Raw H pins](sol/job28/pins/H-explicit/step0-count.raw.txt) · [Replay summary](sol/job28/replay-summary.txt) · [Replay receipts](sol/job28/raw/replay)

| HistoryAgeKeep | UCI search | Reference | Exact rows | Sum of last-info nodes |
|---:|---|---|---:|---:|
| 1024 | `go softnodes 2000` | Job 3 A-soft-warm | 1,200 / 1,200 | 4,294,263 |
| 896 | `go softnodes 2000` | kimi5 keep896_soft | 1,200 / 1,200 | 4,080,162 |
| 896 | `go nodes 20000` | kimi5 keep896_hard | 1,200 / 1,200 | 16,285,974 |

K18 passed. H at `HistoryAgeKeep 1024` versus Job 4, with PC20 at 2,000 nodes per move and the same embedded evaluation, replayed exactly the same ordered UCI moves and scored 1–1 in all 50 pairs. A went 28–28–44 in 100 games, with pentanomial `[0, 0, 50, 0, 0]`. [K18 PGN](sol/job28/raw/K18.pgn) · [Independent K18 check](sol/job28/independent-K18.txt)

The prediction was the sole file in commit `49a432e` after Step 2 and before M1. [Frozen prediction](sol/job28/prediction.txt)

## Prediction grades

Ranges are inclusive. A cut uses the complete pairs actually played.

| Match | Forecast Elo | Observed / grade | Forecast unequal pairs | Observed / grade | Forecast reading | Observed / grade |
|---|---|---|---|---|---|---|
| M1 | [-14.00, +10.00] | +3.74 / met | [800, 1350] | 1237 / met | LEVEL | LEVEL / met |
| M2 | [-16.00, +12.00] | +0.35 / met | [450, 700] | 587 / met | LEVEL | LEVEL / met |

## Part B. HistoryAgeKeep games

Both sides used H with PC20, embedded evaluation, Threads 1, Hash 16 and OwnBook false. A used HistoryAgeKeep 896 and B 1024. The two-sided exact sign test is descriptive. The reading uses the symmetric 95% Elo interval.

| Match | Nodes per move | Status | Games | A W-L-D | Pentanomial | Exact same moves / pairs | Better | Worse | Exact two-sided p | Elo [95%] | Reading |
|---|---:|---|---:|---|---|---|---:|---:|---:|---|---|
| M1 | 2,000 | complete | 4000 | 1402-1359-1239 | 192, 415, 763, 418, 212 | 1/2000 | 630 | 607 | 0.531650 | +3.74 [-4.69, +12.17] | **LEVEL** |
| M2 | 20,000 | complete | 2000 | 580-578-842 | 62, 229, 413, 237, 59 | 1/1000 | 296 | 291 | 0.868885 | +0.35 [-10.15, +10.85] | **LEVEL** |

## What this check cannot see

The PC's engine (its net, its build, its other settings), keep values other than 896, budgets other than 2,000 and
20,000 nodes, games longer than your book's.

## Facts

- The opening manifest assigns 3,100 distinct positions from the pinned official UHO book. The selections are disjoint from all 106 prior archived PGNs, including both D2s parts, by exact FEN and by the first four FEN fields. An independent pass reproduced each source row and both overlap checks. All four subsets also avoid the 100 recorded Job 3 replay starts. [Opening manifest](sol/job28/openings/manifest.json) · [Independent opening proof](sol/job28/openings-independent.txt) · [Job 3 start comparison](sol/job28/opening-replay-crosscheck.txt)
- M1 finished before M2 started. I verified M1's raw PGN, stdout and sidecar on the remote at 19:15:19 UTC, then started M2 at 19:15:20 UTC. The M1 PGN is 15,357,687 bytes. [UTC stamps](sol/job28/stamps.txt) · [M1 byte comparison](sol/job28/independent-M1-published.txt)
- M2 finished at 19:34:57 UTC with all 1,000 planned pairs before the 19:48:05 cutoff. Its 7,980,835-byte PGN, stdout and sidecar reached the remote at 19:35:01 UTC. Both match PGNs fit in single files under the 20 MB limit. The independent full-UCI counts, paired scores and exact p-values agree with the primary audit. [M1 independent recount](sol/job28/independent-M1-full.txt) · [M2 independent recount](sol/job28/independent-M2-full.txt) · [M2 byte comparison](sol/job28/independent-M2-published.txt)

## Suspicions

Ageing all four tables together could change quiet move ordering and pruning in opposing directions. The move lists changed for all but one pair at each budget, yet both score intervals span zero. These games cannot apportion any effect among the four tables. [Patch](sol/job28/history_age.patch.txt)

## What I did not do

I built H and ran the fixed-node replay and match tests in Codex Cloud. I made no tracked engine-source edits and ran no training or experiments on the owner's PC.

## What I am not sure about

The games estimate outcomes on this book at fixed node counts. The tests leave open how much per-search ageing costs in CPU time and how it would fare under a time control. The two-sided sign test describes counts of unequal pairs. It discards the magnitude of the score difference within each pair.

## Reproduction

H and Job 4 used Forge PC r15 from `6b98f2170a3210e71beed04bbd2553972c253ed7`, the Job 2 counters and Job 4 buttons, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. H also uses the pinned ageing patch. Both embedded AL1 s198. The weights-source SHA-256 is `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. Fastchess was `alpha 1.8.3 20261107-d7b47e8`. All four matches used four workers, PC20, Threads 1, Hash 16, one PV, OwnBook false and a 300-move ceiling. [Build receipt](sol/job28/h-build-receipt.txt) · [UCI and fastchess receipts](sol/job28/raw)

From `forge-combo29/sol/job28`, use Python 3 with python-chess 1.11.2 to audit the published games and grade the frozen forecast.

```sh
python3 analyze_matches28.py raw --manifest openings/manifest.json \
  --h-sha 3cf1903d4713ed00acf61965bd20ef6fe01c71db994dbc34f3886faba5a4411c \
  --history-root .. --prediction prediction.txt
```

[UTC stamps](sol/job28/stamps.txt) · [Final readback](sol/job28/readback.txt) · [Precommit tree](sol/job28/precommit-readback.txt)
