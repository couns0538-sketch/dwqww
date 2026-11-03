# Opus R14-B final report (Couns's job, 2026-11-02 12:05 -> 06:00 Nov 3 PC clock) - INTERIM (updated 22:04), final at the end

Window: 15 hours at the start; Couns at ~19:15: work to 06:00, a 20-minute bug hunt every hour (every finding
fixed), make sure everything works in Forge, a 1-hour bug hunt at the end; no sub-agents.

UNPROVEN everywhere: no Elo or training-quality claims; Engine NNUE / QA decide. Nothing of the live npt line, the
queue, gates, self-play or crew files was touched. Own work ran BelowNormal / Idle on CPUs 2-3 (deviations below).

## Summary
| item | state | key evidence | branch / head |
|---|---|---|---|
| 1 fast npt loader (`--fast-loader`, default off) | DONE except the GPU window (requested in GPU_REQUEST.md, not granted: the npt queue holds the GPU to Nov 8) | batches bit-identical to the old loader's `--num-workers 1` stream (1,000 / 1,000 + validation, 24-config matrix, 3,100 batches past a wrap, trainer path 261 / 261); exact CPU loss match; loader ABBA 8.65x (old w2 vs 1 builder) and **6.25x in the live thread setting** (old w4 vs 2 builders, 95% CI 6.13-6.60); distribution vs the live w4 layout: every total-variation distance < 0.001; **from a fresh clone: DLL rebuilt = b5, adoption rehearsal on a fresh copy of the live trainer (264 / 264 = installer base) -> 261 / 261** (20:42); HANDOFF.md | opus-r14b-fast-loader |
| 2 resumable relabel (`relabel2.py`) | DONE: 1M kill / resume proof PASSED (A uninterrupted vs B hard-exited twice: train / val / labels md5 identical); **the whole 1M with the LTO+PGO probe = the proof's files**; **frozen at sha256 e01caaf1...** (re-frozen 22:46 after shards started to record their settings; before that 56eef0a6... at 22:22 after the damaged-job harness: 29 findings, one silent - a lost run_config.json was re-created; earlier 88454db6... at 20:41 and 0a81dd5f... at 22:03 after a prepare fuzz finding); RELABEL_HANDOFF.md with measured costs (50M: 78.7 h at the whole-1M rate) and a 50M runbook on R8 v5 shards 001-057; 50M run not started (as asked) | logs/proof_finish.log, pgo_full_1M.log, chain_2030/ (suites 150 / 0 then, 154 / 0 after the 22:03 re-freeze, 155 / 0 after the 22:22 and 22:46 ones, in the worktree and fresh clones, bridge PASS, probe builds from a fresh clone = the tested exes, R8 v5 end to end through fen2bin) | opus-r14b-relabel |
| tools (Couns 19:46) | DONE: `opus_r14b/tools/` + `opus_r14b/checks/`, entry point `opus.sh`, skill forge-opus-tools | test_tools.sh 25 / 25; engine tools on real builds; GPU baseline; verify chain / refreeze / hash sweep runs | opus-r14b-status |
| P6 crfix 4b537823 (Couns ~20:57) | DONE: applied with patch -p1, rebuilt, P6 checks re-run, pushed | OFF = the corrected lock pins, WDL / DTZ 220 / 220, check50 20 / 20, fail-closed 9 / 9, CI 41515843128 green | opus-r13-p6-syzygy d1751ca1, 4bf626eb |

## Baseline and improvements (measured numbers only)
Baseline = what the two tasks asked for, as it stood when they were done: item 1 = candidate b5 (verified by 14:45);
item 2 = relabel2.py 5c88438f (the proof code) with the R13 probe ed76de96, prepare in one process, 19 exit-code tests.
| improvement | before (baseline) | after | how measured |
|---|---|---|---|
| relabel prepare speed | 5c88438f: 16.0 / 16.6 s per 200k rows (44.2M rows/h) | `--jobs 2`: 10.8 / 11.1 s (65.7M rows/h) = **1.49x**; `--jobs 1`: 16.7 / 17.0 s (0.97x: added input checks) | same 200k rows, order F J1 J2 J2 J1 F, rows.tsv identical in all six |
| relabel probe speed, 1 thread | R13 probe ed76de96 | LTO+PGO 08299f9f: **1.075x** (ABBA 10 pairs, 95% CI 1.044-1.106); LTO only 1.053x (CI 1.009-1.097) | 10,000 / 10,000 answers identical; answers identical in all ABBA runs |
| relabel throughput, 2 workers on one core | R13: 662,337 / 663,485 rows/h | LTO+PGO: 687,266 / 694,693 rows/h = **1.042x** | 19,927 rows, order R P P R, labels md5 identical |
| 50M rows at 20k nodes, 2 workers (light crew load) | 75.4 h (R13) | 72.4 h (LTO+PGO) | rows / measured rate |
| the whole 1M proof sample with the LTO+PGO probe | the proof ran on the R13 probe | train / val / labels **byte-identical** to the proof's (all 999,921 labels); 635,344 rows/h through 94 min of real crew load -> **78.7 h for 50M** (the planning figure) | logs/pgo_full_1M.log |
| R8 v5 input (games run across shard files) | 5c88438f gives a game crossing a file two game ids (leak risk) | one game id (one input stream in name order) | test + real shards 271 / 272 |
| input / job safety | 19 tests | 154 PASS lines in test_relabel2.sh at 22:03 (cases + reason checks): F1-F8, R17, R25, R27, R28, H2-x, H3-x, P-1 fixed with a test each; 300 damaged-input files fuzzed: every one prepared or refused with file:line; every refusal also checks its reason | test_relabel2.sh, RESULTS.md |
| disk rule of the PC (C: / D: >= 50 GB) | not enforced by the tool | `--min-free-gb` (default 50): prepare / assemble refuse, run stops before the shard that would cross it | quick checks; test cases |
| relabel output through the FPOS converters earlier jobs used | not checked | fen2bin carries the new labels 1,200 / 1,200; the whole 1M output: fen2bin 991,077 + 8,844 records = every row, 0 bad; hce_dump the same counts, 0 bad FEN, 0 clamped | conv_check, logs/conv_full_1M.txt |
| failures that explain themselves | a probe that died ended `run` with a bare traceback and no log line; the launcher of every tool returned 0 when a program could not start | `run` writes "run stop ... <error> (exit N)" to sessions.log; lowrun.ps1 exits 127 (missing program / redirect folder / stdin file) | suite cases with a dead probe; 8 launcher cases |
| fast loader adoption | GPU_REQUEST.md only | HANDOFF.md: adapter path (`--npt-repo` + `--npt-extra --fast-loader`), live trainer = installer base (264 / 264 files), thread advice, distribution check; one-command acceptance check (261 / 261); installer `--loader-dll` copies the loader files | item 1 HANDOFF.md, tools/fl_acceptance.sh |
| works from a fresh clone | tools reached into other worktrees / scratch; a default clone (core.autocrlf=true) wrote CRLF and changed the documented hashes | own lowrun.ps1 copy; probe build exports the lock source from git and uses a committed training file; `opus_r14b/.gitattributes` keeps code LF (fresh clone: relabel2.py sha256 = the branch's); the verify chain's fresh-clone step found two more such bugs (C1 lock export, C2 robocopy), fixed | fresh-clone checks 20:33 and again 20:39-20:42: 0 failures (suites, probe builds = the tested exes, DLL = b5, adoption rehearsal 261 / 261) |
| regression caught by measuring | - | R27: a per-row `Path.resolve()` (76.7 us per call = 15.3 s per 200k rows) in the post-proof one-process prepare; the fix took it from 36.5 / 38.3 s to 17.9 / 18.1 s on the same 200k rows (2.05x, the same crew load: one BelowNormal job in both); output identical | logs/measure/resolvefix_check.log, post_chain.log |

## Item 1 - fast npt data loader (`opus_r14b/item1/`)
- Own code `fastloader/forge_fastloader.cpp|.py`, spec LOADER_SPEC.md, installer `tools/install_fast_loader.py` =
  `patches/0005-fast-loader-switch.patch` (default off), optional `patches/0006-seed-before-model-OPTIONAL.patch`.
- b5 DLL sha256 9eb29b7d134a73eb58d47b2ced38587ed450ffaf11fdfcb108898652cefcd935 (pc1 = pc2).
- Speed (advisory): loader-only ABBA 8.65x (CI 8.58-8.69) on CPUs 2-3; a full 152.5M-position epoch through the fast
  loader alone in 29.8 s at 166 MB; CPU training 3.5x faster (64 batches 11.4 vs 40.2 min).
- Finding for Engine NNUE: `--seed` does not fix the initial weights (model built before seeding; torch 2.11 ROCm
  seeds per process from the clock).
- The GPU use it should raise, measured (keeper's HWiNFO log, `tools/gpu_util_stats.py`): the live npt line with the
  default loader, 2026-11-02 15:14-21:14: GPU Utilization mean 45.7 %, p50 48 %, >= 90 % in only 4.0 % of samples;
  hourly means 40-56 %. The trainer runs at Idle on 2-4 CPUs (the keeper sets the mask 0x3 / 0xF) and used 0.4-0.6
  cores at 21:19-21:22 on CPUs that were 86-90 % busy, mostly with heavier-class work - but with 10-14 % idle time
  left, so it was not purely CPU-starved (an early "starved" wording was corrected in hunt #5). On one logical CPU in
  the live thread setting the default loader
  costs 2.45 and the fast loader 0.34 CPU-us per kept position (7.19x, CI 7.08-7.26): feeding the live line takes
  0.30-0.41 of a CPU with the default loader, 0.04-0.06 with the fast one. The GPU window must show the effect.
- Robustness (bug hunt #4): 371 damaged-file runs incl. a bounds-checked build: clean errors, no crash, no hang; one
  limit shared with the default loader (a cyclic stream over a file in which nothing passes the skip filter waits).

## Item 2 - resumable relabel (`opus_r14b/item2/`)
- relabel2.py (prepare / run / assemble / status), FROZEN at sha256
  e01caaf1cf8814771033b3deb71727fd0d2eb45f39ee9b27ae54c7d2970f1602 after the verify chain and three re-freezes (22:03
  after the prepare fuzz, 22:22 after the damaged-job harness `job_damage.py`, 22:46 after shards started to record
  their node limit / hash / probe sha256: suites 155 / 0 in the worktree and a
  fresh clone, bridge PASS, label / game-id functions identical to the proof's); tests, proof driver, bridge, measurement scripts, probe
  LTO / PGO build + bench, label statistics; skill forge-relabel-job; 50M runbook (RELABEL_HANDOFF.md) whose prepare
  command ran as written.
- Proof: 999,921 rows in 10,880 games (val 99 games / 8,844 rows, overlap 0); B's hard exits at 14:48:59 (shard 14)
  and 15:34:20 (shard 36), interrupted attempts kept, no orphaned probe; md5 train 6e9e4e5a..., val 8e639f41...,
  labels 2614e82d... for both.

## Tools for Couns and Opus (Couns 19:46: "create tools scripts that you and i can use"; 19:47-21:17 by the commits)
`opus_r14b/tools/` on opus-r14b-status, skill forge-opus-tools, one entry point `bash opus_r14b/tools/opus.sh help`:
status (job + PC in one look), lint (doc_lint.py: control bytes, CRLF, mojibake, eaten Windows backslashes, broken
GitHub tables, dead links - it found a broken RESULTS table on its first run and a path with lost backslashes in the
memory index), abba (palindromic A/B timing of any two commands with identity check, t-CI and load capture), engine
(fresh export + lock-recipe build + bench / perft pins of any engine ref), bisect (first commit that changed bench
nodes, building each candidate from a `git archive` export), time (spans and pauses from commit times), load, test
(test_tools.sh, 25 checks), gpu (gpu_util_stats.py: GPU utilisation from the keeper's HWiNFO log). `opus_r14b/checks/`
holds the verify chain, the fresh-clone checks, refreeze.sh and the hash sweep as they ran. Validated on real data:
engine builds of the lock and an R12 branch (ALL OK), a planted-change bisect (found), the frozen relabel code
(refreeze 0 failures). Own review R14B-T-1 fixed 5 defects in the new tools, hunt #4 one more (TOOLS.md).

## Review milestones (all after 13:45 are self-reviews, NOT independent)
R14B-I1-1 (sub-agent, before the no-sub-agent rule), R14B-I1-2, R14B-I2-1 (7 findings), R14B-I2-2 (F8, R17, R25),
R14B-I2-3 (handoff exe location), R14B-T-1 (tools); hourly bug hunts #1 19:05, #2 19:41, #3 20:04 (relabel2 `run`
now logs a probe failure to sessions.log and lowers its priority before hashing; item 1 trainer path checked for
use-after-release: none; with the advisor's read: the stop line's exit code, the CPU mask range), #4 20:50 (the fast
loader fuzzed with 371 damaged files: no crash / hang; engine_bisect needs GOOD on BAD's first-parent line);
details in each RESULTS.md and TOOLS.md. Final 1-hour bug hunt: 05:00-06:00.

## Deviations and incidents (honest record)
- 15:22-16:27: dev test runs ran as a third Idle process next to the two proof probes on CPUs 2-3 (over the "<= 2
  threads" rule, inside the 2-CPU mask).
- Item 1 (earlier): an orphaned 3-minute CPU run after a TaskStop (see item 1 RESULTS).
- Two committed text files had backslashes turned into control characters by a heredoc + inline Python (TOOLS.md,
  memory file); fixed, all R14-B files scanned clean.
- CPUs 2-3 are one physical core (SMT): every rate is per that core; crew BelowNormal jobs slowed Idle work at times
  (load samples logged next to each rate).
- Times written from memory instead of the clock (bug hunt #3 "20:04-20:20" when it was 20:04-20:09; the launcher
  fix "20:25-20:31" when the clock said 20:28; a robocopy overlap placed in "pair 1-2" without a per-run log): each
  corrected within minutes from the clock or the log. Tool headers also carried a guessed "2-4 min per build"
  (measured: ~15 s), corrected.
- CPU sharing with the live trainer: the own budget CPUs 2-3 lies inside the trainer's widest mask (0xF). The keeper
  sets that mask itself (0xF at 20:24, 0x3 at 21:15); while it was 0xF, the Idle trainer and the Idle relabel probes
  (18:49-20:24) shared CPUs 2-3, the documented arrangement (forge-pc-rules). The hourly GPU means show no drop in that
  window (18:00 42 %, 19:00 56 %, 20:00 43 %).
- Two bugs reached the branches and were found only by the verify chain's fresh-clone step: build_probe_opt.sh's lock
  export (git archive from a subfolder, broken since 19:18) and a robocopy call under Git Bash (`/E` -> `E:/`); both
  fixed and re-verified from a new fresh clone (0 failures, 20:42). A 1-second robocopy test of mine overlapped the
  live-setting loader ABBA (no outlier pair).

## Couns's message of ~20:53 (corrections to the R15 prompt) - what R14-B checked
- Lock pins: only fd3a5190... (`forge_ltopgo_x_al1s198_v23.exe`) with bench d11 312866 / d13 862329 / d16 3024920 /
  d20 12389307 / d22 34048354, perft startpos d5 4865609, kiwipete d5 193690690. No R14-B branch, skill or memory
  note contains the wrong "273845 / 718758 / 3028212" (git grep of all three branches, 20:54); the only pin check
  R14-B ran (`engine_fresh_check.sh` through the lock package's `uci_check.py`) uses exactly the pins above, and
  `engine_bisect.sh` compares with the good commit's own count (312,866 at d11). Nothing passed against the wrong
  numbers, so nothing needs a re-run. The lock exe itself (read-only, 21:30): both copies,
  `forge_push\bin\` and `forge_push\locks\lock_AL1_s198_ltopgo_x_20261030\forge_ltopgo_x_al1s198_v23.exe`, have the
  sha256 fd3a5190... from the message.
- R15 is not started; it waits for this report's final version (R14-B ends 06:00 Nov 3 PC clock).
- Code Review's LOW P6 crfix 4b537823: **on the PC now** -
  `C:\Users\Administrator\qa_crfix_astra_r10\r13_patches\p6_checks_crfix.patch`, md5
  4b537823b4c93aaf390413843299720b (sha256 5c572b72..., 2,311 bytes, file time 2026-11-02 20:53:41, i.e. it arrived
  after R14 ran). It patches opus_r13/p6/check_tb.py, ci_fetch_tables.sh and tb_probe.cpp (branch
  opus-r13-p6-syzygy). Couns (~20:57): apply it with patch -p1 at the root of opus-r13-p6, rebuild, re-run the P6
  checks, commit and push - done: applied cleanly (3 files, +15 -3); port tree from git = R13's source; plain engine
  rebuilt (differs from R13's only in the PE timestamp / checksum bytes); OFF = the corrected lock pins; both ON benches
  = R13's; tb_probe rebuilt: WDL / DTZ 220/220 vs python-chess, answers = R13's; check50 20/20; the three new
  fail-closed paths 9/9 (each against the R13 version); commit d1751ca1 pushed; CI run 41515843128 (started by hand:
  the workflow's push filter does not cover these files) green - 70 tables present after the new count check,
  ASan+UBSan smoke 0 illegal moves / 0 sanitizer lines in all 5 configs. Incident: a test setup mistake sent 3 GET
  requests to the public table mirror (all 404, nothing downloaded); fixed and re-run offline. Details:
  opus_r13/p6/RESULTS.md.
- The four candidate exes to keep are in place with the given sha256 (checked 20:54, read-only): syz_pc1 150374ff...,
  sfs 029d58e8..., speed2 de20653c..., the relabel probe 08299f9f.... R14-B deletes nothing anywhere.

## Owner items
- GPU window for item 1 (GPU_REQUEST.md); Engine NNUE decides on `--fast-loader` and patch 0006.
- Engine NNUE decides on the 50M relabel (inputs, node count, probe); RELABEL_HANDOFF.md has commands and costs.
- R15: start only after this report's final version; use the corrected pins; keep the four exes (P6 crfix: done above).
- Crew: the npt trainer runs at Idle on its own mask (0x3 / 0xF, set by the keeper) and used 0.4-0.6 cores of its two
  CPUs at 21:19-21:22; those CPUs were 86-90 % busy (21:32), mostly with heavier-class work such as BelowNormal crew
  jobs with affinity on all CPUs (Astra's audit_forge_admission.py, ~1 core each), with 10-14 % idle left; GPU 31-50 %
  in the same minutes. Keeping such jobs off the trainer's CPUs, or another priority class for the
  trainer, is the crew's decision (item 1 RESULTS; the overnight watcher log has the series).
