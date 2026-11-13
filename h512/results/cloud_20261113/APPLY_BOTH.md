# Fused both-perspective update: measured, not kept

The refresh-from-bias change was already in the tree (`b69867892cba62a7c83f3661a86e5fd22efba015`). On top of it, `replay_ply` was changed so a move that leaves both king keys alone updates both perspectives in one AVX-512 loop (quiet sub/add, capture sub/sub/add, castle sub/add/sub/add). The unit walk still matched (96009 checks, 0 failures, same 100000-ply totals). The H512 1000000-ply checksum stayed `-679772115` and the cold-refresh checksum stayed `-4064000000`.

Pinned `taskset -c 1` walk, `eval_only_ns`, same synthetic H512 net as `REFRESH_BIAS.md`:

| Run | refresh-only | fused |
|---:|---:|---:|
| 1 | 328.810 | 313.303 |
| 2 | 295.171 | 281.695 |
| 3 | 302.044 | 300.404 |

The refresh-only arm already moves by about 30 ns between runs. The fused arm is lower in each pair, by 15.5, 13.5 and 1.6 ns. That is smaller than the run spread, so the extra kernel was removed rather than committed. A later attempt should not treat this table as a speedup.

Binaries for that comparison stayed in `/tmp/forge-nnue-build` (`nnue_v3_speed.refresh` versus `nnue_v3_speed`) and were not committed. The working tree was returned to the refresh-only commit before this note.
