# Forge checks of the GPU-trained v2 nets - draft

Written 2026-11-04 13:39:55 (PC clock = Vienna, from `date`). Exe (gate exe) `D:/o30/w/v2p4_pc1/src_copy/forge_ltopgo_v2p4_pc1.exe` sha256 a2a560cb4b6a2c1127a41867fc5287cad0834bcd207f0583571c248d363ee7ca.
All runs at Idle on CPU 0 only (mask 0x1 through `D:/a14/tools/opus_lowrun.py`; every tool pins itself to the same mask), one at a time, between 13:05 and 14:05; no process of anybody else was touched. Scripts: `D:/o30/checks_gpu/scripts/` (step.sh, chain.sh, depth_probe_ab.py, bullet_cpu0.ps1, cpu_busy.ps1, net_ready.py, make_draft.py).

Checks per net: 1. smoke (`tools/smoke2m.py`, 300 s self-play at a real clock 2000+20 ms, Threads 2, Hash 16, OwnBook false, EvalFileV2 = the net - as `a/net_final_checks.sh` step 1, but both engine threads on the one CPU 0); 2. UCI conformance with the net loaded (`tools/uci_conformance_o30.py`, Threads 2); 3. game-position speed (`scripts/depth_probe_ab.py` = `a/depth_probe_o30.py` plus `--opt-a` and a load check): the net (B) vs its control (A, the lock function as v2 replicas with the same bucket layout) on the same exe, 200 positions from the match PGN `D:/o30/control/lockkb4_v2p4/lockkb4_v2p4.pgn`, `go movetime 200`, Threads 1, Hash 16, 2 rounds A-B / B-A; the nodes-per-second ratio B / A is the geometric mean over positions with its 95 % CI; the depth difference is depth at equal time (not a strength claim). No Elo claim anywhere: these are play / conformance / speed checks only.

## o30_gpu_kb4warm_r2

- net `D:/o30/nets/o30_gpu_kb4warm_r2/o30_gpu_kb4warm_r2.nnue2` sha256 08faa2f0301de7583611fd9ae045f596de501bd01657aba36e141a7f7c8da369 md5 3db50f1efe452a09018431c086a019d8, fnv1a 8ad8b3133ed0a15c, package RESULT.json all_checks_passed = True; control `D:/o30/nets/lockv2/lock_kbrank4_ob8.nnue2` md5 7cd8baa967df93228816cd7f1146d58d
- **1. smoke 300 s: PASS** - games 49 (finished 48), plies 6300, illegal 0, crashes 0, hangs 0, time losses 0, overruns 0 (within the 1000 ms margin, reported only), option errors 0, stderr empty; Threads 2, Hash 16, tc 2000+20, mask 0x1, idle True
  - step.sh start 2026-11-04 13:05:13 (PC clock), hard end 14:03, expected 330 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 15.6 % (avg of 3 x 1 s)
  - cpu1 busy 6.8 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:05:22
  - --- run end 2026-11-04 13:10:22 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/smoke_300s.txt` md5 09a87996ce75cf6a16c93f9638596b73; `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/smoke_300s.json` md5 c2d57425c395413686be3a3b7c9b1919; `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/smoke_300s.stderr.txt` md5 d41d8cd98f00b204e9800998ecf8427e
- **2. UCI conformance with the net loaded: PASS** - 22 / 22 checks; net load line fnv1a 8ad8b3133ed0a15c (= the package)
  - observation (not counted): OwnBook true (the default) + go infinite in a book position: conform
  - step.sh start 2026-11-04 13:10:24 (PC clock), hard end 14:03, expected 150 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 17.6 % (avg of 3 x 1 s)
  - cpu1 busy 5.4 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:10:33
  - --- run end 2026-11-04 13:10:37 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/uci_conformance.txt` md5 5f313c8d8746b7743abf75515e2464a7; `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/uci_conformance.json` md5 6f88b4fe84633490f171792e2ae2f940
- **3. game-position speed (main): nps B / A = 0.9984 (95 % CI 0.9902 .. 1.0067)** over 200 positions x 2 rounds, movetime 200 ms; geometric mean nps A 1946356, B 1943253; depth at equal time A 19.520, B 19.468, B - A -0.052 (SE 0.110); 150.4 s; loads: A (control) fnv1a de5133379be80e0d x2 (the control file), B (net) fnv1a 8ad8b3133ed0a15c x2 (= the package)
  - step.sh start 2026-11-04 13:10:39 (PC clock), hard end 14:03, expected 300 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 33.5 % (avg of 3 x 1 s)
  - cpu1 busy 6.5 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:10:48
  - --- run end 2026-11-04 13:13:19 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/depth_probe.txt` md5 d89bbc120adeee8c4aa250b571ee2c5d; `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/depth_probe.json` md5 ea2da8563ab3a89959c4b5d6170caa79
- **3. game-position speed (mt500): nps B / A = 0.9986 (95 % CI 0.9852 .. 1.0121)** over 100 positions x 2 rounds, movetime 500 ms; geometric mean nps A 2061161, B 2058227; depth at equal time A 20.720, B 20.535, B - A -0.185 (SE 0.134); 190.9 s; loads: A (control) fnv1a de5133379be80e0d x2 (the control file), B (net) fnv1a 8ad8b3133ed0a15c x2 (= the package)
  - step.sh start 2026-11-04 13:32:47 (PC clock), hard end 14:03, expected 244 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 14.3 % (avg of 3 x 1 s)
  - cpu1 busy 6.8 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:32:56
  - --- run end 2026-11-04 13:36:07 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/depth_probe_mt500.txt` md5 eb093fd57f852be8a6a095bd5f8cfd5a; `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/depth_probe_mt500.json` md5 f2ab0c1c12bfe45fc5b077f78dd725ce
- **3. game-position speed (rep1): nps B / A = 0.9987 (95 % CI 0.9910 .. 1.0064)** over 200 positions x 2 rounds, movetime 200 ms; geometric mean nps A 1950151, B 1947534; depth at equal time A 19.335, B 19.525, B - A +0.190 (SE 0.107); 149.0 s; loads: A (control) fnv1a de5133379be80e0d x2 (the control file), B (net) fnv1a 8ad8b3133ed0a15c x2 (= the package)
  - step.sh start 2026-11-04 13:21:47 (PC clock), hard end 14:03, expected 300 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 14.9 % (avg of 3 x 1 s)
  - cpu1 busy 13.8 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:21:57
  - --- run end 2026-11-04 13:24:26 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/depth_probe_rep1.txt` md5 e9548b4a85b76603109836eb16caca8b; `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/depth_probe_rep1.json` md5 a5c59dfad63c1b46987050bb21751d24
- **3. game-position speed (rep2): nps B / A = 1.0019 (95 % CI 0.9828 .. 1.0214)** over 200 positions x 2 rounds, movetime 200 ms; geometric mean nps A 1898648, B 1902322; depth at equal time A 19.470, B 19.375, B - A -0.095 (SE 0.106); 150.2 s; loads: A (control) fnv1a de5133379be80e0d x2 (the control file), B (net) fnv1a 8ad8b3133ed0a15c x2 (= the package)
  - step.sh start 2026-11-04 13:27:09 (PC clock), hard end 14:03, expected 300 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 15.4 % (avg of 3 x 1 s)
  - cpu1 busy 7.9 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:27:18
  - --- run end 2026-11-04 13:29:49 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/depth_probe_rep2.txt` md5 f75ccf771f0cf81391bfd7c339ff5eeb; `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/depth_probe_rep2.json` md5 9ef4098112f8df58443929bbfe0b73fa
- **pooled speed at movetime 200 ms over 3 runs (main, rep1, rep2): nps B / A = 0.9997 (95 % CI 0.9923 .. 1.0071; 600 paired position-runs, the same positions in every run); single-run ratios 0.9984 .. 1.0019**
  - probe dry run (positions parsed): `D:/o30/checks_gpu/o30_gpu_kb4warm_r2/probe_dryrun.txt` md5 54088ec335a806d7ef2b4a0d4ddf2087
- **works in Forge: yes (smoke PASS, UCI conformance PASS with the packaged net loaded, speed probe ran with the packaged net loaded)**

## o30_gpu_kb8warm_r3

- net `D:/o30/nets/o30_gpu_kb8warm_r3/o30_gpu_kb8warm_r3.nnue2` sha256 c32b9879bf2013e13ab0387b3f0e9610876a2883ca3d69cfb2f7478e5e3dea30 md5 acd7fcbbf14fa3c8855c3db5f38f0a5a, fnv1a 885fee31103683a2, package RESULT.json all_checks_passed = True; control `D:/o30/nets/lockv2/lock_kbrank4x2_ob8.nnue2` md5 ccacfefbc393d0475c9b98202c5daf3e
- **1. smoke 300 s: PASS** - games 49 (finished 48), plies 6158, illegal 0, crashes 0, hangs 0, time losses 0, overruns 1 (within the 1000 ms margin, reported only), option errors 0, stderr empty; Threads 2, Hash 16, tc 2000+20, mask 0x1, idle True
  - event: {"event": "overrun", "game": 1, "ply": 113, "used_ms": 342, "left_ms": 57}
  - step.sh start 2026-11-04 13:13:40 (PC clock), hard end 14:03, expected 330 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 38.4 % (avg of 3 x 1 s)
  - cpu1 busy 14.3 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:13:50
  - --- run end 2026-11-04 13:18:50 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/smoke_300s.txt` md5 f93dc9305c15e7b89ed5bc7f99c847ee; `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/smoke_300s.json` md5 6c1ce08f41e41b0819e685bda586e980; `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/smoke_300s.stderr.txt` md5 d41d8cd98f00b204e9800998ecf8427e
- **2. UCI conformance with the net loaded: PASS** - 22 / 22 checks; net load line fnv1a 885fee31103683a2 (= the package)
  - observation (not counted): OwnBook true (the default) + go infinite in a book position: conform
  - step.sh start 2026-11-04 13:18:52 (PC clock), hard end 14:03, expected 150 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 92.8 % (avg of 3 x 1 s)
  - cpu1 busy 6.9 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:19:01
  - --- run end 2026-11-04 13:19:05 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/uci_conformance.txt` md5 698782fedd180c17aff4fecc647ab804; `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/uci_conformance.json` md5 83e953e7ed02443880602ed92395ce70
- **3. game-position speed (main): nps B / A = 1.0232 (95 % CI 1.0059 .. 1.0409)** over 200 positions x 2 rounds, movetime 200 ms; geometric mean nps A 1880175, B 1923847; depth at equal time A 19.218, B 19.418, B - A +0.200 (SE 0.126); 149.5 s; loads: A (control) fnv1a 7429405ac8d9a429 x2 (the control file), B (net) fnv1a 885fee31103683a2 x2 (= the package)
  - step.sh start 2026-11-04 13:19:06 (PC clock), hard end 14:03, expected 300 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 18.1 % (avg of 3 x 1 s)
  - cpu1 busy 3.1 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:19:16
  - --- run end 2026-11-04 13:21:45 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/depth_probe.txt` md5 d2e8a8eda6c9a95e3a360277446a5376; `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/depth_probe.json` md5 ff9441396fcab92465776bf69bc466e5
- **3. game-position speed (mt500): nps B / A = 0.9759 (95 % CI 0.9648 .. 0.9871)** over 100 positions x 2 rounds, movetime 500 ms; geometric mean nps A 1772599, B 1729853; depth at equal time A 20.270, B 20.190, B - A -0.080 (SE 0.160); 191.0 s; loads: A (control) fnv1a 7429405ac8d9a429 x2 (the control file), B (net) fnv1a 885fee31103683a2 x2 (= the package)
  - step.sh start 2026-11-04 13:36:09 (PC clock), hard end 14:03, expected 244 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 24.9 % (avg of 3 x 1 s)
  - cpu1 busy 8.7 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:36:19
  - --- run end 2026-11-04 13:39:30 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/depth_probe_mt500.txt` md5 7f755a85d9259e798ee468abd902d44a; `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/depth_probe_mt500.json` md5 20e070512532217293068ae0b42c99d1
- **3. game-position speed (rep1): nps B / A = 0.9994 (95 % CI 0.9910 .. 1.0079)** over 200 positions x 2 rounds, movetime 200 ms; geometric mean nps A 1910560, B 1909407; depth at equal time A 19.433, B 19.492, B - A +0.060 (SE 0.100); 149.5 s; loads: A (control) fnv1a 7429405ac8d9a429 x2 (the control file), B (net) fnv1a 885fee31103683a2 x2 (= the package)
  - step.sh start 2026-11-04 13:24:28 (PC clock), hard end 14:03, expected 300 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 16.8 % (avg of 3 x 1 s)
  - cpu1 busy 4.9 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:24:37
  - --- run end 2026-11-04 13:27:07 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/depth_probe_rep1.txt` md5 7b5f5f258964f4a24c87f616a3aaf200; `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/depth_probe_rep1.json` md5 49d5eab9ce49423f0be06d5c324f92b3
- **3. game-position speed (rep2): nps B / A = 0.9850 (95 % CI 0.9679 .. 1.0023)** over 200 positions x 2 rounds, movetime 200 ms; geometric mean nps A 1730439, B 1704417; depth at equal time A 19.220, B 19.108, B - A -0.113 (SE 0.112); 149.2 s; loads: A (control) fnv1a 7429405ac8d9a429 x2 (the control file), B (net) fnv1a 885fee31103683a2 x2 (= the package)
  - step.sh start 2026-11-04 13:29:51 (PC clock), hard end 14:03, expected 300 s
  - sharer: python.exe pid 10192 aff 0x3 class Idle
  - cpu0 busy 19.7 % (avg of 3 x 1 s)
  - cpu1 busy 96.9 % (avg of 3 x 1 s)
  - --- run start 2026-11-04 13:30:00
  - --- run end 2026-11-04 13:32:30 exit 0
  - files: `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/depth_probe_rep2.txt` md5 38804fa7c1e26797db6d106456cc0ebb; `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/depth_probe_rep2.json` md5 434e0d0ffd052d92accf3be026ec3407
- **pooled speed at movetime 200 ms over 3 runs (main, rep1, rep2): nps B / A = 1.0024 (95 % CI 0.9937 .. 1.0112; 600 paired position-runs, the same positions in every run); single-run ratios 0.9850 .. 1.0232**
  - probe dry run (positions parsed): `D:/o30/checks_gpu/o30_gpu_kb8warm_r3/probe_dryrun.txt` md5 f984eb2b0c63139cb6ad939c1082e6d6
- **works in Forge: yes (smoke PASS, UCI conformance PASS with the packaged net loaded, speed probe ran with the packaged net loaded)**

## Summary

- o30_gpu_kb4warm_r2: works in Forge: yes (smoke PASS, UCI conformance PASS with the packaged net loaded, speed probe ran with the packaged net loaded)
- o30_gpu_kb8warm_r3: works in Forge: yes (smoke PASS, UCI conformance PASS with the packaged net loaded, speed probe ran with the packaged net loaded)

## Notes and caveats

- Reading of the speed figures: the control of each net is the lock's own evaluation written as v2 replicas with the same
  bucket layout, on the same exe, so the ratio is what the net itself costs beyond its bucket layout. KB4 (vs
  lock_kbrank4_ob8): pooled 0.9997 (CI 0.9923 .. 1.0071), single runs 0.9984 / 0.9987 / 1.0019 and 0.9986 at movetime 500
  - no measurable cost. KB8 (vs lock_kbrank4x2_ob8): pooled 1.0024 (CI 0.9937 .. 1.0112), single runs 1.0232 / 0.9994 /
  0.9850 and 0.9759 at movetime 500 - the single runs scatter by about +-2 to 3 % around 1 (the same run-to-run noise the
  main session noted for this testbed), without a consistent sign; no cost beyond noise is shown, and none excluded below
  about 2 %. The pooled CI treats the 600 position-runs as independent; for KB8 the between-run spread (0.985 .. 1.023)
  is wider than any single-run CI, so that spread is the better uncertainty statement, not the pooled +-0.9 %. The
  depth differences at equal time are all within about 2 SE of 0 and are not strength statements.
- Smoke: `net_final_checks.sh` step 1 runs Threads 2 on two CPUs; here both engine threads shared the one logical CPU 0
  (mask 0x1), a harder clock test than the gates' own. KB8 had one overrun (game 1, ply 113: 342 ms used with 57 ms left on
  the 2000+20 ms clock, 285 ms over, inside the 1000 ms margin that fastchess gives in the crew's gates) - reported, not
  a time loss; KB4 had none. 49 games each (48 finished, one cut by the 300 s end).
- Load next to the figures: the CPU 0 / CPU 1 busy lines are 3 x 1 s snapshots taken right before each run (not during
  it). The only other process with CPU 0 in its mask (apart from full-mask system processes) was the forge-uci MCP server
  (python pid 10192, Idle, mask 0x3, idle most of the time). The 92.8 % CPU 0 snapshot before KB8's conformance has no
  identified cause: the sharers list of that block shows only pid 10192, no own process was alive (the smoke's step had
  returned), and full-mask processes are not listed by the sharers check; the 96.9 % CPU 1 snapshot before KB8 rep2 shows the SMT sibling busy
  with somebody else's work at that moment (CPU 1 is not in my mask; its load during the runs is not recorded). No
  forge-v2-bullet process had CPU 0 in its mask at any step (the r3_kb8warm trainer, pid 5948 on mask 0x3, had ended
  before 13:05; later trainers ran on mask 0x38).
- Window: first engine start 13:05:22, last engine end 13:39:30 (PC clock, from `date` in the step logs); no further
  run was started after 13:39:30. Every run went through `opus_lowrun.py --mask 0x1` (Idle +
  affinity read back, fail closed); smoke2m (`--mask 0x1 --idle`), uci_conformance (`--mask 0x1`) and the probe
  (`--mask 0x1`) pinned themselves to the same mask (no tool overrides it with a wider one).
- Not run (not asked, listed for completeness): the normal step 2 of `net_final_checks.sh` (`bench 16` NPS ABBA against
  the lock exe) and its step 3 (the sanity match; KB4's own 400-game sanity match runs on CPU 6, untouched); no probe
  against the lock exe itself. Nothing from the task list is missing.
- Files: everything under `D:/o30/checks_gpu/<net name>/` (step logs *.txt with the command line, clock, sharers and
  busy snapshots; smoke_300s.json / .stderr.txt; uci_conformance.json; depth_probe*.json with per-position depths and
  nps); chains: `D:/o30/checks_gpu/<net name>/chain*.txt`, `D:/o30/checks_gpu/after_kb4.txt`,
  `D:/o30/checks_gpu/after_reps.txt`; helpers in `D:/o30/checks_gpu/scripts/`. Nothing in D:/o30/wt or D:/o30/nets was
  written; the nets were only read. The probe PGN `D:/o30/control/lockkb4_v2p4/lockkb4_v2p4.pgn` (md5
  95a432e46d38c7d30c12eccfb9cc73f3) is the finished control match of this exe (ended 11:49).
