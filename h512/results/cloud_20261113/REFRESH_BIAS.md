# Cloud CPU: v3 refresh rebuilds from the bias when the diff is larger

Date: 2026-11-13. This is a bit-exact inference change measured on synthetic networks. It is not an Elo result, and the depth-16 search bench below does not show a node-rate change outside run-to-run noise.

## Source and machine

- Base: `fable/standalone-h512-20261111` @ `efb2ff960037087299332bc6a44baea69441a17a`
- Change: `refresh_from_pieces` in `forge-combo29/src/nnue_v3.cpp`. When the cached placement and the new placement differ in more columns than the new placement has pieces, the cache entry is copied from `b1` and only the current pieces are added. The comparison is `>`, so an empty entry (difference equals the piece count) stays on the add-only path. This is the same rule as `FORGE_NNUE_V2_FAST` bit 4 in `nnue_v2.hpp`, which that path already had and which v3 did not.
- The loader bound `max|b1| + 32 * max|w1| <= 32767` keeps every partial sum inside int16, so piece-type order and square order store the same bits.
- Compiler: g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
- Flags: `-std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -DNDEBUG` and `FORGE_NNUE_HIDDEN=256`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_SPD_TT_NOTLS=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SEARCH_SPEED2=1`, `FORGE_SPD_PREFETCH_EARLY=1`, `FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`, `FORGE_NNUE_V3=1`, `FORGE_FAIR_DIAG=1`
- CPU: 4-core Intel Xeon reported at 2400 MHz, AVX-512. One core via `taskset -c 1`. This is not the Zen 5 lock machine, and the build is not ThinLTO or PGO.
- Objects and exes stayed in `/tmp/forge-nnue-build` and are not in git. Timed objects: baseline `nnue_v3.o` sha256 `c66a0d4ad46790d9d54eac9cce5ad49d239979f4eef194ec22a2baa740918a4d`, new `ef932159b5de8a617715a827843f01d9e9e793142ea38ee03911bb984da2f320`. New diag exe sha256 `9eb5acc253d9f5bb3f4ec9bf9a5c289b76ac2702d755520fa975ef1c74adbfc5`.

## What was not available

Candidate 3, the wide pilot net, the lock exe, and the training shards are on the machine named in the H512 reports. They are not in this checkout. No match was played. Test set 3 was not scored. The history index at `cursor/forge-history-index-20261113-712a` @ `b39453901cd47c654f94bb7ec0283fc7c7f0ceb0` records that the v2 form of this shortcut did not move search NPS (0.9255x against 0.9266x). That measurement was not repeated here. The engine-correctness agent had not published a branch at the time of this note.

## Correctness

`h512/tools/nnue_v3_tests` (new binary sha256 `dd305a1a543ee9c49746a7aeba3816eecffc9eb152324cf2320a94bb0923df25`), command `/tmp/forge-nnue-build/forge_nnue_v3_tests /tmp/forge-nnue-scratch 100000`:

- 95960 checks, 0 failures. The previous log `h512/results/step3/nnue_v3_tests_combo29.log` had 95879 checks; the extra checks are the far-cache and near-bound cases added with this change.
- The four walk lines match that log exactly, including H128 45000 plies / 29316 evaluations / 0 mismatches and the total 100000 plies / 64987 evaluations / 0 mismatches / 0 kernel mismatches.
- Far-cache case, H1024, one king bucket, five dissimilar FENs repeated: accumulator equals the scalar full refresh.
- Near-bound net, `w1 = 1000`, `b1 = 700` (`32 * 1000 + 700 = 32700`): same equality after the positions share the single bucket.

Search node identity, synthetic nets, Threads inside the bench's `Searcher(16)`, Hash left at the bench default, `NNUEArch` true:

| Net | Depth | Nodes, baseline and new |
|---|---:|---:|
| H512 mirrored, 8 king buckets | 12 | 309106 |
| H512 mirrored, 8 king buckets | 16 | 21116907 |
| H1024, 1 king bucket | 8 | 27556 |

Nets (local only, not committed):

- H512 sha256 `80a533839051d08a3f6da51712ce6bf16a0c57a349fef573e9af2a4d28753d44`, file checksum `b79d7c52a35b3ab5`
- H1024 sha256 `97dfffa70e2c458d3f3c6a73ea6f45df2584ac8c36f3beaed08def9c6e28d755`, file checksum `fd4052a28027225c`

`h512/tools/nnue_v3_speed` checksums matched the baseline binary on every repeated run: H512 walk 200000 plies `-133029274`, H512 walk 1000000 plies `-679772115`, H1024 walk 80000 plies `-28173834`, H1024 walk 400000 plies `-152656135`, cold H512 `-4064000000`, cold H1024 `-681000000`. Output sums were unchanged (H512 `4558683`, H1024 `-982680`).

## Speed (not search NPS, not Elo)

`nnue_v3_speed` times `make_valid` plus `evaluate` on a random legal walk, and a separate loop that alternates two FENs through one refresh cache. The cold pair is a middlegame and a 9-piece endgame that share the black king square, so one king-bucket entry is rewritten every call. Columns are the feature columns actually added or removed.

Pinned H512 cold refresh, 1000000 alternations (2000000 perspective refreshes):

| Arm | columns | ns / call |
|---|---:|---:|
| baseline | 25000044 | 254.777, 234.511, 237.749 |
| rebuild from bias | 17000044 | 191.383, 191.748, 192.441, 199.470 |

Pinned H1024 cold refresh, same loop:

| Arm | columns | ns / call |
|---|---:|---:|
| baseline | 50000010 | 825.742, 830.931, 826.968 |
| rebuild from bias | 34000010 | 620.501, 627.563, 610.832 |

Earlier unpinned H1024 samples were 900 to 1162 ns and are not used. The pinned repeats above are the ones that agree with each other.

Search-shaped walk, H512, 1000000 plies, 500000 timed evaluations, checksum `-679772115` both arms. Refresh columns fell from 3245712 to 2343741.

| Arm | eval_only_ns |
|---|---:|
| baseline | 339.840, 351.767, 333.683 |
| rebuild from bias | 302.824, 302.572, 297.685 |

H1024 walk, 80000 plies, only 3298 refreshes. eval_only_ns stayed about 313 to 319 baseline and 308 to 312 new. The shortcut does not change a quiet move.

Depth-16 bench, same H512 net, two runs each, nodes 21116907 both arms:

| Arm | time ms | nps |
|---|---:|---:|
| baseline | 10307, 9919 | 2048792, 2128935 |
| rebuild from bias | 10114, 9872 | 2087888, 2139070 |

The baseline pair already differs by about 4 percent. The new pair sits inside that spread. This bench does not show a search speedup. A lower cold-refresh time is not a strength result.

## Left alone

Output kernel, incremental `apply_changes`, trainer numerics, `UseNNUE`, and the final test set. No network file in the repository was replaced.
