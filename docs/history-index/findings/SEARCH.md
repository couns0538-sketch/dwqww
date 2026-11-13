# Search findings

This file is thin on purpose. The search-gap, speed-lane, and movegen branches have not been read yet. What is here is only what the lock record and the H512/fair-eval reports say about search, plus the inventory of where the unread reports sit.

## Read

`forge-combo29/LOCK.md`, `forge-combo29/README.md`, `forge-combo29/docs/overnight/RANKED.md`, `forge-combo29/docs/context/HANDOFF.md`, and the search-related sections of the H512 and fair-eval reports. Blobs are in `COVERAGE.md`.

Combo29's overnight table is NPS against trial_w6, one thread, core 4, 10 blocks, one outlier dropped. Median deltas that won, from the table:

- combo29 (KING+SEE+EQ32+CLANG) +10.191% (CI 10.099..10.409)
- combo28 (SEE+EQ32+CLANG) +9.667%
- clang_four (KING+BADCAP+SEE+EQ32+CLANG) +9.516%
- Down to gcc_badcap +0.444% and combo6 +0.273%, still marked win
- Losses: combo9 (KING+EQ32) -0.427%; combo3 (KING+BADCAP) -5.965%
- Errors, no delta: gcc_see, combo25 (KING+EQ32+CLANG)

The lock text says combo29 is bit-exact with trial_w6 on nodes and on 12,000 FENs, and that the +10.19% NPS has no Elo claim. The handoff for three further candidates (clang_four as a scoped bundle, clang_only, gcc_king) says builds were not run: no exe, no pins, no match. Logs marked HISTORICAL are not results for those candidates.

H512 does not change move generation when the v3 switch is off. When the switch is on, bench node counts change because the evaluation changes. That is a different tree, not a search-patch speedup. Equal-node matches are the report's way of taking speed out. Candidate 1 loses that comparison; candidate 3 wins it. See `NNUE.md`.

Job D's U8 and run 5 NPS gaps versus the replica, on the same code, are tree effects. The per-evaluation microbenchmark says their inference cost matches the replica.

## Not read, and the reason they are next

| Branch | Tip | Files to read before new search work |
|---|---|---|
| `fable52-search-gap-20261109` | `56a76b153bb88026f2d83d65df6e422b0f3298f9` | `fable_search_gap/NO_QUALIFIED_GAP.md`, `FALSIFICATION.md`, `STATUS.md` |
| `fable52-speed-lane-20261109` | `08897a88e11c707c0ac4e39c19e44c06e1360bdd` | `fable_speed_lane/STATUS.md`, `BENCH.md` |
| `fable52-movegen-proof-20261110` | `2ff77f98927cf19d55d6cac5cf182a81eb0d71e6` | `fable_movegen_proof/PROOF.md` |
| `fable52-cpu-20261110` | `ea3759a9ec3b17c58e3daeab8ff31af53e7ae6ab` | `fable_cpu_speed/DONE.md`, `STATUS.md` |
| `cursor/speed-and-search-patches-c7cb` | `2cf370d3e7672c18692bfa044ec376e6e584eff6` | 36 files, mostly JS and patches. Subject: node-identical speed patches and tuned search changes. Not opened |
| `cursor/smp-threads-fixes-c7cb` | `c4314e3bde6e8372419227cc22b032319487aa71` | Subject only: patch paths for `search/smp.js` |

## Source inventory, not a review

`inventory/KEY_SOURCE_BLOBS.tsv` lists unique blobs whose basename is `search.cpp` or a neighbour. There are 95 `search.cpp` blobs and 71 `search.hpp` blobs across tips. None of those blobs were diffed in this checkpoint. A later pass should diff only the pairs a report names.

October `forge/` hourly branches are mostly repeated tips. Shared commit `356e863dbd86d2ce24b8ee9486d7406f1d525480` is the tip of 29 branches whose subjects are "Fix Forge 6.4 native CI to compare pinned pre-fix commit". Branch names about terminal-zero nodes, qsearch, and later hours do not add a commit. Read that commit once if the CI fix matters, and do not read it 29 times.
