# Sol — Job 29 threshold-matching replay stopped at the node-count gate

## Step 0 and HC build

- Job 4 and H with `HistoryAgeKeep 1024` set explicitly each passed all eight fresh-process pins. Defaults returned 312866, 862329 and 3024920 bench nodes and 4865609 perft nodes at depth 5. S14 returned 242796 and 656517, and PC20 returned 278024 and 587276. Both builds used embedded AL1 s198. [Job 4 raw pins](sol/job29/pins/job4/step0-count.raw.txt) · [H raw pins](sol/job29/pins/H-explicit/step0-count.raw.txt)
- HC uses H from Job 28 and the pinned 47-line Kimi counter patch, Git blob `c5b4ed88`, SHA-256 `04be507a5ebbfcabc333179813cf542764549f405149661be604d914e25cc39b`. H's existing Job 2 counters occupied two of the patch's context lines. I adjusted only the placement context. All eight inserted lines match the upstream patch byte for byte, and the adapted patch passed a zero-fuzz dry run. The build matches H's compiler, linker settings and embedded weights. HC's SHA-256 is `2c664f4e0f6099a4bed0a3db162d2a07fd479d175fedf5ae7c90e4c1ef875875`. [Pinned patch](sol/job29/count27.patch.txt) · [Context adaptation](sol/job29/count27-h-context.patch.txt) · [Build receipt](sol/job29/hc-build-receipt.txt)

## Step 2. Known-answer gate

**Gate failed.** HC with `HistoryAgeKeep 1024`, PC20, Threads 1, Hash 16 and embedded AL1 s198 ran the first 1,200 searches with `go softnodes 2000`. The statements about node count and best move matched the archived Job 28 rows. HP27's count also matched Kimi's known answer. The required equality between HP27's node field and the last depth line failed on 42 searches. [Fresh rows](sol/job29/raw/replay/keep1024_soft.jsonl) · [Replay metadata](sol/job29/raw/replay/keep1024_soft.meta)

| Check | Expected | Observed |
|---|---:|---:|
| Last depth-line nodes and best move matching Job 28 | 1,200 | 1,200 |
| HP27 lines summed | 1,200 | 1,200 |
| HP27 pruning events | 11,633 | 11,633 |
| Last depth-line node sum | 4,294,263 | 4,294,263 |
| HP27 node field equal to the last depth-line field | 1,200 | **1,158** |
| HP27 node sum | Informational | 4,561,961 |
| HP27 node field equal to the final softnodes diagnostic | Informational | 1,200 |

The first failing row is 29, game 1, zero-based ply 28. The last depth line was depth 8 and showed 1,965 nodes. The engine then printed these lines.

```text
info string softnodes nodes 8000
info string HP27 9 8000
bestmove b4b5
```

The fresh run matched all 1,200 archived Kimi rows on last depth-line nodes, best move, HP27 count and HP27 node field. Kimi's archived default soft run contains the same 42 mismatches. The archived keep-896 soft and hard mismatches are also documented in the independent readback. [Archived Kimi default-soft rows](https://github.com/couns0538-sketch/dwqww/blob/7ccde908be2577964408256344c61a6944a1c111/forge-combo29/tests_kimi5_job27/rows/ka2_soft_dfl.jsonl) · [Independent provenance](sol/job29/independent-hp27-provenance.txt)

## Step 3, prediction and Part B

The gate stopped Job 29. The remaining two Step 2 cases and the threshold sweep were unrun. There is no selected multiplier or frozen prediction. K19, M3 and M4 were unplayed.

## Facts

The H source emits node snapshots with each `info depth` line at `src/search.cpp:2787–2804`. It breaks out of a node-aborted iteration without publishing that iteration at `src/search.cpp:3045–3072`. The final `result.nodes` is captured at `src/search.cpp:3250–3251` and used for the softnodes diagnostic at `src/search.cpp:3261–3263`. The pinned patch prints that final `result.nodes` in HP27. [Patch, line 25](sol/job29/count27.patch.txt#L25) · [Independent source trace](sol/job29/independent-hp27-provenance.txt)

## Suspicions

The gate likely conflated the total work performed with the last published depth snapshot. Comparing whole-search counts against the last depth-line denominator can still reproduce the historical rate by convention. Normalizing by the final totals instead changes the baseline on the same soft replay from 2.709 to 2.550 prunes per 1,000 nodes, so it may change which multiplier the sweep selects. [Archived counts and node totals](sol/job29/archived-hp27-crosscheck.txt)

## What I did not do

I stopped after collecting the evidence for the first gate. I made no tracked engine-source changes and ran no training or work on the owner's PC.

## What I am not sure about

The replay establishes the difference between the counters. I have no result for which multiplier restores pruning under either denominator or whether a restored rate improves play.

## What this check cannot see

The PC's engine (its net, its build, its other settings), keep values other than 896, other ways to restore
pruning (depth, the improving factor), budgets other than 2,000 and 20,000 nodes.

## FOR FABLE AND OPUS

Should the next job keep the declared historical last-depth denominator and verify HP27's node field against the final total separately, or use final node totals for both the calibration baseline and the sweep? The two published node fields need separate assertions.

The replay driver, metadata, build receipt and UTC stamps identify the executable, inputs, commands and stopping point. [Driver](sol/job29/replay_hp29.py) · [UTC stamps](sol/job29/stamps.txt) · [Precommit readback](sol/job29/precommit-readback.txt)
