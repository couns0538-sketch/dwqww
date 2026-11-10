# opus_smp_layout — SCALING_PLAN (PREPARED-ONLY, for QA's quiet allocation; NOT run by this job)

This job ran only on CPUs 12-15: two physical cores with their SMT siblings, on a shared PC. So Threads 4 there is SMT-loaded, and Threads 8 is oversubscribed. **Nothing measured on those CPUs is scaling evidence.** This plan is for QA, who owns quiet timing and core allocation. It does not seize eight cores and does not interrupt any timing.

## Question
Does the lockless TT (`TtLockless=true`) and the `nodes_` line change speed up multi-threaded search versus the striped-lock TT, at equal search behaviour? At Threads 1 both modes are node-identical (BENCH.md). At Threads ≥ 2, searches are nondeterministic, so the metrics are speed metrics only.

## Exes (sha256)
| name | exe | options |
|---|---|---|
| P | trial_w6 `forge_ltopgo_x_al1s198_trial_w6.exe` (4181a589…) | none |
| G-off | gate exe of the candidate `a675c04`, sha256 `a4b57032294d9d9efe2742408bb0a56da970cd1146f15c360a1fe99aada2c54b` (kit f1c/f1d; on this PC `D:\forge_jobs_20261107\opus2\out\exe\forge_smpgate_a4b57032.exe`). It supersedes `541e8b3d…` (`0599271`) | `TtLockless=false` (layout change only) |
| G-on | same gate exe | `TtLockless=true` |

## Allocation (QA)
- One logical CPU per physical core, SMT siblings idle. On the 9850X3D that is mask 0x5555 (CPUs 0,2,4,…,14) for Threads 8, 0x0055 for Threads 4, 0x0005 for Threads 2, 0x0001 for Threads 1.
- Quiet PC (no gates, trainer or self-play on the chosen cores and their siblings), High or Normal priority as QA's protocol prescribes.

## Protocol
1. Positions: 32 FENs from `opus_speed/data/fens_12k_v2.txt` (lines 501-532), OwnBook false, Hash 256.
2. Per thread count T in {1, 2, 4, 8}, per exe: a fresh process, `setoption Threads T`, then per FEN: `ucinewgame`, `position`, `go movetime 5000`. Record nodes and time from the last info line, and the depth reached.
3. Order: palindromic blocks P, G-off, G-on, G-on, G-off, P (7 blocks), plus 3 A/A blocks of P against a byte copy (per-file placement noise).
4. Metrics, per T:
   - wall nps ratio G-on/P and G-off/P (median, bootstrap 95 % lower bound);
   - time-to-depth ratio on a fixed depth (a second pass with `go depth D`, with D chosen so that P takes about 5 s at that T);
   - for G-on, `go nodes 2000000` at T = 8. This tests node-limited stopping: `nodes_` is read by every worker on every node under `go nodes`.
5. Decision rules are QA's own (WIN = 95 % lower bound > 1.000 and median ≥ 1.010, on wall nps). No Elo claim: an SPRT is QA's call.

## Commands (prepared; not run here)
```
# per T and mask, from Git Bash; nps_smoke.ps1 needs only its config file and an allowed mask
# (this job's copy only allows 0xF000, so QA would set $script:OspdAllowedMask for its own allocation first)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File opus_smp_layout/tools/nps_smoke.ps1 -ConfigFile <P/G-off/G-on tsv> \
  -OutDir <qa dir> -Tag T8_movetime -Threads 8 -Mode movetime -MoveTime 5000 -Rounds 7 -FenCount 32 -Mask 0x5555
```
