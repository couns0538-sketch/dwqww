# OSS scout for Forge - STATUS (handoff file)

Updated: 2026-11-06 21:45 (PC clock). Branch `opus-oss-scout-20261106` (from main 5176ddf7), repo copy of this file:
`opus_oss_scout/STATUS.md`. Plan: `C:\Users\Administrator\.claude\plans\velvet-seeking-meerkat.md`.

## Rules in force (brief of 2026-11-06 + findings)
- Research and sandbox trials only: no engine edits, no Elo claims, no helper agents.
- Own work: Idle priority, CPUs 2-3 (mask 0xC). The session process (pid 4532) was narrowed from 0xF to 0xC
  at 19:24 (PC clock); its children inherit Idle + 0xC. At most 2 heavy threads.
- Never touch: live gates, fastchess, forge_queue, self-play, NNUE training runs or their run dirs, locks, nets in use,
  datasets (copies of small samples only), other bots' configs, F:\ospd, C:\ospd_hunt. No deletes, no kills, no
  force-push, no main, no PATH changes or system installs. GPL / AGPL = ideas only.
- Disk: build and download only into `C:\opus_5h\oss_scout\` (target <= 10 GB, hard cap 15 GB). Stop downloading when
  C:, D: or F: is under 30 GB free. Nothing is written to D: or F:.
- Commits: identity couns0538-sketch, no vendor names, no trailer; push `git push -q -u origin opus-oss-scout-20261106`.

## Findings that change the brief (one sentence each)
1. The GPU is an AMD RX 7900 XT (no nvidia-smi); headroom is read from Windows GPU counters, the live trainer uses
   ~75-80 % compute and npt has the GPU booked to Nov 8, so this job uses no GPU and writes GPU steps as commands for an
   owner window.
2. E: is a 3 GB volume, so the 30 GB floor applies to C:, D: and F: only.
3. The Idle trainer shares CPUs 0-3, so own work runs on CPUs 2-3 only and every rate is written next to the crew load
   (CPUs 0-3 were 66-85 % busy at 19:25 before any own work).
4. Already with the crew (cited, not re-proved): bullet on ROCm for v2 nets (30-h job), Forge's own Syzygy reader
   (R13 P6, not in the lock exe), UHO_Lichess_4852_v1.epd on the PC (gates use 8moves_v3), large pages (H1/H7
   NO-WIN), own SPSA tuners, exact fastchess LLR tools.
5. Commit messages carry no vendor names and no trailer (same-day 5-h brief convention).

## Done
- Folder layout `C:\opus_5h\oss_scout\{dl,build,data,tools,tmp,logs}`; gate script `tools\scout_gate.ps1` (first run
  OK, log `logs\scout_gate.jsonl`).
- Shallow sparse clone `C:\opus_5h\oss_scout\repo` (sparse `/opus_oss_scout/`), branch created.

- Step 1 pushed (058dea3b).
- Step 2: `opus_oss_scout/CATALOG.md`, 69 entries (A 9, B 13, C 19, D 19, E 5, F 4). Licence finding: bullet_lib links
  crates.io sfbinpack (GPL-3.0) and montyformat (AGPL-3.0) -> any bullet build is GPL/AGPL-encumbered (tool use only).
- T1 setup: own fastchess 1.8.2-alpha (zip sha256 007CE550..., exe C6D7E445...), lock copy 4181A589 (pin_check PASS
  19:27), books copied (8moves 5835239F, UHO 7A7F6470); smoke 4 games OK.
- Step 3: ranking in REPORT.md section 1 (pushed d07e21f); ideas-only section 4 written.
- T1 UHO half DONE (19:28-19:41): 600 pairs, pentanomial [1, 25, 130, 239, 205] = fastchess, nElo +296.3
  [+276.7, +316.0], draw ratio 0.303. Gate-TC context (8moves, 10+0.1): draw ratio 0.797
  (`trials/t1_books/logs/gate_context_8moves.txt`).
- T2 prepared: source `build/t2/src_w6` = d4f4312 (LF) + trial_w6.patch (md5 5786e9b8, 8 files, no rejects); build
  script `tools/t2_build.ps1`; workload copy `data/frozen_train_cmds.txt` (sha256 1D52720A = QA kit v2.3 v1).
- T3 prepared: samply 0.13.1 zip (sha256 8fed74da = the release's .sha256) unpacked in `dl/samply-0.13.1/x`.
- T5 prepared: Fathom c9c6fef0 in `dl/fathom`; P6 tree `build/t5/src_p6` = d4f4312 + syzygy_port.patch (md5 4342d24f)
  + tb_probe.cpp (P6 tip 4bf626eb); 50k FENs `build/t5/data/t5_50k.fens` (sha256 a1b3ca09, seed 20261106, 145
  materials); batch prober source `tools/t5_fathom_batch.c`.
- T1a DONE (pushed 7147dd6): at 2:1 node odds, 8moves nElo +340.5 [+320.9, +360.2] vs UHO +296.3 [+276.7, +316.0];
  ratio UHO / 8moves 0.870 [0.794, 0.947]. UHO is NOT better in this large-gap proxy; small changes still untested (T1b).
- T2 builds:
  - g0 (g++ plain) 758608C8 pin_check PASS (source identity).
  - c0 (installed LLVM 18, MSVC target): FAILS to compile. The VS 18 STL 14.51 asserts "expected Clang 20 or newer"
    (STL1000) and uses `__is_layout_compatible`.
  - llvm-mingw 20261104 (clang 23.1.5, zip sha256 552191b5, 737 MB in `dl/llvm-mingw-20261104/x`):
    - With its libc++: m0 EA0645FB bench DIFF (d11 369996, net-off d11 369292).
    - Cause: libc++ vs libstdc++. The MovePicker's `std::sort` has unstable tie order (search.cpp:632); the LMR table
      uses `std::log`.
    - With `--sysroot=C:/msys64/ucrt64 -stdlib=libstdc++ -rtlib=libgcc -unwindlib=libgcc` (MSYS2 GCC 15.2 runtime):
      m0_lsx 3785AD3B PASS, m1_lsx (ThinLTO) DC0705A1 PASS, m2use_lsx (ThinLTO + IR PGO, workload v1) F982D177 PASS
      full (d11-d22 + perft), net-off d11 / d16 = 375354 / 2448617 = lock, 61 UCI options = lock.
- T2 DONE (pushed d2bd296): ABBA bench 20 on CPU 2 BelowNormal.
  - A/A 1.0052 [0.9977, 1.0127] (SANE).
  - lock vs m2use_lsx **1.0472 [1.0378, 1.0566]** (median +4.53 %, 10/10 pairs > +2.9 %): WIN by the QA rule,
    SCREENING only.
- T3 DONE (pushed 2de37f7):
  - `samply record` needs xperf (ADK, not allowed). Instead: built-in `wpr -start CPU` / `wpr -stop` + `samply import`.
  - Hotspot tables for the clang bench (PDB) and for the lock in the live gate (COFF symbols).
  - `std::sort` in the MovePicker = 3.6-4.8 %; `Move::operator==` 3.4 %.
  - WPR is system-wide (6 s, disclosed).
- T5 DONE (pushed 71258c9): Forge's own Syzygy reader vs Fathom on 50,000 positions: WDL 50000/50000, DTZ
  49678/49678 exact, VERDICT AGREE. Warm WDL probe Forge ~0.97 us vs Fathom ~0.54 us.
- T4 written (design only; no build, no GPU): every K32H3^ piece maps to bullet's advanced example; exporter to the npt
  `.nnue` layout missing; GPU-window plan in `trials/t4_bullet_halfka/TUNING.md`.
- T6 prepared: 2000 Lichess puzzles (CC0, dataset-viewer API, seed 20261106, ratings 399-3025, median 1400) in
  `build/t6/puzzles_2000.jsonl`; solver `tools/t6_solve.py`.

- T1b DONE: 1.33:1 node odds, 1500 pairs per book.
  - UHO 20:13:49-20:54:35, nElo +133.5 [+121.1, +146.0].
  - 8moves 20:54:35-21:36:01, nElo +121.2 [+108.8, +133.6].
  - Ratio 1.102 [0.949, 1.255].
  - Around 21:0x the PC ran critically low on memory, and the session harness stopped the outer chain shell (task
    bxiyom1vz). fastchess and the inner runner finished anyway (end line rc 0). Fixed nodes: games unaffected.
- T6 DONE 21:36-21:39: the lock solves 96.0 % (20k nodes) / 98.8 % (200k) of 2,000 puzzles; 2500+ band 73.5 / 86.7 %.
- REPORT.md FINAL: ranked table, ideas-only section, unproven claims, owner items.

## In progress
- Nothing of this job is running (T1b's fastchess ended 21:36; T6 ended 21:39).

## Exact next step (for the crew; this job is finished)
- QA: official lock path for the T2 clang build (REPORT section 5, item 3).
- QA: the near-zero gate-TC book test (trials/t1_books/TUNING.md 1-2).
- NNUE: the bullet K32H3^ exporter + a GPU window (trials/t4_bullet_halfka/TUNING.md).

## Owner alert (not touched)
- C: free falls fast because the live npt run `..._s85` writes ~1.4 GB checkpoints to `C:\forge_nnue_train\runs`
  (4.3 GB in 20 min at 19:36; C: 65.7 GB at 19:06 -> 58.4 GB at 19:37). At that rate C: reaches 30 GB in ~2 h and fills
  in ~4-5 h, which would stop the trainer. This job's own footprint on C: is ~0.2 GB.
- Update 19:56: C: 50.3 GB (58.2 at 19:42), i.e. ~0.5 GB/min. Trainer pid changed 2188 -> 14296 -> 1036 (new runs).
  This job's footprint ~1.1 GB (llvm-mingw 0.9 GB of it).
- Update 20:16: C: 44.5 GB, still ~0.5 GB/min. At that rate (a projection) it would cross 30 GB within ~30 min and fill
  within ~1.5 h. This job
  makes no more downloads below 30 GB; its footprint is 1.5 GB (incl. the 354 MB WPR trace).
- Update 21:10 (supervisor.log, read-only):
  - Run s86 DONE 20:24:56.
  - Run s87 (launched 20:24:59) "ended without 'Finished' but made checkpoint progress (epoch006-step000055842.pt) ->
    needs_resume" at 21:03:04, in the same window as the PC's low-memory event. The resume was launched at 21:03:07
    but was not running at 21:10.
  - The supervisor launched s88 at 21:10:10.
  - C: free was 72.5 GB at 21:10 (cleaned by someone else). A second agent session started 20:59; Firefox was
    started 20:32:47 by a process that had already exited (not by this job).
  - This job's processes at 21:10: fastchess + 4 engines (~60 MB in all). Nothing of the trainer was touched.

## Resume commands
- Gate before any heavy step: `pwsh -NoProfile -File C:\opus_5h\oss_scout\tools\scout_gate.ps1 -Step "<what>" -PlannedGB <n>`
- Re-pin the session after an app restart: find the new session process pid (parent chain of `$PID`), then
  `(Get-Process -Id <pid>).ProcessorAffinity = [IntPtr]0xC` (priority must stay Idle).
- Commit: copy `C:\opus_5h\oss_scout\STATUS.md` to `repo\opus_oss_scout\STATUS.md`, then in `C:\opus_5h\oss_scout\repo`:
  `git -c user.name=couns0538-sketch -c user.email=couns0538@gmail.com commit -F <msgfile>` and the literal push.

- Re-run a trial: commands in `opus_oss_scout/trials/<name>/CMDS.md`. Re-check the records:
  `python -I -B tools/check_catalog.py repo/opus_oss_scout/CATALOG.md`, `python -I -B tools/verify_sums.py repo/opus_oss_scout/trials`.

## Unproven claims
- T2 +4.72 % nps: a screening ABBA on a shared PC with the bench-only PGO workload. Not a lock: QA timing, 12k
  BIT-EXACT, warm identity and the Threads 2-4 soak are still owed. No Elo.
- T1: nothing proven for gate TC / gate-size changes; the ~17 % fewer-pairs figure is an extrapolation of T1b.
- T4: no bullet HalfKA throughput on this PC (design only).
- T5 speed ratio (Fathom ~1.8x faster WDL probe): one run on a shared core.
- T6: puzzle rates are not Elo.
