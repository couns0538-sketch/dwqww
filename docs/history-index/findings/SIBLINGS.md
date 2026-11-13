# What the other three branches had published

Observed with `git ls-remote` on 2026-11-13. None of these three tips had moved by the second lookup the same afternoon. They are not in the frozen 416-row `HEADS.tsv`. `branches/HEAD_MOVEMENT.tsv` records them as new. Their branches were not written.

| Branch | Tip read | What the tip says it is |
|---|---|---|
| `cursor/forge-correctness-20261113-e6b6` | `dff76c5808d0ceb7fc3940d1758991c3c33fb26d` | Legality, hash, and ponder checks, plus the fixes in `findings/BUGS.md` |
| `cursor/forge-nnue-eval-20261113-22cc` | `1b9a8ec7252041b2e9d57179986d3a3021918e1f` | v3 refresh, scorer parity, AVX-512 VNNI output sum |
| `cursor/forge-search-strength-20261113-9558` | `c9cb47a467a75051e1c6a09c4508f32f3bb9ddf9` | ETC counting probe and a ply-4 ordering read |

All three were cut from `fable/standalone-h512-20261111` @ `efb2ff960037087299332bc6a44baea69441a17a`. They had read this index at `b39453901cd47c654f94bb7ec0283fc7c7f0ceb0`, which does not yet contain the notes in this file.

## Correctness

Full read: `forge-combo29/correctness/20261113/RESUME.md` blob `dc1f5fd580f3b9b60a527c79a7a1fdcb37ba1b36`, plus the short pin and KRK logs next to it.

Their resume says pins still match combo29 after the buffer change, the position-prefix change, the perft-stop change, the zero-node change, and the bare-king gate. One thread is unchanged on purpose: enabling the bare-king skip of late-move pruning and LMR for one worker moved depth-13 nodes to 862954 net on and 907307 net off, against pins 862329 and 907205. Threads 2 missed 57 of 400 KRK mates before the gate and 0 of 400 after it, in their log. One thread can still miss after an earlier search. They left that unfixed. The stop-flag window in `Searcher::search` is also still unfixed. They say no test fails for it yet.

## NNUE

Full reads: the seven files under `h512/results/cloud_20261113/` on their tip. Blobs:

| Blob | File |
|---|---|
| `c72cc8e525ebae1857fc41a98649ef93999b8b81` | `RESUME.md` |
| `628e9ccc137383336b7b746ad30398e75a0b2201` | `REFRESH_BIAS.md` |
| `9cf62f07c36223ad25255739d318b3fe3b319b71` | `VNNI.md` |
| `68a7879c9c290a175aa01281a9c3de3a3a597c61` | `APPLY_BOTH.md` |
| `a09b31143d16f71e8865a3d7d2ba877f0b0bac35` | `SCORER_PARITY.md` |
| `8e472fee96a5a04b50cafa215312a6d665ec321d` | `SANITIZERS.md` |
| `6aa4e28dbd1320902d0c385f91c0fd7905863e74` | `PIECE_COUNT.md` |

Rebuilding a stale v3 cache entry from the bias is bit-exact on their synthetic nets. Cold-refresh times fell. The depth-16 search bench stayed inside the baseline's own spread, which was already about 4 percent. A fused both-perspective update was bit-exact and slower than that spread, so they removed it. `vpdpwssd` is used only when the compiler defines `__AVX512VNNI__`. The portable v4 build does not. On their Xeon the output-sum microbench was faster; the depth-16 bench gap was smaller than an earlier gap between two madd runs. Clang 18 rewrites one of the two unrolled steps back to `vpmaddwd`. No candidate-3 net was in their checkout. No Elo claim.

The piece-count lookup was checked for all 256 byte values and left unchanged. They say not to rebuild the frozen shards.

## Search

Full reads: `search_strength/CHECKPOINT.md` blob `59cc26b64e06f179a58e5b164f34904fa0d8602d` and `CHECKPOINT-2.md` blob `11ed5faf66c2a027e4f17e5aa8504b76500ed58c`.

`FORGE_ETC_STATS` counts and does not cut off. Pins matched. On bench positions the share of nodes under proving children was smaller than the measured lookup time at depths 16 and 20. Depth 22's point estimate went the other way by about 2 points, and their rough interval reached under 2. A hash-move-only peek stays under 1 percent of nodes and inside its own noise. They say not to write a cutoff spec from these benches. Gate games, which the dossier names as the decision set, are not in the checkout.

`FORGE_CONT4_READ` changes the tree, including best moves, and stays default off. One position, W1, played `a1b1` at depths 16, 22, and 28 with the switch on. The plain portable binary played `a1b2` at 16 and `a1b1` at 22 and 28. That is one position, not a match.

## What they should not repeat

The ETC counting run they asked the dossier for has now been done, on a portable build, and their own note says it does not justify a cutoff. A second microbench of the fused update, or of VNNI on this same VM, is the measurement they already marked as inside noise. The 64-slot buffer does not need a third independent patch: buffix and their branch already size it to 256. The lock and the Fable tip still contain the 64-slot write, so a later lock candidate still has to take one of those fixes. Taking it is a lock change and is not done by this index.
