# STATUS - Opus 30-h job (branch opus-30h-20261103, worktree D:\o30\wt, scratch D:\o30)

Plan approved 2026-11-03 (PLAN.md, defaults D1-D4). Worktree created 16:17 PC clock. No sub-agents. No Elo claims.
User goal (16:2x): work the full 30 hours (to about 22:17 on 2026-11-04, PC clock); when one thing is blocked, improve
the unblocked ones; 1-hour bug hunt at the end; check that it works in Forge.

## GPU
Released by Couns 2026-11-04 ~10:06 PC clock for 4 hours + 6 CPU cores (quote: D:\o30\WINDOW.md, copy
a/logs/gpu/WINDOW.md). Deviation from plan default D1 (written release from Engine QA): the owner's own release is
used. The npt run s47 had already ended (no npt process, GPU 1-4 %, keeper STATUS stale since 09:48); nothing of npt
was touched. Own guard a/o30_gpu_guard.py (thermal limits, yields to npt-like trainers). CPUs: 0-1 rematches, 3 Astra
scan, 4-5 GPU trainer, 2 export / scoring.
- 10:13 smoke01: the reader stopped after one chunk (inverted stop flag, fixed); 10:15 smoke02 PASS (parity 10000/10000
  x 3, S31 consistent with the trainer loss); 2.8-3.0M positions/s.
- 10:17 run 1: KB4 rank map, from scratch, 11.7G positions (ends ~11:26); checkpoints scored by a/gpu_ckpt_watch.sh.
- 10:22 warm start proven byte-identical (import_v2r.py -> GPU load -> save -> export = lock-as-KB4 net). Re-proven 13:35-13:36 on the
  current builds with the decay line and the exe md5 in each log (CR item 11): logs/gpu/warmproof02_rocm2.out (exe of runs 2-6),
  warmproof03_rocm3.out (item-10 build), warmproof04_kb16.out (16-bucket build); each ends "COMPARE: byte-identical -> PASS".
- Next: run 2 = warm start from the lock net (KB4), lr 2e-5 cosine, ~11.7G positions; run 3 by the scores (KB8 warm
  start ready: D:\o30\gpu\init_lockkb8). Freed CPUs after ~12:00 go to sanity matches of the GPU nets.

- 11:5x-13:35 runs 2-6 (all warm starts from the lock net, exe D:\o30\target_rocm2 md5 04b6944a): finals in a/RESULTS.md;
  run 6 (KB8, lr 3e-5, 800 superbatches) ended 13:35:14 at S31 -1.33e-4 / jobA -8.9e-6 (rule PASS, weaker than run 5).

## GPU window 2 (owner's extra 5 h GPU + 5 h CPU, received ~13:18, recorded 13:27; read as ~14:06-19:06)
Quote and reading in D:\o30\WINDOW.md (copy a/logs/gpu/WINDOW.md). CPUs: 3-5 GPU trainer (0x38) + checkpoint scoring,
2 run-5 sanity match (since 13:26), 6 run-2 sanity match, 0-1 Item B kit build (agent, from 13:45), then sanity
matches of the new nets. GPU run outputs from run 8 on are on C:\o30g\gpu (D: at 53 GB, floor 50; a/gpu_run_o30c.bat).
- 13:28-13:45 CR items 9-13 of the owner's fix list (commits 8b57f4a8, 24d98b82, f9136f2f, 16e84bc9, 345cf411):
  trainer refuses a warm start without O30_CLIP + O30_DECAY; guard fails closed with ABORT + --resume-pid (dummy-child
  tests); warm proofs 02-04 byte-identical on the current builds; watcher bounded; two bug-hunt logs labelled.
- 13:31 16 / 32 king-bucket layouts (rank4x4, rank4x8) in the trainer and the Python tools (b74033b4); Rust = Python
  features on 3,000 rows; the engine reads the map from the file (no engine change).
- 13:36 run 7: KB16 rank4x4, run 5's recipe (200 superbatches, lr 2e-5), exe D:\o30\target_rocm4 (md5 1a180f7b).
  At 150 superbatches S31 -1.74e-4 (z -36.7), jobA -1.01e-4 (z -1.98): ahead of run 5 (KB8) at every checkpoint.
- run 8 queued (a/queue_w2b.sh): KB32 rank4x8 warm proof, then the same recipe; watcher on C:\o30g\gpu.
- Play checks (agent, CPU 0, 13:05-13:39): nets of runs 2 and 3 work in Forge - smoke 300 s 0 illegal / 0 crashes /
  0 time losses, UCI conformance 22/22, speed vs their lock-as-KB controls within noise (draft D:\o30\tmp\forge_checks_draft.md).
- Sanity (400 games 10+0.1 vs the lock exe, sanity only, no Elo claim): run 2 at 160 games 50.31 %; run 5 started
  13:26 on CPU 2; run 3's queued start on CPU 5 was refused on purpose (placeholder note in its sanity folder).
- 13:50-14:05 run 8 (KB32 rank4x8, same recipe): final S31 -1.80e-4 / jobA -5.4e-5 (= run 7 on S31, weaker on jobA);
  first live run under the new guard (start line with pid + create time, end exit 0, 0 poll errors).
- 13:55 engine identity of the new layouts: the lock net written as KB16 / KB32 gives the lock pins in v2p4.
- 13:56 run 7 packed (D:\o30\nets\o30_gpu_kb16short_r7, all checks incl. parity at KB16); sanity on CPU 0 from 13:57.
- 14:05 WEIGHT SOUPS: nets trained from the same lock warm start, rewritten exactly to one layout
  (a/o30_expand_kb.py) and averaged (a/o30_soup.py, a/soup_score.sh): best of the soups scored (14 by 14:36, 33 by 19:00, 37 by 21:19), selection-biased
  (chosen and judged on the same S31 / jobA sets); UNPROVEN in play, needs an SPRT gate. Runs 3+5+7+8 as
  KB32 S31 -2.25e-4 (z -50.2) / jobA -1.34e-4 (z -2.70); runs 3+5+7 as KB16 -2.09e-4 / -1.30e-4 (z -2.54). Run 2 (KB4)
  hurts jobA in a soup. The KB32 soup is packed (D:\o30\nets\o30_gpu_soupC_r3r5r7r8, sha256 0dddfdc9, all checks,
  parity 10000/10000 x 3) and plays its sanity match on CPU 1 from 14:12.
- 14:12 layout speed (identity nets, same trees, gate exe; 3-4 runs each by 18:21, single runs scatter +-1-2 %):
  nps vs KB4 KB8 mean 0.988 (0.983-0.997), KB16 mean 0.969 (0.956-0.985), KB32 mean 0.942 (0.940-0.944) ->
  the GPU plan (C:\o30g\gpu\plan.txt, a/queue_runner.sh, cutoff 18:40) now makes KB16 and KB8 soup members only.
- 14:35-15:22 independent review of the window-2 code (12 findings) and its fixes (runner2 / watch2 / guard; W2-03's
  second half dropped: psutil reads a suspended process as running, re-suspending stacked suspend counts on a dummy);
  15:19 runner2 took over between runs.
- 15:19-18:59 runs 12-20 (KB8 / KB16, 100-600 superbatches, lr 1e-5 / 1.5e-5 / 2e-5 / 3e-5); the 600-superbatch KB16 run
  is worse alone, the 600-superbatch KB8 run has the best single-net jobA (-1.46e-4). Soups packed: P16, Z32, V16, U8, Y8.
- 16:07-18:11 second owner list: items 1-5 here (73e4c828, 8f473e8a, 3bc5cd88, 101379e6, 6085d7b2), items 6-7 on the
  R14 branch by the agent (0e9f68e1, CI green).
- Sanity finals (vs the lock exe; control 47.0 %): r2 49.62 %, r5 52.62 %, r7 50.62 %, soupC 52.12 % (400 games each),
  U8 51.00 %, P16 47.75 % (200 each); 0 time losses / illegal moves / crashes. V16 (CPU 1, 300 games) and Y8 (CPU 0,
  400 games) play on after the window on the normal CPUs 0-1.
- 17:51-18:32 Forge smoke 300 s + UCI conformance 22/22 for Y8, U8, V16, Z32; layout speed 3-4 runs: KB8 0.988x,
  KB16 0.969x, KB32 0.942x of KB4; end to end v2p4 + Y8 0.893x and v2p4 + Z32 0.849x the lock exe's nps.
- 19:00 final offline soups (all 11 KB8 runs -1.86e-4 = the KB8 plateau); 19:01 window 2 over (GPU idle from 18:59).

## End of the job (CPUs 0-1 from 19:06; window 3 from 19:38)
- 19:08-19:31 bug hunt, part 1 (reading + stub tests while V16 / Y8 play on CPUs 0-1): seven findings BH-1..BH-7, all
  fixed or handed over, none changes a cited result (FINAL_REPORT 6.1). The one that matters for later use: a GPU run
  refused at start could never start on the retry (the bat refuses existing <run>.out / .guard.log with exit 4), also
  in the version delivered for fix list 2 item 1 - fixed in 1ab804be with a stub that does the bat's checks, and a
  correction note in CR_FIXLIST_20261104_REPORT.md. Fix list 2 report-back (items 1-7) complete in that file.
- 19:38 WINDOW 3 (owner: "another 2h 40min for cpu 0-6 and the whole gpu"; quote in WINDOW.md): ~19:38-22:18, the
  job's own end ~22:17, so runs and matches end by ~21:50. 19:41 Z32 (KB32 soup, never played) 400 games on CPUs 2-3
  and U8 200 more games (seed 31, sanity2) on CPU 4; 19:42 GPU plan 3 on CPUs 5-6 (queue_runner2.sh, RUNNER_GPU_MASK
  0x60; 2.7M positions/s with two loader CPUs): r21 / r22 = lr 5e-6 fine-tunes warm-started from the soups Y8 / Z32,
  r23-r25 = r5-recipe KB8 seeds + one KB32 run; cutoff 21:10.
- 19:55-20:08 soup fine-tunes: r21 (from Y8) ends WORSE than Y8 (paired S31 z +10.7, jobA z +2.4), r22 (from Z32)
  level with Z32 (z -1.6 / +0.7) -> no; r25 changed to a second KB32 seed. 20:30 r23 (KB8 seed of the r5 recipe)
  S31 -1.64e-4 / jobA -5.5e-5 = r5 / r10 (the recipe replicates).
- 20:28 V16 final 300 games 51.33 % (+9.3 +/- 22.0). 20:28 abba.py A/A with the identical command: B/A 1.014 (CI
  0.985-1.044) = no harness bias (BH-8: the night's 5.5 % came with two exe files). 20:29-20:33 final checks pre-run
  on CPU 1: 19 PASS, 0 FAIL. 20:33 CPU 1 plays 120 more r5 games (seed 31, to ~21:38).
- 20:53 r24 (native KB32 seed) S31 -1.83e-4 / jobA -9.4e-5; 21:17 r25 -1.85e-4 / -6.4e-5; 21:17 r27 (native KB32, 400
  superbatches) starts for the GPU's last hour (plan3c, ends ~22:05, scores in C:\o30g\gpu\r27_kb32m400_scores.tsv).
- 21:17-21:19 window-3 soups: Y8b (+r23) = Y8 (KB8 plateau); Z32b (+r24) -2.31e-4 / -1.50e-4; Z32c (+r24 +r25)
  -2.34e-4 / -1.45e-4 = the best S31 of the job (37 soups scored). 21:22 Z32c packed (all checks PASS, sha256 e4b58944),
  21:23-21:28 its Forge smoke 300 s + conformance 22/22 PASS on CPU 0.
- Sanity finals: Y8 400 g 50.75 % (21:21), U8 +200 g 51.00 % = pooled 400 g 51.00 % (21:28), Z32 400 g 49.62 % (21:31),
  r5 +120 g 47.50 % = pooled 520 g 51.44 % (21:37); 21:31 A/A on a quiet core B/A 0.9998 (BH-8 confirmed). 21:32 Z32c
  first read, 120 games on CPUs 0 / 2 / 3 / 4 (to ~21:50).
- Next: Z32c's read into the report, tables, INDEX.md, document checks, CI, publish copies; job end ~22:17.

Before the window: the nets were CPU fine-tunes of the lock net (`opus_30h/a/o30_fit.py`, warm start = the lock
function).

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
