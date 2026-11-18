# Sol — Job 33 NullMateGuard second seed at 20,000 and first seed at 80,000 nodes

## Step 0. Unchanged HG and fresh pins

I reused Job 32's HG executable, SHA-256 `626cd562ddd9a64364d45adb92f7cd21f5bd8cbae5a24ca5908e8bd5585f8d97`. All six fresh-process pins passed. With default options, `bench 11`, `bench 13`, `bench 16` and `go perft 5` returned 312866, 862329, 3024920 and 4865609 nodes. With PC20, the bench 11 and 13 pins were 278024 and 587276. HG uses GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and embedded AL1 s198. [Raw HG pins](sol/job33/pins/HG/step0-count.raw.txt) · [Job 32 build receipt](sol/job32/hg-build-receipt.txt)

## K23 and C23 controls

- **K23 PASS.** With HG, PC20, keep 1024 and guard 0 on both sides at 20,000 nodes per move, all 25 reversed-color pairs replayed identical ordered UCI moves and scored 1–1. A went 8–8–34 in 50 games, pentanomial `[0, 0, 25, 0, 0]`. [Raw PGN](sol/job33/raw/K23.pgn) · [Independent readback](sol/job33/independent-K23-published.txt)
- **C23 PASS.** With the same build and options, the 40,000-node side went 2–55–43 against the 80,000-node side in 100 games, pentanomial `[11, 32, 6, 1, 0]`. The Elo was −205.04 [−248.67, −161.41], with the upper bound below zero. [Raw PGN](sol/job33/raw/C23.pgn) · [Independent readback](sol/job33/independent-C23-published.txt)

The prediction was the sole file in commit `8b47d3d`, after both controls and before M7. It used Job 32 M6 and Astra5's 20,000- and 80,000-node results. [Frozen prediction](sol/job33/prediction.txt)
## Prediction grades

The frozen forecast disclosed its use of prior results.

> yes, Job 32 M6 and Astra5's 20,000- and 80,000-node results.

| Match | Forecast Elo | Observed / grade | Forecast reading | Observed / grade |
|---|---:|---|---|---|
| M7 | [-10.00, +10.00] | +1.39 / met | LEVEL | LEVEL / met |
| M8 | [-18.00, +15.00] | +2.78 / met | LEVEL | LEVEL / met |

## Job 33 matches

Both sides used pinned HG, PC20, embedded AL1 s198, Threads 1, Hash 16, HistoryAgeKeep 1024 and OwnBook false. A set NullMateGuard 2 and B set 0. M7’s reading is POOL20. M8 uses its own interval. The exact sign tests are descriptive.

| Match | Nodes per move | Status | Games | A W-L-D | Pentanomial | Same moves / pairs | Better | Worse | Two-sided exact p | Elo [95%] | Reading |
|---|---:|---|---:|---|---|---:|---:|---:|---:|---|---|
| M7 | 20,000 | complete | 2,000 | 560-552-888 | [18, 168, 623, 170, 21] | 70/1000 | 191 | 186 | 0.836817 | +1.39 [-6.18, +8.96] | **LEVEL** |
| M8 | 80,000 | complete | 500 | 121-117-262 | [5, 49, 139, 51, 6] | 3/250 | 57 | 54 | 0.849550 | +2.78 [-13.57, +19.13] | **LEVEL** |

## POOL20

The pool adds the paired buckets from completed M6 and M7. A cut or missing match is named and its buckets are excluded. BETTER requires a wholly positive pooled interval and positive M7 Elo. WORSE requires a wholly negative pooled interval and negative M7 Elo. All other results are LEVEL.

| Included | Omitted | Pairs | Pentanomial | Elo [95%] | Reading |
|---|---|---:|---|---|---|
| M6, M7 | none | 2,000 | [40, 321, 1271, 329, 39] | +0.52 [-4.77, +5.81] | **LEVEL** |

The pinned M6 standalone Elo was -0.35 [-7.75, +7.05]. M6 PGN, transcript and sidecar matched the Job 32 checkpoint `ec0dd36b04e4facc8279371f390a2367973f9ffa`.

## Astra5 pools beside Sol

Astra5’s r15d guard build used PC20 and the corresponding fixed-node guard 2 versus 0 comparison. The pools are descriptive, with Astra5’s counted pairs kept in its own build and opening samples.

| Nodes per move | Sol Elo [95%] | Astra5 complete cells | Astra5 pairs | Astra5 pentanomial | Astra5 Elo [95%] |
|---:|---|---|---:|---|---|
| 20,000 | +0.52 [-4.77, +5.81] | job8/M2, job9/M2b, job11/M2c, job11/M2d | 1,600 | [29, 253, 1018, 255, 45] | +3.69 [-2.34, +9.72] |
| 80,000 | +2.78 [-13.57, +19.13] | job12/M3, job12/M3b, job13/M3c, job13/M3d | 1,200 | [28, 247, 665, 237, 23] | -2.90 [-10.34, +4.55] |

[Astra5 pool source and archive hashes](sol/job33/astra5-prior33.json)

## Facts

- The books contain 1,325 distinct opening positions from the pinned UHO source. The independent readback checked them against all 124 older Sol PGNs, 100 Job 3 replay starts and 3,597 pinned Astra5 guard-game openings. No selected position needed en-passant normalization, and the normalized intersection counts were all zero. [Opening manifest](sol/job33/openings/manifest.json) · [Independent opening proof](sol/job33/openings-independent.txt) · [Legal en-passant receipt](sol/job33/opening-ep33.json)
- M7 finished all 1,000 pairs at 22:17:52 UTC. Its 8,014,438-byte PGN, stdout and metadata reached the remote at 22:17:56 before M8 began. The independent parser verified zero shared canonical openings between Job 32 M6 and M7, and both complete seeds enter POOL20. [M7 committed-byte verification](sol/job33/independent-M7-published.txt) · [Independent pool](sol/job33/independent-pool33.txt)
- The Astra5 refresh added Job 13's two completed 80,000-node seeds. The later comparison is based on four complete Astra5 seeds at each budget, with no cut or missing matches in either pool. Each pool's opening sets were disjoint after legal en-passant normalization. [Astra5 pool receipt](sol/job33/astra5-pools33.md) · [Original Elo records](sol/job33/astra5-elo-source33.txt)
- M8 finished all 250 pairs at 22:35:55 UTC before the 22:38:12 cutoff, and its PGN, stdout and metadata reached the remote at 22:35:57. The PGN is 2,027,775 bytes. No Sol match required a cut, and all four prediction cells matched. [Independent M8 readback](sol/job33/independent-M8-published.txt) · [UTC stamps](sol/job33/stamps.txt)

## Suspicions

The exact move lists diverged in 247 of 250 M8 pairs. A small change in the guard can propagate through later search choices, and the 80,000-node score interval is still wide. The game records do not trace which guard event first separated the moves. [M8 move-list tally](sol/job33/independent-M8-published.txt)

## What this check cannot see

The PC's engine (its net, its build, its other settings), node counts other than 20,000 and 80,000, time controls.

## What I did not do

I reused the original HG executable and ran the prescribed controls and fixed-node matches in Codex Cloud. I did not edit tracked engine source, run training, or run anything on the owner's PC.

## What I am not sure about

The pools describe these opening samples, build and fixed-node settings. Astra5 ran its native r15d guard build, and the comparisons by node budget do not isolate the effect of build differences.

## Reproduction

Both sides used HG, PC20, `HistoryAgeKeep 1024`, embedded AL1 s198, Threads 1, Hash 16, one PV and OwnBook false. The measured comparison used `NullMateGuard 2` versus `0`. Fastchess `alpha 1.8.3 20261107-d7b47e8` used four workers, reversed colors and capped games at 300 moves. [UCI, engine and match receipts](sol/job33/raw)

From `forge-combo29/sol/job33`, use Python 3 and python-chess 1.11.2.

```sh
python3 analyze_matches33.py raw --manifest openings/manifest.json --history-root .. \
  --prediction prediction.txt --astra astra5-prior33.json
```

[UTC stamps](sol/job33/stamps.txt) · [Final readback](sol/job33/readback.txt) · [Precommit tree](sol/job33/precommit-readback.txt)
