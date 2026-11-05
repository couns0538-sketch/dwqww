---
name: forge-o30-v2net
description: Forge v2 nets (FORGENN2) on the lock engine - the EvalFileV2 port (opus_30h/a/v2port.patch on the lock d4f4312), its proofs (lock net as v2 = lock pins, parity 10000/10000 x AVX2/SSE/scalar vs an own float32 reference, accumulator walk, in-search verify build), the holdout scorer that reproduces the crew's S31 numbers, the training-data audit, the CPU fine-tune trainer warm-started from the lock net, net_pack.sh (paired holdout diff vs the lock net + the offline rule verdict), net_final_checks.sh (smoke, NPS ABBA, sanity match), INDEX.md, and the kit choice (v2.5 workload v2n; v2.3 leaves the v2 path cold). Use for any v2 / EvalFileV2 net, a new trained net to check or package, a holdout-loss question, or a speed question about an option-only code path in a kit exe.
---

# Forge v2 nets on the lock (Opus 30-h job, branch opus-30h-20261103)

Tools: `D:\o30\wt\opus_30h\a\` (branch copy `opus_30h/a/`), scratch `D:\o30`. Rules first: forge-pc-rules (latest
round), own work at Idle on CPUs 0-1, D: >= 50 GB / C: >= 30 GB, never delete / kill, no sub-agents.

## Facts
- The lock (FD3A5190, source d4f4312) has no v2 code; `v2port.patch` adds it: header-only `include/forge/nnue_v2.hpp`
  (FORGENN2 loader, king buckets 1-32 + mirror, output buckets 1-16, residual flag; feature set 0 only), loader at the
  end of `src/nnue.cpp`, `Worker::static_evaluate_v2` in `src/search.cpp` (lazy accumulators reuse
  `SearchStack::accumulator`; king-bucket changes refresh through a per-worker cache), UCI string `EvalFileV2`
  (empty = off; a bad file prints `info string ERROR EvalFileV2 ...` and leaves no v2 net active).
- v2 hidden size = the engine's (256). Weights int16 / 4096 like the lock net: every accumulator value is exact, so
  incremental = cached = full refresh bit for bit, and the output kernel has the lock's lane order: the lock net written
  as v2 (`o30_v2net.py from-lock`, any king map without mirror / any output-bucket count) gives the lock's bench
  pins d11-d22 exactly. That is the port's identity test; a random net must be LIVE.
- Residual (flag bit 0) = the lock's HCE + the net, like the compiled-in net. FHCE files = the lock's
  `Evaluator::evaluate_uncached` on every holdout row (checked on 1,024,286 rows).
- Kit: v2.3 profiles the OFF path only -> the v2 path is cold-optimised (0.71x the lock's speed on the same tree).
  Kit v2.4 `-PartialTraining` (`tools/kit24_build_o30.sh`): 0.959x. Kit v2.5 (`tools/kit25_build_o30.sh`, working copy
  `D:\o30\kit25`, = v2.4 + workload v2n that also benches the lock net written as v2) -> the gate exe for v2 nets is
  `D:\o30\w\v2p4_pc1\src_copy\forge_ltopgo_v2p4_pc1.exe` a2a560cb (pc1 = pc2; patch md5 926ada2c WITH the root fix).
  NOT ff856ba8 (v2p3): it lacks the root fix.
- ROOT REFRESH (bug found 2026-11-04): the v2 path must build the root accumulator at search start like the compiled-in
  net. Left lazy, in GAMES (hash kept between moves, the root's evaluation from the hash) 19 % of evaluations had no
  valid ancestor and rebuilt from the cache: ~8 % slower, ~0.15 ply shallower, an identical-evaluation control lost
  -32 +/- 18.5. The bench clears the hash per position and never showed it. Time any eval path with
  `a/depth_probe_o30.py` (game positions, long-lived process, nodes-per-second ratio with a CI) and count work with
  `a/o30_v2stats.py` + `a/stats_run_o30.py`; read every match against an identical-evaluation control (the lock net
  written as v2 on the same exe), not only against 0.

## Checks (in this order)
1. `pin_check.ps1 -Exe X -Full` (OFF pins); lock net as v2 + `-Expect` the lock pins (PASS); random net ON = LIVE;
   missing file = FAIL with the ERROR line.
2. `bash build_harness_o30.sh <port repo> <new dir>`; `bash parity_o30.sh <new dir> C:\o13\p4\fens10k.txt <harness>
   <nets...>` -> PARITY PASS + planted bug caught; `v2_eval_avx2.exe --walk <net> <seed> 3000 300` -> 0 mismatches
   (use a random KB4 mirrored net: replicated weights hide king-bucket bugs).
3. Verify build: `plain_build_o30.sh <repo> <dir> -DFORGE_NNUE_V2_VERIFY=1` + bench with a random KB4m net: no abort.
4. Holdout: `D:\o30\tools_bin\o30_score_v2.exe --net <file> --pos <S31 .pos> --hce <S31 .hce>`: lock as v2 = b0.6
   0.014310027 / b1.0 0.004572428 (the crew's AL1 numbers); jobA val (`D:\o30\data\jobA_val.*`, 20k-node labels):
   lock 0.013272058.
5. A trained net: `bash net_pack.sh <name> <net> <kit exe> <harness dir>` -> D:\o30\nets\<name>\RESULT.json (copy,
   sha256 / md5, parity x 3 + planted bug, S31 + jobA scores with per-row dumps, PAIRED diff / SE / z vs the lock net's
   dumps `D:\o30\dumps\{s16,jobA}_lock.f64` via `o30_paired.py`, `offline_rule` verdict, OFF pins -Full, ON bench twice).
   Refuses an existing folder (no deletes: a failed try burns the name - test new packer code on old dumps first).
   Then `net_training_json.py <run> <net> <folder>\TRAINING.json`.
6. Play checks: `bash net_final_checks.sh <name> <exe> [games=400] [conc=2] [cpus=0,1]` -> smoke 300 s (Threads 2 on the
   CPU list), NPS ABBA 6 pairs on the FIRST listed CPU, sanity match vs the lock 10+0.1 + gate_summary ->
   FINAL_CHECKS.json (refuses an existing one). Keep it off the CPUs of a running SPSA session (the tuner treats any
   other fastchess on its CPUs as a gate and waits). Sanity only, never an Elo claim.
7. `make_net_index.py` -> `D:\o30\nets\INDEX.md` (summary table: paired diffs, z, rule verdict, sanity line).
Offline rule (written before the results): S31 b0.6 >= 2e-5 below the lock net AND paired jobA z <= +2 (paired SE:
S31 ~1.6e-6, jobA ~1.8e-5; seed spread of final b0.6 ~7e-6). A failing net is still packaged and marked.

## Training on the CPU (no GPU window)
- Data: `o30_data.py --out <new dir>`: train = FPOS / FHCE shards 001-039 minus 013 / 014 = the npt binpack's
  304,999,573 rows; skip lists (holdout-overlap board+stm keys 7,706 rows, jobA val, mates), jobA 20k-node overrides.
- `o30_fit.py selfcheck` must reproduce the scorer before training. `fit_bg.sh <name> <mask> --init lock ...`;
  ~50-60k positions/s per CPU (1 torch thread). Checkpoints every --save-minutes, last.pt / best.pt / best.nnue2,
  val.csv per checkpoint; `o30_fit.py stop <run>` (named event) saves and exits; `--resume` continues the same stream.
- Measured: the lock net is converged on its data. KB1 / OB8 fine-tune, 30M positions: lr 5e-6 -> S31 b0.6 -0.8e-6,
  lr 2e-5 -> -0.4e-6 (seed noise of b0.6 ~7e-6; lr 1e-4 made it worse first). Gains need capacity (king buckets) or
  better labels, not more steps.
- Use `--mix 8` (8 shards per 1M-row chunk): one-shard chunks pulled the output layer toward one self-play file and made
  the jobA loss jump +1.5e-4 between checkpoints.
- KB4 (rank map: king rank 1 / 2 / 3-4 / 5-8, unmirrored = exact warm start) + OB8, lr 2e-5, output layer x2, cosine to
  1e-7: 3.5e8 positions (~2 h 20 min on one CPU) -> S31 b0.6 -5.58e-5 (paired z -34), jobA +2.2e-5 (z +1.23) = rule PASS
  (net `D:\o30\nets\o30_kb4ob8_n2e`, sha256 998db5e9...). KB1 / OB8 at the same length: -1.4e-5 (fails the rule).

## Training on the GPU (window from the owner, 2026-11-04; record in D:\o30\WINDOW.md first)
- Trainer: ROCm build of `a/forge_v2_bullet_o30` (`build_bullet_o30.bat rocm <tag>`; BULLET_TARGET=<dir> builds into
  another target dir - a running exe cannot be relinked). Run only through `a/gpu_run_o30.bat <run> <kb map> <mirror>
  [hidden sb bpsb threads seed lr wdl mix]`: o30_gpu_guard.py starts it at Idle on CPUs 4-5, suspends it on the PC's
  GPU limits (hot spot 76 / memory junction 86, resume 72 / 83, emergency 78 / 88; fail closed on a stale HWiNFO feed)
  and while any npt-like python trainer runs (F:\forge_nnue_train\tools\gpu_guard.ps1 only watches npt itself).
- Before the first GPU minute: no npt python process, GPU utilisation near zero (HWiNFO CSV), never touch npt.
- Speed: 2.8-3.0M positions/s at H256 (KB1 and KB4), batch 16384, 2 loader threads; 1024 x 16384 per superbatch =
  ~5.9 s; 700 superbatches = 11.7G positions = ~70 min; 8 checkpoints per run.
- Reader contract: bullet's read_chunks callback returns TRUE to STOP. An inverted test ran one batch and died with
  "Data loader ended before all scheduled batches completed" (fixed 2026-11-04; the CPU mock build cannot show it).
- Every checkpoint: `a/gpu_ckpt_watch.sh <run> <kb map>` (Idle, CPU 2) exports (export_v2r.py), scores S31 + jobA and
  pairs vs the lock -> D:\o30\gpu\<run>_scores.tsv.
- Warm start: `import_v2r.py <net.nnue2> <dir> --kb-map rank4` (lock-as-KB4 = D:\o30\nets\lockv2\lock_kbrank4_ob8.nnue2;
  `o30_v2net.py from-lock <lock nnue_weights.inc> <out> --kb-map rank4x2 --ob 8` for KB8), then run with
  O30_INIT_DIR=<dir> O30_CLIP=7.99 O30_DECAY=0 (bullet's AdamW clips weights to +-1.98 by default - the lock net reaches
  3.47 - and its decay 0.01 would shrink a warm start ~7 % over 700k steps). Proven: import -> GPU load -> lr-0
  superbatch -> save -> export = the input net byte for byte.
- From scratch (KB4, lr 1e-3): checkpoint at 1.46G positions S31 +7.7e-4 vs the lock (worse) - from-scratch nets must
  get through the whole cosine schedule before they can be judged.
- Window 2 (2026-11-04 13:27-19:06) lessons: warm-start recipe lr 2e-5, 200 superbatches (~13-15 min at 3-4.4M pos/s)
  is as good as 700 (lr 3e-5 is worse). More king buckets help offline: KB4 -1.41e-4, KB8 -1.65e-4, KB16 -1.80e-4,
  KB32 -1.80e-4 (S31 paired vs the lock, same recipe; seed noise ~4e-6) - but cost engine speed (identity nets, same
  trees, 3-4 runs each, single runs scatter +-1-2 %: KB8 ~0.988x, KB16 ~0.969x, KB32 ~0.942x the nps of KB4;
  layout_*_vs_kb4*.txt). Maps rank4x4 (16) / rank4x8 (32) exist in the
  trainer and the tools; the engine reads the 64-entry map from the file (no rebuild); prove a new layout with
  `pin_check -Options EvalFileV2=<lock written in that layout>` (= lock pins) and net_pack's parity.
- WEIGHT SOUPS gave the best offline numbers (best of 37 soups scored on 2026-11-04, selection-biased: chosen and judged on the same S31 /
  jobA sets; UNPROVEN in play, needs an SPRT gate): nets warm-started from the same lock net, rewritten exactly to one layout
  (`a/o30_expand_kb.py --from rank4|rank4x2|rank4x4 --to rank4x4|rank4x8`) and averaged (`a/o30_soup.py`, scored like
  a checkpoint by `a/soup_score.sh <name> <kb map> <quantised.bin>...`, table `a/soup_table.py`). Independent runs of
  different length / layout make the gain (r3+r5+r7+r8 as KB32: S31 -2.25e-4, jobA z -2.70; best single -1.80e-4);
  checkpoints of one run and seeds of one recipe add little; a weak-jobA member (KB4 run 2) hurts the soup's jobA.
- Do not fine-tune a soup: 100 superbatches at lr 5e-6 from the soup (fresh AdamW) made the KB8 soup Y8 worse (paired
  S31 z +10.7, jobA z +2.4) and left the KB32 soup Z32 level (a/logs/gpu/w3_r21_vs_Y8.txt, w3_r22_vs_Z32.txt).
- Unattended GPU queue: `a/queue_runner2.sh <guard log to wait for> [cutoff]` runs C:\o30g\gpu\plan2.txt line by line
  (edit the PLAN between runs, never a running .sh / .bat; a refused start is retried after its <run>.out /
  .guard.log / .runner.txt move aside - the bat refuses existing ones with exit 4 -, marked done only after the
  trainer started); run outputs on C:\o30g\gpu via a/gpu_run_o30c.bat when D: is near its floor; the watcher
  `a/gpu_ckpt_watch2.sh` needs WATCH_MASK and is bounded; net_pack.sh / final_checks_o30.sh / soup_score.sh need O30_MASK.
- Play (sanity, 10+0.1 vs the lock exe on v2p4, control = the same exe playing the lock net = 47.0 %): run 5 (KB8)
  52.6 % / 400, soupC (KB32 soup) 52.1 % / 400, U8 (KB8 soup) 51.0 % / 200, run 7 (KB16) 50.6 % / 400, run 2 (KB4)
  49.6 % / 400, P16 (KB16 soup) 47.75 % / 200 - all within noise; KB16 reads lowest in play. End to end the gate exe
  with a KB8 soup runs at 0.893x and with a KB32 soup at 0.849x the lock exe's nps (different trees): closing the v2
  path's speed gap is worth more than another 1e-5 of S31. Candidates + gate lines: FINAL_REPORT section 4.
- Forge checks for any new net before handing it on: `smoke2m.py <v2 exe> --line EvalFileV2=<net> --seconds 300
  --threads 2 --hash 16 --mask <cpu> --idle` and `uci_conformance_o30.py <v2 exe> --opt EvalFileV2=<net>
  --expect-info "EvalFileV2 loaded"` (examples in a/cpu6_final.sh).

## Pitfalls (all hit on 2026-11-03)
- Bash-tool commands collapse `\\` before `$var` -> a literal `$var` (a run dir named `runs$1`, a net path the engine
  could not open). Use forward slashes or `cygpath -w`.
- Never cut pin_check output with `head` (the FAIL / ERROR line is the first or the last line).
- `export_src.sh` copies the WORKING tree per kit side: do not edit the scratch repo while a kit build runs (pc2 is
  exported after pc1 finishes).
- JSON from C++ tools: escape the backslashes of Windows paths (the first scorer printed invalid JSON).
