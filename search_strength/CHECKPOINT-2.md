# Search-strength checkpoint 2

Date: 2026-11-13. Measurement record only. No Elo result, and no candidate is promoted.

Checkpoint 1 is `search_strength/CHECKPOINT.md`, commit `d970a779acf072910a9a75e8c09b2e2138acda67`, which matches `origin/cursor/forge-search-strength-20261113-9558` at the time that note was pushed. This file is the work after that commit.

## Source identities

- Base: `fable/standalone-h512-20261111` at `efb2ff960037087299332bc6a44baea69441a17a`.
- This branch: `cursor/forge-search-strength-20261113-9558`. Not pushed to `main`, `lock/combo29-20261110`, the Fable branch, or another agent's branch.
- Search-gap rule still in force: `fable52-search-gap-20261109` at `56a76b153bb88026f2d83d65df6e422b0f3298f9`, `FALSIFICATION.md` section 3. The decision set is gate games. None are in this checkout, so the rule cannot formally close or open a spec. Bench numbers are recorded against that rule and are not a substitute for it.

## Other agents read this round

Fetched after checkpoint 1. Revisions actually read:

- Correctness: `cursor/forge-correctness-20261113-e6b6` at `dff76c5808d0ceb7fc3940d1758991c3c33fb26d`. Read `forge-combo29/correctness/20261113/RESUME.md` and the `search.cpp` diff against the Fable tip. Their search edits are a larger bad-capture buffer, a zero-node answer before the terminal-root report, and a bare-king skip of late-move pruning and LMR when more than one worker is searching. One worker is unchanged, on purpose, because enabling that gate for one worker moves the depth-13 bench off the pins. Not duplicated here. Their branch was not written.
- NNUE: `cursor/forge-nnue-eval-20261113-22cc` at `1b9a8ec7252041b2e9d57179986d3a3021918e1f`. Read `h512/results/cloud_20261113/RESUME.md`. That work is the v3 refresh, the scorer, and an AVX-512 VNNI output sum. It does not change the search switches in this branch. Not duplicated. Their branch was not written.
- History index, unchanged since checkpoint 1: `cursor/forge-history-index-20261113-712a` at `b39453901cd47c654f94bb7ec0283fc7c7f0ceb0`.
- No evidence or benchmarking branch was on `origin` at this fetch.

## What changed since checkpoint 1

`FORGE_CONT4_READ` now affects quiet ordering only. The first build also added the ply-4 term inside `quiet_history()`, and late-move reduction uses that function, so reductions moved too. That combination was measured and then split. Reduction depth again uses plies 1 and 2 only. The ordering read stays in the move picker.

`FORGE_ETC_HASH_ONLY` (default off, and inert unless `FORGE_ETC_STATS` is also on) peeks the hash move and does not generate the move list. The full-child probe is unchanged. A rebuild of that probe, hash-only off, reproduced the checkpoint 1 depth-16 line exactly: eligible 26486, lookups 727953, hits 1289, below 52694, nodes 3024920, mismatch counters 0.

## Build

Same portable command as checkpoint 1: g++ 13.3.0, `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`. Binaries stayed in `/tmp` and are not committed.

`check_pins.sh` after the ordering split, switches off: `PINS MATCH combo29`. Kiwipete `perft 5` on that plain binary was already 193690690 in checkpoint 1. The hash-only binary also printed `PINS MATCH combo29`.

## Ply-4 ordering

This is a different tree. Node ratios against the lock pins are not a speed result and not Elo. The engine's own millisecond field is one run of that different tree.

The discarded combination (ordering plus the reduction term), net on, nodes / pin ratio at depths 11, 13, 16, 20, 22: 1.155, 0.928, 1.114, 1.475, 1.040. Net off: 0.944, 0.912, 1.115, 0.775, 0.775. Not the switch that remains.

Ordering only, the switch as committed:

| Depth | Net on nodes | Ratio to pin | Net off nodes | Ratio to pin |
|---|---|---|---|---|
| 11 | 338201 | 1.081 | 375223 | 0.9997 |
| 13 | 676264 | 0.784 | 881135 | 0.971 |
| 16 | 3021059 | 0.999 | 2567689 | 1.049 |
| 20 | 12365936 | 0.998 | 9958641 | 0.734 |
| 22 | 20896497 | 0.614 | 22833719 | 0.932 |

Pins, for the ratios: net on 312866 / 862329 / 3024920 / 12389307 / 34048354, net off 375354 / 907205 / 2448617 / 13573040 / 24506465.

Best moves, Hash 16, Threads 1, OwnBook false, UseNNUE true, one process per search so `quit` cannot abort `go`. Depth 12, eight bench positions: six best moves agreed. Differences: the mate-in-2 position, plain `f6h5` at cp 623 and the ordering build `g3g6` mate 2; the rook ending, `f7f6` against `g7g5`. Depth 16: startpos `e2e4` against `d2d4`; the middlegame `h2h3` against `c4d5`; the rook ending `g7g6` against `h7h5`. The mate-in-2 position was `g3g6` mate 2 for both at depth 16.

W1, `8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1`. The search-gap dossier says the lock plays `a1b1` from depth 22. The plain portable binary did that: `a1b2` at depth 16, `a1b1` at depths 22 and 28. The ordering build played `a1b1` at 16, 22, and 28. One position, three depths. Not a match.

The switch stays default off. A match would have to be run on the user's machine. This VM did not play one.

## Hash-move peek

Same counting rule as checkpoint 1, but only the hash move, with no move generation. Nodes stayed on the pins in every timed repetition and in `check_pins.sh`. `top_hits_fail_high` equals `top_hits` in every row below. Mismatch counters stayed 0. A first hash-only build still walked the picker after the hash move and cost about 3% to 5% at these depths; its counters matched the direct peek, so that time was generation, and it is not the cost used here.

Net on, direct peek:

| Depth | Hits | Below | Below/nodes |
|---|---|---|---|
| 11 | 4 | 112 | 0.036% |
| 13 | 13 | 252 | 0.029% |
| 16 | 216 | 3171 | 0.105% |
| 20 | 3727 | 43880 | 0.354% |
| 22 | 23248 | 248800 | 0.731% |

Net off, below/nodes: 0, 0.011%, 0.049%, 0.160%, 0.167%. Not timed.

Wall clock, `taskset -c 0`, four interleaved reps, Python `time.perf_counter` around the process. Not a lock NPS figure.

| Depth | Pair ratios (peek/plain) | Mean | Standard error |
|---|---|---|---|
| 16 | 0.9932, 1.0123, 1.0077, 1.0017 | 1.0037 | 0.0041 |
| 20 | 1.0265, 1.0173, 1.0047, 1.0063 | 1.0137 | 0.0051 |
| 22 | 1.0231, 0.9840, 1.0008, 1.0183 | 1.0065 | 0.0089 |

At depth 16 the mean overhead is 0.37% against a 0.10% node share, and one pair was faster than plain. At depth 20 the mean overhead is 1.37% against 0.35%. At depth 22 the mean overhead is 0.65% against 0.73%, inside a standard error of 0.89 points. Nowhere does the node share beat the lookup time by 2 points. The full-child result from checkpoint 1 is unchanged: depths 16 and 20 cost more than the nodes under every proving child, and depth 22's point estimate cleared 2 points only with a rough interval that reached under 2.

No cutoff was added. `FORGE_ETC` and `EtcDepth` are still unused.

## Decision

- Do not write an enhanced-transposition spec from these benches. The full probe does not pay at the depths the dossier named. The hash-move peek's possible saving is under 1% of nodes and is not larger than its own noise.
- Keep `FORGE_CONT4_READ` default off. The term changes the tree, including best moves, and it is not a measured gain.
- Do not treat either result as Elo or as a speed lock.

## Next

A match of the ordering switch, option off against on, belongs on the user's gate machine. This checkout still has no gate PGNs, so the transposition rule stays open only in the formal sense and closed as a reason to change the tree here. The bare-king multi-thread gate is the correctness branch's work; the one-thread version moves the pins and was left off there.
