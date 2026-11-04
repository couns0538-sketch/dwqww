# STATUS - Opus 30-h job (branch opus-30h-20261103, worktree D:\o30\wt, scratch D:\o30)

Plan approved 2026-11-03 (PLAN.md, defaults D1-D4). Worktree created 16:17 PC clock. No sub-agents. No Elo claims.
User goal (16:2x): work the full 30 hours (to about 22:17 on 2026-11-04, PC clock); when one thing is blocked, improve
the unblocked ones; 1-hour bug hunt at the end; check that it works in Forge.

## GPU
Not released (npt keeper: window to 2026-11-08 00:00 PC). The nets are CPU fine-tunes of the lock net
(`opus_30h/a/o30_fit.py`, warm start = the lock function); the GPU path (residual bullet mode, ROCm exe) is ready, unrun.

## State (2026-11-03 20:1x PC clock)
| item | state |
|---|---|
| 0 base re-verify | kit v2.3 -Expose of the unpatched lock = fd3a5190... on pc1 and pc2 |
| A port (EvalFileV2) | OFF pins PASS; lock net as v2 = lock pins d11-d22 (3 layouts); parity 10000/10000 x 4 nets x AVX2/SSE/scalar; walk 830k plies x 3 nets 0 mismatches; in-search verify clean; CI (ASan+UBSan, TSan) green |
| A gate exe | kit v2.5 `D:\o30\w\v2p3_pc1\src_copy\forge_ltopgo_v2p3_pc1.exe` ff856ba8 (pc1 = pc2): OFF pins PASS, lock net as v2 = lock pins, v2 path ~1.0x the lock (advisory); kit v2.4 8704d302 0.96x, kit v2.3 0.71x (cold) |
| A scorer / data | S31 control = AL1 0.014310027 / 0.004572428 (0 mate rows at the 30000 cut); 304,999,573 train rows, 7,706 holdout-overlap rows skipped, 988,336 jobA overrides, jobA val 8,821 rows |
| A trainer | selfcheck PASS; resume proof PASS (bit-identical); mixed chunks (8 shards) after the one-shard jumps |
| A net #1 `o30_kb4ob8_n2e` | KB4 rank map, OB8, residual, 3.5e8 positions: S31 b0.6 0.014254268 (-5.58e-5 vs the lock net), b1.0 0.004543952, jobA 0.013294160 (+2.21e-5); packing 20:07 (paired verdict in RESULT.json); play checks next on CPU 1 |
| A net #2 n2L | same shape, 1.4e9 positions, seed 222, CPU 0 until 2026-11-04 03:30 |
| B options | 22 new tunables (defaults = lock pins PASS), 22 / 22 live; kit v2.3 exe pc1 = pc2 7bf5dab3; CI green |
| B tuner | tune_spsa + wrapper + README; SELFTEST PASS; disk-floor stop (C: 30 / D: 51 GB) added 20:00; main session stc8 starts on CPU 1 after net #1's play checks |
| tools | MCP forge-o30 (5 tools, self-test 8/8), skills forge-o30-v2net / forge-o30-spsa, TOOLS.md, net_pack with paired rule verdict, INDEX summary table |

## Finding so far
The lock net is converged on its own labels at its own shape (KB1 / OB8 fine-tunes move S31 b0.6 by -1.4e-5 at most in
1.5e8 positions); more first-layer capacity (4 king buckets, same 256 hidden units, same speed class) moves it -5.6e-5
in 3.5e8 positions, and the early-file jobA positions with deeper labels stay within the noise of the lock net (paired z
in RESULT.json). Whether this offline gain is Elo is for the crew's gate (S30: loss has not predicted Elo reliably here).

## CPU plan (CPUs 0-1 only, Idle; gates 0xFFF0, npt Idle on 0x000F)
- CPU 1: n2e pack (20:07) -> n2e play checks (smoke 300 s, NPS ABBA 6 pairs, 400 games 10+0.1 vs the lock; ~4 h) ->
  SPSA stc8 (`-Cpus 1 -Threads 1`) from ~00:30.
- CPU 0: n2L until 03:30 -> pack -> smoke + ABBA (SPSA paused by its stop event for ~20 min, then resumed on CPU 1) ->
  n2L 400 games on CPU 0 (~4 h) -> SPSA on both CPUs (`-Cpus 0,1 -Threads 2`) until ~18:00.
- From ~18:00: SPSA report + tuned-set exe, final_checks_o30.sh, 1-hour bug hunt (incl. the deliverables in Forge),
  FINAL_REPORT.
