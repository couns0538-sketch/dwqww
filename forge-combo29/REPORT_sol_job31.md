# Sol — Job 31 second-seed ageing and pruning-threshold matches

## Step 0 and the unchanged multiplier

Job 4 and H each passed all eight fresh-process pins. Defaults returned 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 returned 242796 and 656517, and PC20 returned 278024 and 587276. H explicitly set `HistoryAgeKeep 1024` for the pins. Job 4 used executable SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333` and H used `3cf1903d4713ed00acf61965bd20ef6fe01c71db994dbc34f3886faba5a4411c`. [Job 4 raw pins](sol/job31/pins/job4/step0-count.raw.txt) · [H raw pins](sol/job31/pins/H/step0-count.raw.txt)

The multiplier remains **1200** from Job 30's `mstar.txt`, line 1. H is the original Job 28 executable, with GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and embedded AL1 s198. Its build and net were shared across both match seeds. [Job 30 selection, line 1](sol/job30/mstar.txt#L1) · [H build receipt](sol/job28/h-build-receipt.txt)

## K21 and C21 controls

- **K21 PASS.** H with PC20, keep 896 and multiplier 1200 at 2,000 nodes per move on both sides replayed exactly the same ordered UCI moves and scored 1–1 in all 50 pairs. A went 32–32–36 in 100 games, pentanomial `[0, 0, 50, 0, 0]`. [K21 PGN](sol/job31/raw/K21.pgn) · [Independent readback](sol/job31/independent-K21-full.txt)
- **C21 PASS.** Both sides used H with PC20, keep 1024 and multiplier 2220. The 1,000-node A side went 19–138–43 against the 2,000-node B side in 200 games, pentanomial `[46, 31, 19, 4, 0]`. Its Elo was −238.12 [−285.07, −191.17], so the 95% upper bound was below zero. [C21 PGN](sol/job31/raw/C21.pgn) · [Independent readback](sol/job31/independent-C21-full.txt)

The forecast used Job 30's numbers and was the sole file in commit `efc3fa3`, after both controls and before M3b. [Frozen prediction](sol/job31/prediction.txt)

## Prediction grades

The frozen forecast used Job 30’s numbers. The ranges are inclusive and apply to the fresh match. The forecast reading applies to the declared pooled rule.

| Match | Forecast Elo | Observed / grade | Forecast pooled reading | Observed / grade |
|---|---|---|---|---|
| M3b | [-9.00, +11.00] | +3.43 / met | LEVEL | LEVEL / met |
| M4b | [-27.00, +5.00] | -6.78 / met | WORSE | WORSE / met |

## Job 31 matches

Both sides used H with PC20, embedded evaluation, Threads 1, Hash 16 and OwnBook false. A used HistoryAgeKeep 896 with HistoryPruneMultiplier 1200, and B 1024 with 2220. Elo uses the symmetric 95% interval computed at full precision from the pentanomial counts. The two-sided exact sign test is descriptive.

| Match | Nodes per move | Status | Games in complete pairs | A W-L-D | Pentanomial | Exact same moves / pairs | Better | Worse | Exact two-sided p | Elo [95%] |
|---|---:|---|---:|---|---|---|---:|---:|---:|---|
| M3b | 2,000 | complete | 8,000 | 2776-2697-2527 | 377, 833, 1528, 858, 404 | 1/4000 | 1262 | 1210 | 0.305004 | +3.43 [-2.48, +9.34] |
| M4b | 20,000 | complete | 2,000 | 515-554-931 | 45, 256, 431, 229, 39 | 0/1000 | 268 | 301 | 0.179704 | -6.78 [-16.53, +2.98] |

## Pooled reading

For each node count: POOL = job 30's match plus job 31's match at that node count (pentanomial counts added; a cut or missing match is left out and named), Elo with its 95 % interval from the pooled counts. BETTER when the pooled interval lies wholly above 0 AND the job 31 match alone has a positive Elo; WORSE when it lies wholly below 0 AND the job 31 match alone has a negative Elo; LEVEL otherwise.

| Nodes per move | Job 30 Elo [95%] | Job 31 Elo [95%] | Included | Omitted | Pairs | Pooled pentanomial | Pooled Elo [95%] | Reading |
|---:|---|---|---|---|---:|---|---|---|
| 2,000 | +1.30 [-4.57, +7.17] | +3.43 [-2.48, +9.34] | M3, M3b | none | 8,000 | 764, 1652, 3081, 1717, 786 | +2.37 [-1.80, +6.53] | **LEVEL** |
| 20,000 | -12.51 [-22.81, -2.22] | -6.78 [-16.53, +2.98] | M4, M4b | none | 2,000 | 111, 510, 839, 459, 81 | -9.64 [-16.73, -2.55] | **WORSE** |

## What this check cannot see

The PC's engine (its net, its build, its other settings), keep values other than 896, budgets other than 2,000 and
20,000 nodes.

## Facts

- The manifest reserves 5,150 fresh UHO openings for the controls and second seed. Independent validation reproduced the original source rows and checked zero overlap among the four subsets, against all 114 earlier PGNs and against all 100 Job 3 replay starts. The prior PGN inventory includes both parts of Job 30's M3 and its M4. [Opening manifest](sol/job31/openings/manifest.json) · [Independent opening proof](sol/job31/openings-independent.txt)
- The K21 publisher initially assumed the new archive folder existed. I added the folder creation and published the original K21 bytes before C21 began. Both controls were published before the forecast. [K21 publication proof](sol/job31/independent-K21-published.txt) · [C21 publication proof](sol/job31/independent-C21-published.txt) · [UTC stamps](sol/job31/stamps.txt)
- M3b's verified push preceded the M4b launch at 20:48:35 UTC. M3b's two PGN parts restore all 31,182,193 original bytes and all 4,000 pairs. The largest part is 19,998,113 bytes. [M3b independent tally and byte check](sol/job31/independent-M3b-published.txt) · [PGN shard manifest](sol/job31/raw/M3b.pgn.manifest.json)
- M4b finished all 1,000 pairs at 21:08:44 UTC before its 21:16:20 cutoff. Its 8,069,140-byte PGN, stdout and metadata reached the remote at 21:08:48. Both fresh matches finished, and both earlier cells also qualified for the pools. [M4b independent tally and byte check](sol/job31/independent-M4b-published.txt) · [UTC stamps](sol/job31/stamps.txt)
- Both 20,000-node seeds have negative centers. M4b's own interval crosses zero, and the pooled interval lies below zero. Under the declared rule the 20,000-node bundle reads WORSE. The independent parser reproduced the two pentanomial sums and checked that the seeds use disjoint openings. [Independent pools](sol/job31/independent-pools31.txt)

## Suspicions

The bundle's closer aggregate pruning rate in Job 30's hard replay may still conceal changes in which moves get pruned. Both 20,000-node seeds point in the same direction for this setting bundle. These games do not measure the individual pruning choices behind that score. [Job 30 replay sweep](sol/job30/step3.txt)

## What I did not do

I reused the same H build and selected multiplier. I ran the controls and scheduled fixed-node matches in Codex Cloud, with no tracked engine-source changes, owner PC activity or training.

## What I am not sure about

The two seeds compare the same settings on independent opening sets from one book. They leave open how the bundle behaves with a different net, under a time control, or at untested node budgets. The bundle changes age and pruning threshold together, so the comparison cannot attribute the effect to either setting alone.

## Reproduction

Both seeds used H with PC20, embedded AL1 s198, Threads 1, Hash 16, one PV and OwnBook false. A used keep 896 with multiplier 1200, and B keep 1024 with multiplier 2220. Fastchess `alpha 1.8.3 20261107-d7b47e8` reversed colors for each opening and used four workers and a 300-move ceiling. [Raw games, UCI and runner receipts](sol/job31/raw)

From `forge-combo29/sol/job31`, use Python 3 and python-chess 1.11.2. The analyzer verifies and rejoins the split PGNs in a temporary directory.

```sh
python3 analyze_matches31.py raw --manifest openings/manifest.json --m-star 1200 \
  --history-root .. --prediction prediction.txt
```

[UTC stamps](sol/job31/stamps.txt) · [Final readback](sol/job31/readback.txt) · [Precommit tree](sol/job31/precommit-readback.txt)
