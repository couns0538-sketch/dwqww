# Opus R14-B final report (Couns's job, 2026-11-02 12:05 -> 06:00 Nov 3 PC clock) - INTERIM (updated 03:36), final at the end

Window: 15 hours at the start; Couns at ~19:15: work to 06:00, a 20-minute bug hunt every hour (every finding
fixed), make sure everything works in Forge, a 1-hour bug hunt at the end; no sub-agents.

UNPROVEN everywhere: no Elo or training-quality claims; Engine NNUE / QA decide. Nothing of the live npt line, the
queue, gates, self-play or crew files was touched. Own work ran BelowNormal / Idle on CPUs 2-3 (deviations below).

## In short
- **Item 1, fast npt loader** (`--fast-loader`, off by default): done and verified on the CPU - the same batches as
  the default loader's `--num-workers 1` stream, byte for byte; exact loss match; 6.25x the default loader's
  throughput in the live thread setting (8.65x in the w2 layout). Owed: the GPU measurement (no window granted; the
  npt queue holds the GPU to Nov 8). Adoption: item 1 HANDOFF.md (installer + one-command acceptance check).
- **Item 2, resumable relabel** (`relabel2.py`): done - the 1M kill / resume proof passed (md5 identical), frozen at
  e01caaf1; 50M rows at 20k nodes = ~79 h on one core (RELABEL_HANDOFF.md runbook; not started, as asked);
  `verify_job.py` checks a finished job before its labels are used.
- **Tools** (Couns 19:46): `opus_r14b/tools/opus.sh` (status, lint, abba, engine, bisect, time, load, gpu, test);
  `opus_r14b/checks/final_checks.sh` runs every end-of-job check in about a minute.
- **The night** (Couns ~19:15): hourly bug hunts; every finding fixed and re-checked (records in the item RESULTS.md
  files and TOOLS.md); the 1-hour hunt at the end. P6 crfix applied (Couns ~20:57); R15 waits for this report.

## Summary
| item | state | key evidence | branch / head |
|---|---|---|---|
| 1 fast npt loader (`--fast-loader`, default off) | DONE except the GPU window (requested in GPU_REQUEST.md, not granted: the npt queue holds the GPU to Nov 8) | batches bit-identical to the old loader's `--num-workers 1` stream (1,000 / 1,000 + validation, 24-config matrix, 3,100 batches past a wrap, trainer path 261 / 261); exact CPU loss match; loader ABBA 8.65x (old w2 vs 1 builder) and **6.25x in the live thread setting** (old w4 vs 2 builders, 95% CI 6.13-6.60) - medians of 10 per-pair ratios, intervals of the mean ratio; distribution vs the live w4 layout: every total-variation distance < 0.001; **from a fresh clone: DLL rebuilt = b5, adoption rehearsal on a fresh copy of the live trainer (264 / 264 = installer base) -> 261 / 261** (20:42, again 21:44 and 22:35-22:39 with the hardened installer, and 04:13-04:17 after hunts #15-#16); every out-of-scope setting refused with a clear message (test_scope.py 20 / 20); installer tests 28 / 28 (the live-folder guard under any spelling since the final hunt); HANDOFF.md | opus-r14b-fast-loader |
| 2 resumable relabel (`relabel2.py`) | DONE: 1M kill / resume proof PASSED (A uninterrupted vs B hard-exited twice: train / val / labels md5 identical); **the whole 1M with the LTO+PGO probe = the proof's files**; **frozen at sha256 e01caaf1...** (re-frozen 22:46 after shards started to record their settings; before that 56eef0a6... at 22:22 after the damaged-job harness: 29 findings, one silent - a lost run_config.json was re-created; earlier 88454db6... at 20:41 and 0a81dd5f... at 22:03 after a prepare fuzz finding); RELABEL_HANDOFF.md with measured costs (50M: 78.7 h at the whole-1M rate) and a 50M runbook on R8 v5 shards 001-057; 50M run not started (as asked) | logs/proof_finish.log, pgo_full_1M.log, chain_2030/ (suites 150 / 0 then, 154 / 0 after the 22:03 re-freeze, 155 / 0 after the 22:22 and 22:46 ones, in the worktree and fresh clones, 157 / 0 at 23:06 with verify_job.py, bridge PASS, probe builds from a fresh clone = the tested exes, R8 v5 end to end through fen2bin and hce_dump: the final freeze's output = the first freeze's, byte for byte) | opus-r14b-relabel |
| tools (Couns 19:46) | DONE: `opus_r14b/tools/` + `opus_r14b/checks/`, entry point `opus.sh`, skill forge-opus-tools; `checks/final_checks.sh` = the end-of-job check in one command | test_tools.sh 37 / 37 (04:24; the launcher's refusals added in hunt #15, six more tools' in the final hunt); engine tools on real builds; GPU baseline; verify chain / refreeze / hash sweep runs; final_checks.sh dry runs 22:56, 02:37 and 04:33, 8 / 8 steps | opus-r14b-status |
| P6 crfix 4b537823 (Couns ~20:57) | DONE: applied with patch -p1, rebuilt, P6 checks re-run, pushed | OFF = the corrected lock pins, WDL / DTZ 220 / 220, check50 20 / 20, fail-closed 9 / 9, CI 41515843128 green | opus-r13-p6-syzygy d1751ca1, 4bf626eb |

## Baseline and improvements (measured numbers only)
Baseline = what the two tasks asked for, as it stood when they were done: item 1 = candidate b5 (verified by 14:45);
item 2 = relabel2.py 5c88438f (the proof code) with the R13 probe ed76de96, prepare in one process, 19 exit-code tests.
| improvement | before (baseline) | after | how measured |
|---|---|---|---|
| relabel prepare speed | 5c88438f: 16.0 / 16.6 s per 200k rows (44.2M rows/h) | `--jobs 2`: 10.8 / 11.1 s (65.7M rows/h) = **1.49x**; `--jobs 1`: 16.7 / 17.0 s (0.97x: added input checks) | same 200k rows, order F J1 J2 J2 J1 F, rows.tsv identical in all six |
| relabel probe speed, 1 thread | R13 probe ed76de96 | LTO+PGO 08299f9f: **1.075x** (mean of 10 pair ratios, 95% CI 1.044-1.106; median 1.094); LTO only 1.053x (CI 1.009-1.097) | 10,000 / 10,000 answers identical; answers identical in all ABBA runs |
| relabel throughput, 2 workers on one core | R13: 662,337 / 663,485 rows/h | LTO+PGO: 687,266 / 694,693 rows/h = **1.042x** | 19,927 rows, order R P P R, labels md5 identical |
| 50M rows at 20k nodes, 2 workers (light crew load) | 75.4 h (R13) | 72.4 h (LTO+PGO) | rows / measured rate |
| the whole 1M proof sample with the LTO+PGO probe | the proof ran on the R13 probe | train / val / labels **byte-identical** to the proof's (all 999,921 labels); 635,344 rows/h through 94 min of real crew load -> **78.7 h for 50M** (the planning figure) | logs/pgo_full_1M.log |
| R8 v5 input (games run across shard files) | 5c88438f gives a game crossing a file two game ids (leak risk) | one game id (one input stream in name order) | test + real shards 271 / 272 |
| input / job safety | 19 tests | 157 PASS lines in test_relabel2.sh at 23:06 (155 at the 22:46 re-freeze; cases + reason checks): F1-F8, R17, R25, R27, R28, H2-x, H3-x, P-1, J-1..J-5 fixed with a test each; 300 damaged self-play files + 250 damaged JSONL files fuzzed: every one prepared or refused with file:line; 105 damaged-job runs (job_damage.py: published shards, manifests, rows.tsv, prepare.json, run_config.json, stray names): every one refused with exit 4 / 3 / 2 and a reason or clean exit 0 - on the 22:03 freeze 29 of them failed (one silently: a lost run_config.json was re-created), on the 22:22 freeze 3 (an edited run_config.json); the helpers around relabel2.py (sort_normalized, label_stats, probe_bench) with broken input in bug hunt #14: 36 of 54 calls wrong (one emptied an existing output file, `abba` passed changed answers with exit 0), all fixed, 66 / 66 cases; hunt #15: the remaining scripts refuse wrong arguments before any work and fail on a failed comparison, 77 / 77 | test_relabel2.sh, job_damage.py, test_helpers.py, RESULTS.md |
| disk rule of the PC (C: / D: >= 50 GB) | not enforced by the tool | `--min-free-gb` (default 50): prepare / assemble refuse, run stops before the shard that would cross it | quick checks; test cases |
| relabel output through the FPOS converters earlier jobs used | not checked | fen2bin carries the new labels 1,200 / 1,200; the whole 1M output: fen2bin 991,077 + 8,844 records = every row, 0 bad; hce_dump the same counts, 0 bad FEN, 0 clamped | conv_check, logs/conv_full_1M.txt |
| failures that explain themselves | a probe that died ended `run` with a bare traceback and no log line; the launcher of every tool returned 0 when a program could not start | `run` writes "run stop ... <error> (exit N)" to sessions.log; lowrun.ps1 exits 127 (missing program / redirect folder / stdin file; since hunt #15 also a bad CPU mask - it ran the program on every CPU - and an existing redirect target) | suite cases with a dead probe; 8 launcher cases |
| fast loader adoption | GPU_REQUEST.md only | HANDOFF.md: adapter path (`--npt-repo` + `--npt-extra --fast-loader`), live trainer = installer base (264 / 264 files), thread advice, distribution check; one-command acceptance check (261 / 261); installer `--loader-dll` copies the loader files | item 1 HANDOFF.md, tools/fl_acceptance.sh |
| works from a fresh clone | tools reached into other worktrees / scratch; a default clone (core.autocrlf=true) wrote CRLF and changed the documented hashes | own lowrun.ps1 copy; probe build exports the lock source from git and uses a committed training file; `opus_r14b/.gitattributes` keeps code LF (fresh clone: relabel2.py sha256 = the branch's); the verify chain's fresh-clone step found two more such bugs (C1 lock export, C2 robocopy), fixed | fresh-clone checks 20:33, 20:39-20:42, 21:44-21:48, 22:35-22:39 and 04:13-04:17: 0 failures (suites, probe builds = the tested exes, DLL = b5, adoption rehearsal 261 / 261) |
| regression caught by measuring | - | R27: a per-row `Path.resolve()` (76.7 us per call = 15.3 s per 200k rows) in the post-proof one-process prepare; the fix took it from 36.5 / 38.3 s to 17.9 / 18.1 s on the same 200k rows (2.05x, the same crew load: one BelowNormal job in both); output identical | logs/measure/resolvefix_check.log, post_chain.log |

## Item 1 - fast npt data loader (`opus_r14b/item1/`)
- Own code `fastloader/forge_fastloader.cpp|.py`, spec LOADER_SPEC.md, installer `tools/install_fast_loader.py` =
  `patches/0005-fast-loader-switch.patch` (default off), optional `patches/0006-seed-before-model-OPTIONAL.patch`.
- b5 DLL sha256 9eb29b7d134a73eb58d47b2ced38587ed450ffaf11fdfcb108898652cefcd935 (pc1 = pc2).
- Speed (advisory): loader-only ABBA 8.65x (median of 10 pair ratios; mean 8.64, 95% CI 8.58-8.69) on CPUs 2-3; a full 152.5M-position epoch through the fast
  loader alone in 29.8 s at 166 MB; CPU training 3.5x faster (64 batches 11.4 vs 40.2 min).
- Finding for Engine NNUE: `--seed` does not fix the initial weights (model built before seeding; torch 2.11 ROCm
  seeds per process from the clock).
- The GPU use it should raise, measured (keeper's HWiNFO log, `tools/gpu_util_stats.py`): the live npt line with the
  default loader, 2026-11-02 15:14-21:14: GPU Utilization mean 45.7 %, p50 48 %, >= 90 % in only 4.0 % of samples;
  hourly means 40-56 %. The trainer runs at Idle on 2-4 CPUs (the keeper sets the mask 0x3 / 0xF) and used 0.4-0.6
  cores at 21:19-21:22 on CPUs that were 86-90 % busy, mostly with heavier-class work - but with 10-14 % idle time
  left, so it was not purely CPU-starved (an early "starved" wording was corrected in hunt #5). On one logical CPU in
  the live thread setting the default loader
  costs 2.45 and the fast loader 0.34 CPU-us per kept position (7.19x, median of 10 pair ratios; mean 7.17, 95% CI 7.08-7.26): feeding the live line takes
  0.30-0.41 of a CPU with the default loader, 0.04-0.06 with the fast one. The GPU window must show the effect.
- Robustness (bug hunt #4): 371 damaged-file runs incl. a bounds-checked build: clean errors, no crash, no hang; one
  limit shared with the default loader (a cyclic stream over a file in which nothing passes the skip filter waits).
- Scope (bug hunt #7): `tools/test_scope.py` 20 / 20 - another feature set, two files or none, DDP with 2 ranks,
  filtered / wld_filtered / simple-eval skipping, a missing skip-config field, a missing binpack / DLL / loader file:
  each refused with a message that names it; a planted removal of the DDP check is caught.
- Installer (bug hunt #6): a misspelt `--check` used to install (H6-1), a missing folder or a non-UTF-8 file ended in
  a traceback (H6-2), a real install into the live trainer folder was not refused (H6-3): all fixed;
  `tools/test_installer.sh` 25 / 25 then (28 / 28 since the final hunt: the guard now also catches the `\\?\` spelling), with the live-folder guard tested on a stand-in (H6-4); the patched files are
  byte-identical to the earlier rehearsal's, and the fresh-clone adoption rehearsal passed again (22:35-22:39).
- Documents against the code (bug hunt #16, 03:25-03:35): every option of the GPU_REQUEST command was compared with the
  live trainer's command line (s33): all accepted, only the intended ones differ; HANDOFF's switch, startup lines,
  adapter options and thread rule, lm_run.sh's dry-run settings and LOADER_SPEC's names match the code. Fixed:
  **the acceptance check's verdict (`fl_dataset_equal.py --compare`) passed two junk or empty dumps with exit 0** (now
  a dump must be complete); the equality / distribution tools refused an existing `--out` only after the whole run;
  fl_abba.py made its folder before failing on bad input; tracebacks; three document lines (HANDOFF 3b's 3rd argument
  is a DLL file, the skill's missing `--data`, GPU_REQUEST's queue facts and two preconditions). `tools/test_cli.py`
  34 / 34; recorded comparisons and a fresh 2-batch pair unchanged.
- The live-folder guard under other spellings (final bug hunt, 04:28-04:31): **the installer's guard compared paths
  and missed the `\\?\F:\opus_scratch\r6\nnue-pytorch-amd` spelling of the live trainer folder** - shown on a stand-in,
  where that spelling installed (exit 0, files patched) while the plain one was refused. Fixed: file identity
  (`os.path.samefile`) first, then the path comparison; `tools/test_installer.sh` 28 / 28 with three spelling cases.
  The live folder was never sent an install; only `--check` reads it.

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
- Damaged job state (bug hunt #6 and the advisor's read at 22:29): `job_damage.py`, 35 kinds of damage x run /
  assemble / status. J-1: a lost run_config.json was silently re-created from the command line (a resume with other
  settings would have mixed labels); J-2..J-4: tracebacks instead of exit 4 with the file named, `status` crashes;
  J-5: shards did not record their settings, so an edited run_config.json passed. All fixed (shards now record node
  limit / hash / probe sha256), 105 / 105 runs clean; the 1M proof's older shards still resume and assemble (bridge).
- End to end on R8 v5 with the final freeze (22:53): prepare -> run -> assemble -> fen2bin + hce_dump, 11 / 11 checks;
  the output files are byte-identical to the first freeze's at 20:30.
- The 50M runbook's commands as written (with `--rows 3000`, 23:00) on the final freeze: every step exit 0, run at
  634,842 rows/h. `verify_job.py JOB --convert OUT`: the output checks in one read-only command (hashes, rows, every
  label row once and in order, splits, shards, settings, fen2bin + hce_dump); whole 1M job all PASS in 1.7 s,
  planted damage 6 / 6 caught; suite 157 / 0 with its two cases.
- The helpers around relabel2.py with broken input (bug hunt #14, 02:08-02:20): 36 of 54 calls were wrong.
  `probe_bench.py run` emptied an existing `--out` file before the probe ran (Start-Process empties its redirect
  targets), `abba` reported changed answers but exited 0, `compare` passed two empty files or failed answers,
  sort_normalized.py wrote an empty file for an empty input and let `--min-free-ram-gb nan` switch its RAM check off,
  label_stats.py crashed on valid input whose new scores are all equal, and a dozen damaged inputs gave tracebacks.
  All fixed: one line naming the file and line, exit 2 (1 = answers differ or failed), nothing written, no output
  overwritten. `test_helpers.py` 66 / 66 in the worktree and a fresh clone; valid input gives the same results as
  before (Astra's chain sorted byte for byte, the 1M label statistics, the 500 reference requests, the R13 probe's
  answers on 5 positions).
- Files overwritten and checks that pass on failure (bug hunt #15, 02:25-02:34, all three branches): **the shared
  launcher lowrun.ps1, given a bad CPU mask (`xyz`, `0x0`), printed an exception and then ran the program on every
  CPU with exit 0**, and it emptied an existing `-Out` / `-Err` file (the root of the hunt-#14 finding). Both refused
  now (exit 127, program not started). Three check scripts printed a failed comparison but exited 0 (item 1
  `b5_checks.sh`, item 2 `prove_resume.sh finish` and `measure_rates.sh`); two started work before refusing a wrong
  argument (`measure_rates.sh` wrote its 14 MB input, `bridge_check.sh` started the 1M-row prepare); fn_diff.py
  gave tracebacks. All fixed; the recorded runs of these scripts had no failure (checked in their logs).
  test_tools.sh 31 / 31, test_helpers.py 77 / 77.

## Tools for Couns and Opus (Couns 19:46: "create tools scripts that you and i can use"; 19:47-21:17 by the commits)
`opus_r14b/tools/` on opus-r14b-status, skill forge-opus-tools, one entry point `bash opus_r14b/tools/opus.sh help`:
status (job + PC in one look), lint (doc_lint.py: control bytes, CRLF, mojibake, eaten Windows backslashes, broken
GitHub tables, dead links - it found a broken RESULTS table on its first run and a path with lost backslashes in the
memory index), abba (palindromic A/B timing of any two commands with identity check, t-CI and load capture), engine
(fresh export + lock-recipe build + bench / perft pins of any engine ref), bisect (first commit that changed bench
nodes, building each candidate from a `git archive` export), time (spans and pauses from commit times), load, test
(test_tools.sh, 37 checks), gpu (gpu_util_stats.py: GPU utilisation from the keeper's HWiNFO log). `opus_r14b/checks/`
holds the verify chain, the fresh-clone checks, refreeze.sh, the hash sweep, the file index, the R8 v5 end-to-end
check and `final_checks.sh` (all end-of-job checks in one command, ~1 minute). Validated on real data:
engine builds of the lock and an R12 branch (ALL OK), a planted-change bisect (found), the frozen relabel code
(refreeze 0 failures). Own review R14B-T-1 fixed 5 defects in the new tools, hunt #4 one more (TOOLS.md).

## Review milestones (all after 13:45 are self-reviews, NOT independent)
R14B-I1-1 (sub-agent, before the no-sub-agent rule), R14B-I1-2, R14B-I2-1 (7 findings), R14B-I2-2 (F8, R17, R25),
R14B-I2-3 (handoff exe location), R14B-T-1 (tools); hourly bug hunts #1 19:05, #2 19:41, #3 20:04 (relabel2 `run`
now logs a probe failure to sessions.log and lowers its priority before hashing; item 1 trainer path checked for
use-after-release: none; with the advisor's read: the stop line's exit code, the CPU mask range), #4 20:50 (the fast
loader fuzzed with 371 damaged files: no crash / hang; engine_bisect needs GOOD on BAD's first-parent line), #5 21:31
(the "starved" wording corrected; doc_lint table rule, 11 broken tables fixed), prepare fuzz 21:56 (P-1: input score
range), #6 22:09-22:27 (damaged job state J-1..J-4; installer H6-1..H6-3), advisor read 22:29 (H6-4, J-5), #7
22:49-22:52 (fast loader scope: no code finding), #8 23:10-23:11 (the DLL's lifecycle: no reachable race in the
trainer path; threading contract in LOADER_SPEC.md), #9 23:19-23:20 (the trainer's dataset calls: all covered), #10 23:20-23:21
(relabel paths with spaces end to end: all exit 0), claims audit 23:21-23:24 (report numbers -> raw logs), #11
00:08-00:09 (kept exes in place; one wrong note of mine corrected: the s31 line differs from the request only in the
seed), #12 00:25 (relabel documents vs the code: consistent), #13 01:08-01:10 (tools with wrong
arguments: two fixed - a bad CPU mask exited 0, a misspelt status option was ignored), #14 02:08-02:20 (item 2's
helpers with broken input: H14-1..H14-10 fixed, one of them an output file emptied by `probe_bench.py run`), #15
02:25-02:34 (files overwritten, checks that pass on failure: H15-1..H15-7 fixed, among them the launcher running a
program on every CPU when given a bad mask), #16 03:25-03:35 (item 1's documents against its code, its tools with
wrong arguments: H16-1..H16-7 fixed, among them the acceptance compare passing junk); details in each RESULTS.md and
TOOLS.md. Final 1-hour bug hunt from 04:13 (TOOLS.md): F-1..F-8 fixed - among them the installer's live-folder guard
missing the `\\?\` spelling of the live trainer folder (F-8) and pc_gate.ps1 passing a CPU that does not exist (F-1);
the fresh-clone checks again with 0 failures; a second claims audit.

## Time (from the commits: `tools/commit_span.py`, as of 04:36)
315 distinct commits on the four branches between 12:19 and 04:32 (16h12): opus-r14b-status 124, fast-loader 82,
relabel 107, opus-r13-p6-syzygy 2 (the P6 crfix). Six pauses over 30 minutes with no commit on any branch, 5h18 in
all: 16:28-17:21 while the proof ran, the other five after 23:25 - the waits between the scheduled hunts. Most commits
per hour: 19:00-23:00 (29-57). What the time did not buy: the GPU measurement of item 1 (no window granted), any
independent review (no sub-agents after 13:45: every review is a self-review), the 50M relabel (not asked for), any
Elo or training-quality claim.

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
- H6-4: my first `test_installer.sh` checked the live-folder guard by sending a real install command to the live
  trainer folder `F:\opus_scratch\r6\nnue-pytorch-amd` (22:25 and 22:26): the guard refused both and the live files
  were unchanged (sha256 before = after = the installer's base manifest at 22:34), but a broken guard would have
  patched the live trainer. The test now uses a stand-in folder; only the read-only `--check` reads the live folder.
- Times written ahead of the clock again in drafts (22:25, 22:40, 22:53 written at 22:23, 22:37, 22:51): corrected
  from `date` before or right after the commit; every record carries the clock time it was checked against.
- 22:29: the trainer's CPU mask changed from 0x3 to 0xF (the keeper's usual trainer pair) and at 22:34 a new trainer
  process started (pid 13960 -> 11328), not Opus's doing (watcher log). Opus's later checks on CPUs 2-3 share those
  CPUs with it; they are short (refreeze ~6 min, final checks ~1 min) and the long-running parts run at Idle.
- 23:09: the session's permission check stopped a CPU dry run of the GPU command's recipe (`tools/lm_run.sh fast`,
  4 training steps on CPUs 2-3) before it started ("Interfere With Workloads"); not worked around, nothing ran. From
  then on Opus kept CPU-heavy work off CPUs 2-3 while the trainer shares them (checks of ~1 minute, desk reviews);
  the dry run is optional pre-check 4 in GPU_REQUEST.md for a time when no npt line trains. From 22:59 the trainer
  was back on 0x3 (CPUs 0-1, the watcher log), so the later checks on CPUs 2-3 - the final_checks.sh dry run 02:37
  (~1 minute), the fresh-clone checks 04:13-04:17 (~3.5 minutes, BelowNormal / Idle) - did not share its CPUs.
- 04:13: D: had 48.88 GB free, under Couns's 50 GB floor - not from Opus's work (its D:\o14b has been 3.7 GB since
  22:07, tonight's scratch is on C:, D: got only git commits); 51.97 GB again at 04:22. Nothing was moved or deleted.

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
- GPU window for item 1 (GPU_REQUEST.md; optional pre-check 4 = a CPU dry run of the recipe while no npt line
  trains); Engine NNUE decides on `--fast-loader` and patch 0006.
- Engine NNUE decides on the 50M relabel (inputs, node count, probe); RELABEL_HANDOFF.md has commands and costs.
- R15: start only after this report's final version; use the corrected pins; keep the four exes (P6 crfix: done above).
- Crew: the npt trainer runs at Idle on its own mask (0x3 / 0xF, set by the keeper) and used 0.4-0.6 cores of its two
  CPUs at 21:19-21:22; those CPUs were 86-90 % busy (21:32), mostly with heavier-class work such as BelowNormal crew
  jobs with affinity on all CPUs (Astra's audit_forge_admission.py, ~1 core each), with 10-14 % idle left; GPU 31-50 %
  in the same minutes. Keeping such jobs off the trainer's CPUs, or another priority class for the
  trainer, is the crew's decision (item 1 RESULTS; the overnight watcher log has the series).
- Crew: free disk space is thin - D: dipped under its 50 GB floor at 04:13 (48.88 GB; 51.97 GB at 04:22) and F: had
  44.9 GB at 04:17 (under its 50 GB reserve); neither from Opus's work.
- Not re-run after their last edit (honest record): item 1 `tools/b5_checks.sh` (hunt #15: exit code) and
  `checks/verify_chain.sh` (final hunt F-7: calls the committed fresh-clone script). Both pass `bash -n`, and what
  they call ran clean afterwards (fresh-clone checks 04:13-04:17, the item tests in final_checks.sh), but the two
  scripts themselves have not run end to end since the change: their recorded results are from the versions before
  (b5_checks 14:23, the chain 20:29-20:39). A full run takes minutes of CPU on CPUs 2-3 (the chain includes a 1M-row
  prepare), so it was left to a quiet time.
- Overnight watcher (item 1 RESULTS): with other work crowding its two CPUs the trainer's GPU use rose with its CPU
  share; with free CPUs it still stayed near 40 %. CPU competition explains part of the low GPU use, not all of it -
  the GPU window decides.
