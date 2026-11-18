# Sol — Job 12 games and agreement judges

## Step 0 and match gates

1. **The counting executable passed all eight fresh-process pins.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. Binary SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. [Step 0 raw output](sol/job12/step0-count.raw.txt)
2. **Fastchess and the openings verified.** GitHub's latest official release pointed to `v1.8.3-alpha`, commit `d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75`. Its version line was `fastchess alpha 1.8.3 20261107-d7b47e8`. The official `UHO_Lichess_4852_v1.epd` had 2,632,036 lines and SHA-256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. The host returned `nproc = 5`. [Build and opening receipts](sol/job12/build.txt)
3. **K passed 100/100.** Every color-reversed pair had the same opening FEN, identical ordered move list and 1–1 points. On 200 games with 20,000 nodes per search on both sides, A scored 49 wins, 49 losses and 102 draws. Fastchess printed pentanomial counts `[0, 0, 100, 0, 0]` and Elo 0.00 with zero halfwidth. [K PGN](sol/job12/raw/K.pgn) · [K output](sol/job12/raw/K.out)
4. **C passed.** Across 400 games at 10,000 versus 20,000 nodes per search, A scored 37–222–141 and pentanomial `[57, 86, 43, 13, 1]`. Fastchess printed Elo −173.89 with a 95% interval of [−201.37, −146.41], meeting both thresholds. Each side used plain PC20. [C PGN](sol/job12/raw/C.pgn) · [C output](sol/job12/raw/C.out) · [Pair and interval readback](sol/job12/gates-KC.txt)

The [prediction](sol/job12/prediction.txt) was committed alone as `cd6194c3d803daf9102649d7bd0fd46b157722f8` after K and C passed. E and I started after the push. The two processes each used two workers, the integer half of the host's five. K and C used five workers. Fastchess printed a rating block after each completed pair in E and I so a cutoff could keep a complete-pair interval. [UTC stamps](sol/job12/stamps.txt)

## Prediction grades

A nonzero Elo forecast requires the observed sign and a magnitude within a factor of 1.5. Zero requires zero. Judge forecasts are exact categories.

| Match | Forecast Elo | Measured Elo | Elo grade | Forecast judge | Measured judge | Judge grade |
|---|---:|---:|---|---|---|---|
| E | +25.00 | +9.73 | KILLED | neither | neither | survives |
| I | -48.00 | -3.30 | KILLED | neither | S | KILLED |

## Table G. Paired game outcomes and agreement judges

All results are from engine A's perspective. One C-normalized unit is 173.89 Elo. Judge coverage uses the inclusive 95% interval in those units.

| Match | Status | Paired games | W-L-D | Pentanomial | Elo [95% interval] | C-normalized Elo [95% interval] | R agreement doublings | S agreement doublings |
|---|---|---:|---|---|---|---|---:|---:|
| C | complete | 400 | 37-222-141 | 57, 86, 43, 13, 1 | -173.89 [-201.37, -146.41] | -1.0000 [-1.1580, -0.8420] | -0.7338 | -0.9216 |
| E | complete | 2000 | 555-499-946 | 35, 234, 411, 280, 40 | +9.73 [+0.02, +19.44] | +0.0560 [+0.0001, +0.1118] | -0.2374 | +0.5490 |
| I | complete | 2000 | 544-563-893 | 57, 261, 383, 242, 57 | -3.30 [-13.85, +7.25] | -0.0190 [-0.0796, +0.0417] | -0.5396 | -0.0196 |

E: Games side with neither.
I: Games side with S.

## Facts

- Both setting matches completed 1,000 color-reversed opening pairs, 2,000 games each, at 20,000 nodes per move for both engines. Fastchess launched both matches at 05:42:10Z. I finished at 06:18:45Z and E at 06:18:58Z, before the 06:24:28Z cutoff. Every scored game belonged to a complete pair. Two I games reached the requested 300-move ceiling and their PGNs label them adjudicated draws. The PGNs, intervals, settings and digests matched an independent readback. [Independent results](sol/job12/independent-EI.txt)
- E's +9.73 Elo interval barely cleared zero at the printed precision. Both judge estimates fell outside it, one on each side. I's −3.30 Elo interval included zero and the Stockfish estimate. The Forge estimate fell below it. For the half-node control C, Stockfish's −0.9216 doublings fell inside the C-normalized interval and Forge's −0.7338 fell above it.
- One of the four predictions survived. Both predicted Elo magnitudes were too large. The neither-judge prediction held for E, and the I interval included S.


## Suspicions

- The Job 4 counting source applies `EvalSwingMult` to the butterfly-history update after a qualifying quiet move at `src/search.cpp:2045–2057`. Its match behavior can depend on history carried across a game and on the evaluation used for that update.
- `IirDepth` changes both the minimum depth for IIR on a missing TT move and the minimum depth of the upper-bound TT reduction at `src/search.cpp:2203–2215`. This match changes their common setting.

## What I did not do

The games ran on Codex Cloud using the unchanged Forge counting executable. Engine source, engine weights and the owner's running tune were outside this job.

## What I am not sure about

The judge comparison uses two settings, one opening-order seed per setting, and Elo scaled by this one half-node control. A judge within a match interval is compatible with these data. General screening accuracy, results on the owner's net, and transfer to other node budgets remain unmeasured.

## Reproduction

Both sides used Forge PC r15 at `6b98f2170a3210e71beed04bbd2553972c253ed7`, the Job 2 counter patch and Job 4 buttons. The build used GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. Each used PC20, Threads 1, Hash 16 MiB, one PV, OwnBook false and embedded AL1 s198, weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. A's single effective variant was applied after PC20. A fresh A process acknowledged every match's full setup through `readyok`. The four sidecars retain the exact arguments, settings, seeds, opening and executable hashes, run UTC times and PGN/output digests. [Forge build](REPORT_sol_job4.md) · [Match files and metadata](sol/job12/raw)

The opening book supplied each starting FEN twice, with A and B exchanging colors. Fixed-node budgets, no adjudication flags for resign or draw, and the 300-move ceiling were the same where specified. The fastchess UCI path sends `ucinewgame` at the game start, `app/src/engine/uci_engine.cpp:167–174,368–371`. [Pinned fastchess source](https://github.com/Disservin/fastchess/blob/d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75/app/src/engine/uci_engine.cpp#L368-L372)

From `forge-combo29/sol/job12`, with Python 3 and python-chess 1.11.2, these commands read and validate the saved whole pairs and printed intervals.

```sh
python3 analyze_matches.py gates raw
python3 analyze_matches.py table raw --job10-dir ../job10 --job11-dir ../job11 --prediction prediction.txt
```

[Recomputed game counts and intervals](sol/job12/readback.txt) · [UTC stamps](sol/job12/stamps.txt) · [Precommit tree readback](sol/job12/precommit-readback.txt)
