# Opus R14-B final report (Couns's job, 2026-11-02 12:05 -> 06:00 Nov 3 PC clock) - INTERIM (updated 20:16), final at the end

Window: 15 hours at the start; Couns at ~19:15: work to 06:00, a 20-minute bug hunt every hour (every finding
fixed), make sure everything works in Forge, a 1-hour bug hunt at the end; no sub-agents.

UNPROVEN everywhere: no Elo or training-quality claims; Engine NNUE / QA decide. Nothing of the live npt line, the
queue, gates, self-play or crew files was touched. Own work ran BelowNormal / Idle on CPUs 2-3 (deviations below).

## Summary
| item | state | key evidence | branch / head |
|---|---|---|---|
| 1 fast npt loader (`--fast-loader`, default off) | DONE except the GPU window (requested in GPU_REQUEST.md, not granted: the npt queue holds the GPU to Nov 8) | batches bit-identical to the old loader's `--num-workers 1` stream (1,000 / 1,000 + validation, 24-config matrix, 3,100 batches past a wrap, trainer path 261 / 261); exact CPU loss match; loader ABBA 8.65x; distribution vs the live w4 layout: every total-variation distance < 0.001; HANDOFF.md | opus-r14b-fast-loader |
| 2 resumable relabel (`relabel2.py`) | DONE: 1M kill / resume proof PASSED (A uninterrupted vs B hard-exited twice: train / val / labels md5 identical); RELABEL_HANDOFF.md with measured costs; 50M run not started (as asked) | logs/proof_finish.log; bridge_check.log; 75 / 75 tests | opus-r14b-relabel |

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
| input / job safety | 19 tests | 150 PASS lines in test_relabel2.sh at 20:30 (cases + reason checks): F1-F8, R17, R25, R27, R28, H2-x, H3-x fixed with a test each; every refusal also checks its reason | test_relabel2.sh, RESULTS.md |
| disk rule of the PC (C: / D: >= 50 GB) | not enforced by the tool | `--min-free-gb` (default 50): prepare / assemble refuse, run stops before the shard that would cross it | quick checks; test cases |
| relabel output through the FPOS converters earlier jobs used | not checked | fen2bin carries the new labels 1,200 / 1,200; the whole 1M output: fen2bin 991,077 + 8,844 records = every row, 0 bad; hce_dump the same counts, 0 bad FEN, 0 clamped | conv_check, logs/conv_full_1M.txt |
| failures that explain themselves | a probe that died ended `run` with a bare traceback and no log line; the launcher of every tool returned 0 when a program could not start | `run` writes "run stop ... <error> (exit N)" to sessions.log; lowrun.ps1 exits 127 (missing program / redirect folder / stdin file) | suite cases with a dead probe; 8 launcher cases |
| fast loader adoption | GPU_REQUEST.md only | HANDOFF.md: adapter path (`--npt-repo` + `--npt-extra --fast-loader`), live trainer = installer base (264 / 264 files), thread advice, distribution check; one-command acceptance check (261 / 261); installer `--loader-dll` copies the loader files | item 1 HANDOFF.md, tools/fl_acceptance.sh |
| works from a fresh clone | tools reached into other worktrees / scratch; a default clone (core.autocrlf=true) wrote CRLF and changed the documented hashes | own lowrun.ps1 copy; probe build exports the lock source from git and uses a committed training file; `opus_r14b/.gitattributes` keeps code LF (fresh clone: relabel2.py sha256 = the branch's) | fresh clone checks (more after the PGO run) |
| regression caught by measuring | - | R27: a per-row `Path.resolve()` (76.7 us per call = 15.3 s per 200k rows) in the post-proof one-process prepare; the fix took it from 36.5 / 38.3 s to 17.9 / 18.1 s on the same 200k rows (2.05x, the same crew load: one BelowNormal job in both); output identical | logs/measure/resolvefix_check.log, post_chain.log |

## Item 1 - fast npt data loader (`opus_r14b/item1/`)
- Own code `fastloader/forge_fastloader.cpp|.py`, spec LOADER_SPEC.md, installer `tools/install_fast_loader.py` =
  `patches/0005-fast-loader-switch.patch` (default off), optional `patches/0006-seed-before-model-OPTIONAL.patch`.
- b5 DLL sha256 9eb29b7d134a73eb58d47b2ced38587ed450ffaf11fdfcb108898652cefcd935 (pc1 = pc2).
- Speed (advisory): loader-only ABBA 8.65x (CI 8.58-8.69) on CPUs 2-3; a full 152.5M-position epoch through the fast
  loader alone in 29.8 s at 166 MB; CPU training 3.5x faster (64 batches 11.4 vs 40.2 min).
- Finding for Engine NNUE: `--seed` does not fix the initial weights (model built before seeding; torch 2.11 ROCm
  seeds per process from the clock).

## Item 2 - resumable relabel (`opus_r14b/item2/`)
- relabel2.py (prepare / run / assemble / status; freeze candidate 88454db6... in the verify chain since 20:29), tests, proof driver, bridge, measurement scripts, probe
  LTO / PGO build + bench, label statistics; skill forge-relabel-job.
- Proof: 999,921 rows in 10,880 games (val 99 games / 8,844 rows, overlap 0); B's hard exits at 14:48:59 (shard 14)
  and 15:34:20 (shard 36), interrupted attempts kept, no orphaned probe; md5 train 6e9e4e5a..., val 8e639f41...,
  labels 2614e82d... for both.

## Tools for Couns and Opus (Couns 19:46: "create tools scripts that you and i can use"; block 19:47-21:47)
`opus_r14b/tools/` on opus-r14b-status, skill forge-opus-tools, one entry point `bash opus_r14b/tools/opus.sh help`:
status (job + PC in one look), lint (doc_lint.py: control bytes, CRLF, mojibake, eaten Windows backslashes, broken
GitHub tables, dead links - it found a broken RESULTS table on its first run and a path with lost backslashes in the
memory index), abba (palindromic A/B timing of any two commands with identity check, t-CI and load capture), engine
(fresh export + lock-recipe build + bench / perft pins of any engine ref), bisect (first commit that changed bench
nodes, building each candidate from a `git archive` export), time (spans and pauses from commit times), load, test
(test_tools.sh). Own review R14B-T-1 fixed 5 defects in the new tools (TOOLS.md).

## Review milestones (all after 13:45 are self-reviews, NOT independent)
R14B-I1-1 (sub-agent, before the no-sub-agent rule), R14B-I1-2, R14B-I2-1 (7 findings), R14B-I2-2 (F8, R17, R25),
R14B-I2-3 (handoff exe location), R14B-T-1 (tools); hourly bug hunts #1 19:05, #2 19:41, #3 20:04 (relabel2 `run`
now logs a probe failure to sessions.log and lowers its priority before hashing; item 1 trainer path checked for
use-after-release: none); details in each RESULTS.md. Final 1-hour bug hunt: 05:00-06:00.

## Deviations and incidents (honest record)
- 15:22-16:27: dev test runs ran as a third Idle process next to the two proof probes on CPUs 2-3 (over the "<= 2
  threads" rule, inside the 2-CPU mask).
- Item 1 (earlier): an orphaned 3-minute CPU run after a TaskStop (see item 1 RESULTS).
- Two committed text files had backslashes turned into control characters by a heredoc + inline Python (TOOLS.md,
  memory file); fixed, all R14-B files scanned clean.
- CPUs 2-3 are one physical core (SMT): every rate is per that core; crew BelowNormal jobs slowed Idle work at times
  (load samples logged next to each rate).

## Owner items
- GPU window for item 1 (GPU_REQUEST.md); Engine NNUE decides on `--fast-loader` and patch 0006.
- Engine NNUE decides on the 50M relabel (inputs, node count, probe); RELABEL_HANDOFF.md has commands and costs.
