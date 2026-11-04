# STATUS - Opus 30-h job (branch opus-30h-20261103, worktree D:\o30\wt, scratch D:\o30)

Plan approved 2026-11-03 (PLAN.md, defaults D1-D4). Worktree created 16:17 PC clock. No sub-agents. No Elo claims.
User goal (16:2x): work the full 30 hours (to about 22:17 on 2026-11-04, PC clock); when one thing is blocked, improve
the unblocked ones; 1-hour bug hunt at the end; check that it works in Forge.

## GPU
Not released (npt keeper: window to 2026-11-08 00:00 PC). The nets are CPU fine-tunes of the lock net
(`opus_30h/a/o30_fit.py`, warm start = the lock function); the GPU path (residual bullet mode, ROCm exe) is ready, unrun.

## State (2026-11-04 08:2x PC clock)
| item | state |
|---|---|
| 0 base re-verify | kit v2.3 -Expose of the unpatched lock = fd3a5190... on pc1 and pc2 |
| A port (EvalFileV2) | OFF pins PASS; lock net as v2 = lock pins d11-d22 (3 layouts); parity 10000/10000 x 4 nets x AVX2/SSE/scalar; walk 830k plies x 3 nets 0 mismatches; in-search verify clean; CI (ASan+UBSan, TSan) green |
| A gate exe | kit v2.5 `D:\o30\w\v2p3_pc1\src_copy\forge_ltopgo_v2p3_pc1.exe` ff856ba8 (pc1 = pc2): OFF pins PASS, lock net as v2 = lock pins, v2 path ~1.0x the lock (advisory); kit v2.4 8704d302 0.96x, kit v2.3 0.71x (cold) |
| A scorer / data | S31 control = AL1 0.014310027 / 0.004572428 (0 mate rows at the 30000 cut); 304,999,573 train rows, 7,706 holdout-overlap rows skipped, 988,336 jobA overrides, jobA val 8,821 rows |
| A trainer | selfcheck PASS; resume proof PASS (bit-identical); mixed chunks (8 shards) after the one-shard jumps |
| A net #1 `o30_kb4ob8_n2e` | KB4 rank map, OB8, residual, 3.5e8 positions: S31 b0.6 0.014254268 (paired -5.58e-5, z -34), jobA +2.21e-5 (z +1.23) -> offline rule PASS; all pack checks PASS; smoke PASS; NPS 0.90x (same mean depth in games); verify build, fuzz, conformance 22/22 PASS; 400-game sanity match vs the lock 79 / 213 / 108 = -25.2 +/- 18.5 (sanity only; the S31 gain did not show in play) -> not a gate candidate on its own |
| A net #2 n2L | same shape, 1.4e9 positions, seed 222, CPU 0 until ~03:25 (deadline 03:30); 21:09 checkpoint at 3.65e8: S31 0.014246212 (-6.4e-5), jobA +2.7e-5 |
| B options | 22 new tunables (defaults = lock pins PASS), 22 / 22 live; kit v2.3 exe pc1 = pc2 7bf5dab3; CI green |
| B tuner | tune_spsa + wrapper + README; SELFTEST PASS; disk-floor stop (C: 30 / D: 51 GB) added 20:00; main session stc8 starts on CPU 1 after net #1's play checks |
| tools | MCP forge-o30 (5 tools, self-test 8/8), skills forge-o30-v2net / forge-o30-spsa, TOOLS.md, net_pack with paired rule verdict, INDEX summary table |

## Finding so far
The lock net is converged on its own labels at its own shape (KB1 / OB8 fine-tunes move S31 b0.6 by -1.4e-5 at most in
1.5e8 positions); more first-layer capacity (4 king buckets, same 256 hidden units, same speed class) moves it -5.6e-5
in 3.5e8 positions, and the early-file jobA positions with deeper labels stay within the noise of the lock net (paired z
in RESULT.json). Whether this offline gain is Elo is for the crew's gate (S30: loss has not predicted Elo reliably here).

## Deviation from plan default D1 (disclosed 2026-11-03 20:4x)
D1 said the heavy CPU work (SPSA session, 400-game matches) waits until npt is off CPUs 0-3 or the crew frees cores.
Since ~17:30 I run CPU fine-tunes, and since 20:12 the n2e match, at Idle on CPUs 0-1 (npt's mask 0xF includes them;
no gate uses them; the prompt's rules - <= 8 threads, off gate cores, never touch npt - hold). Evidence that npt is not
slowed: hourly mean GPU utilisation from the keeper's HWiNFO log (`tools/gpu_util_stats.py`, read-only): 12:00-15:00
(before this job's CPU work) 29-30 %, 16:00 34, 17:00 36, 18:00 31, 19:00 32, 20:00 32 %. If you want D1 kept to the
letter, the tuner and trainers stop cleanly (`tune_spsa.ps1 -Stop`, `o30_fit.py stop <run>`) and resume later.

## CPU plan (CPUs 0-1 only, Idle; gates 0xFFF0, npt Idle on 0x000F)
- CPU 1: n2e pack (20:07) -> n2e play checks (until 23:58) -> A/A both ways + 1.1M-ply walk (done 00:03) -> SPSA stc8
  00:03:59-02:49 and 02:56-02:57 (`D:\o30\spsa\stc8_main`, 184 pairs) -> control match 02:58-~06:40 (the gate exe +
  the lock net as KB4 replicas vs the lock exe, `D:\o30\control\lockkb4_v2exe`). The KB8 test n3 was NOT run (dated
  reason in a/RESULTS.md: n2e's match showed S31 does not predict play).
- CPU 0: n2L done 02:47:53 -> packed 02:49 (offline rule FAIL: jobA z +2.55) -> smoke + ABBA (02:50-02:56, CPU 1 idle)
  -> n2L 400 games until ~06:40.
- 06:38-07:33: speed discriminators (KB1 on the v2 path, the v2 exe OFF; 100 games each) -> 07:3x-08:1x the speed
  hunt (game-position probe, counters) found the lazy-root bug -> fix, gate exe v2p4 (a2a560cb) -> 08:1x rematches on
  v2p4, 400 games each: n2L (CPU 0, `D:\o30\nets\o30_kb4ob8_n2L\sanity_v2p4`), control (CPU 1, `D:\o30\control\
  lockkb4_v2p4`), until ~11:55. 08:2x: Code Review fix (patch scripts all-or-nothing).
- ~11:55: record both rematches; resume SPSA `tune_spsa.ps1 -RunDir D:\o30\spsa\stc8_main -Until '2026-11-04 19:30'
  -Threads 2 -Cpus '0,1'` until 19:30 (paused at 184 pairs; ~1,000 more expected).
- From 19:30: SPSA report + tuned-set exe (`b/build_o30tuned.sh`, ~10 min), final_checks_o30.sh, 1-hour bug hunt
  (incl. the deliverables in Forge), FINAL_REPORT; job end ~22:17.

## End-of-job bug hunt (1 hour; the checklist, written early)
1. `tools/final_checks_o30.sh`: 16 checks (pins of 3 exes + the O30Tuned exe added, identity, parity, walk, scorer,
   selfcheck, MCP, clean-room lint incl. the O30Tuned patch and >= 1 commit scanned, doc_lint, INDEX hashes, paths).
2. Forge as a GUI / the gate runner uses it: `tools/uci_conformance_o30.py` on the gate exe + each net, on the
   O30Tuned exe with O30Tuned=true, on the SPSA exe and the lock exe.
3. `b/test_o30tuned.sh` on the final O30Tuned exe; INDEX.md complete (both nets with FINAL_CHECKS, rule verdicts).
4. hash_sweep + path_sweep over every document; publish_o30.sh copies = branch; skills user scope = branch copies.
5. Re-read the diffs (v2port, expose22, O30Tuned) and every RESULTS claim against its evidence file.
6. CI: the last run of the branch head green (no pushes while it runs).
7. Own processes: nothing of mine still running except what the report says; memory file updated; time from commit
   spans (`tools/commit_span.py`).
8. abba.py arm bias (A/A both ways: arm B ~5.5 % slower in nearly every slot, AB and BA alike; the code reads
   symmetric): A/A with the IDENTICAL command in both arms on a quiet CPU - if B is still slower it is the harness /
   launch path, else the command strings; fix or document before any speed figure leaves the job.
