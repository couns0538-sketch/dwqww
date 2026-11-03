# R14-B item 2 - resumable relabel with original FENs and a game-level validation split - 1M KILL / RESUME PROOF PASSED (md5 identical); UNPROVEN as training data

Branch `opus-r14b-relabel` (from `opus-r13-p5-nnue-data`). Own code `relabel2.py`; unchanged copies of R13's probe
client `forge_probe.py` (sha256 980c20cc...) and Astra's `astra/records.py` (from astra-r8-datafilter 8ebcf115,
sha256 444e854e...). Labels come from the R13 probe `C:\o13\p5\forge_data_probe.exe` (sha256 ed76de96..., lock
source d4f4312; transposition table, histories and caches cleared before every search). Engine NNUE decides whether
any of these labels are used; nothing here is a strength claim. The 50M run is not started.

**State (2026-11-02 21:52 PC clock; details in the dated sections below, the newest at the end):** relabel2.py
FROZEN at sha256 88454db6e17cf4e72cfa651ea253c9fc8599d1317a553d25d14dd96685570545 (after bug hunt 3 and the verify
chain). Test suite: 150 PASS / 0 FAIL in the worktree and in fresh clones (the 19 / 19 below is the afternoon's
first version). The 1M kill / resume proof (frozen proof code 5c88438f) and the bridge tie the frozen code to it; the
whole 1M sample with the LTO+PGO probe gave the proof's files byte for byte; Forge's fen2bin / hce_dump take all 1M
rows. Probe builds from a fresh clone reproduce the tested exes. 50M: ~79 h on CPUs 2-3 with 2 workers (the whole-1M
rate under load); runbook for R8 v5 shards 001-057 in RELABEL_HANDOFF.md. `FILES.txt` + `SHA256SUMS` index this
folder (`sha256sum -c --quiet SHA256SUMS` after a checkout).

## What R13 had and what is new
| R13 / R14 P5 (`opus_r13/p5/`) | R14-B `relabel2.py` |
|---|---|
| input .pos + FEN sidecar (sidecar fix proven on 1,000 rows) | input = self-play text (`FEN \| stm cp \| white result`) or Astra normalized JSONL: the original FEN with castling / en passant / clocks is the input itself |
| shards redone into `_r<attempt>` dirs; no kill / resume proof | `.part.N` shard dirs published by one rename after fsynced labels + manifest + summary; resume re-hashes every published shard; interrupted attempts kept |
| no game ids; split by position (Astra's converter) | game id per input file and game (leak-safe rule), split by sha256(salt, game id) |
| one slice per call | `prepare` / `run` / `assemble` / `status`; exit codes 2 bad input, 3 configuration differs, 4 integrity |

## Checks
| check | result | evidence |
|---|---|---|
| prepare on 2,000 rows: games found | 1,986 rows in 21 whole games, lengths 40-147, every game starts at ply 8-11 (the opening-book plies) | smoke, 13:20 |
| tiny-budget guard: 500 nodes, a position that cannot finish depth 1 | the run stops (not an exact searched label), assemble refuses (exit 4) | smoke |
| mini kill / resume (1,986 rows, 5,000 nodes, shards of 300; hard exit during start-up, resume) | md5 of train.txt / val.txt / labels.tsv identical to the uninterrupted job | smoke |
| bad input / configuration / integrity exit codes | **19 / 19 PASS**: 8 bad inputs (FEN fields, piece letter, score, result token, missing field, empty line, terminal position, no result) -> exit 2 naming the row, no rows.tsv published; missing file -> 2; existing job -> 3; changed nodes / shard size / run id -> 3; unfinished assemble, tampered shard, tampered rows.tsv -> 4; `--drop-terminal` -> 0 | logs/test_relabel2.log |
| Astra chain (normalized input): Astra's `convert_forge.py --keep-result` (unchanged code; in the scratch copy only its output root moved from Astra's `C:/astra8_data` to `D:/o14b/r2/nt`) on 3,000 self-play lines -> 2,810 rows (190 > 30 pieces dropped), shuffled, split by position -> `sort_normalized.py` -> `prepare --normalized` -> run (5k nodes) -> assemble | unsorted input refused (exit 2, "must be in source order"); sorted: 2,810 rows in 32 games, the same game partition as `prepare --selfplay` on the raw file over all 2,810 common rows (0 disagreements); run + assemble OK | `D:/o14b/r2/nt` |
| found by that test, fixed after the proof (relabel2.py is frozen while the proof runs): for normalized input rows.tsv records the JSONL line instead of the record's own source / source_row, and a change of the record's source is not a game boundary by itself (it was in the first, non-streaming version) | DONE in the post-proof version (origins list in prepare.json; promoted 17:55 after the bridge check) | dev tests, logs/test_relabel2_dev_final.log |
| 1M sample prepared twice (jobs A and B, `prove_resume.sh prepare`): `forge_selfplay_001.txt` (466,506 lines) + the start of `_002.txt`, cut at a game boundary | **999,921 rows in 10,880 whole games**; train 991,077 rows / 10,781 games, validation 8,844 rows / 99 games (1 % of games); game length 2-276 (median 85, p99 227); every game starts at ply 8-15 (no fragment); 0 terminal positions; rows.tsv A = B byte for byte (sha256 eefb1662...); 21 min wall for both at Idle next to BelowNormal training | `D:\o14b\r2\proof\job{A,B}\prepare.json` |
| 1,000,000-row proof: A uninterrupted vs B hard-killed twice and resumed. Both kills are self-inflicted hard exits (os._exit from a watchdog thread at an arbitrary moment: no cleanup, no flush), because the session permissions block terminating processes and stopping a background task ends only its outer shell. Code frozen for the proof: relabel2.py sha256 5c88438f... (in both jobs' run_config.json) | **PASS: md5 of train.txt, val.txt and labels.tsv IDENTICAL for A and B** (train.txt 6e9e4e5abbf9e1fa86dc33823aef7903, val.txt 8e639f41c64dbe96581b1d6a3f4cf675, labels.tsv 2614e82d55bc5e9572c24d3900a8810a); both assembles checked every row id exactly once and in order (999,921 = prepared; no duplicate, no drop), game ids disjoint across the splits (train 991,077 rows / 10,781 games, val 8,844 / 99, overlap 0), counts = prepare.json. A (CPU 2, Idle, 1 probe): 14:23:26-17:36:09, one session. B (CPU 3): exit 1 = 137 at 14:48:59 inside shard 14 (`shard_00014.part.1` kept, redone as `.part.2`); exit 2 = 137 at 15:34:20 inside shard 36 (`shard_00036.part.1` kept); after each exit only the other run's probe and the new session's probe were alive (no orphan); session 3 15:34:20-17:43:28 labelled the remaining 639,921 rows. `finish` ran with relabel2.py still 5c88438f (re-hashed at 17:43; also in both run_config.json) | `D:/o14b/r2/proof`, logs/proof_finish.log, runA.log / runB.log, job sessions.log |
| RELABEL_HANDOFF.md (positions / hour, 50M cost) | measured numbers after the proof: see the measurement section below | - |

## Review milestone R14B-I2-1 (15:15-15:25; structured self-review, NOT independent - no sub-agents after 13:45)
Reviewed: relabel2.py (the frozen proof copy, sha256 5c88438f) line by line, Astra's records.py validation, the probe
client's lifecycle, test_relabel2.sh and the proof driver. The frozen copy stays unchanged until the proof is assembled;
every fix is in the dev copy `D:\o14b\r2\dev\relabel2.py` (sha256 b9878a40...) and in
`patches/post_proof_changes.patch` (which also holds the origin fix from the Astra-chain test and the tool-hash pin).
| # | severity | finding | fix (dev copy) | test (dev test script) |
|---|---|---|---|---|
| F1 | medium | assemble renamed final.part.N to final and only then wrote MANIFEST.json: a stop in between leaves final/ without a manifest, and assemble refuses to run again (final exists) | MANIFEST.json is written inside final.part.N; one rename publishes data + manifest | manifest_published_with_data, no_final_part_left, assemble_again (3) |
| F2 | medium (split leak) | the same input file given twice (or a byte-identical copy) gets new game ids, so its games can land in train AND val | every input once by resolved path and by sha256, else exit 2 | prepare_same_file_twice, prepare_same_content_twice (2) |
| F3 | low | an input that grows while prepare reads it (the self-play file still being written) is recorded with a hash that does not describe the rows read | inputs hashed before and after reading; a change -> exit 2, nothing published | prepare_input_changed (2) + nothing_published |
| F4 | low | a FEN with a tab between fields passes Astra's validation (python-chess splits on any whitespace) and would shift rows.tsv columns; it failed only later, in run | FEN must be printable ASCII -> else exit 2 in prepare | prepare_bad_tab (2) |
| F5 | low | two run sessions on one job at once label the same shard (the second one crashes at publish) | job.lock held with an OS lock by prepare / run / assemble (released by the OS on any exit, never deleted) -> exit 3 | run_busy_job (3, message checked) |
| F6 | low | out-of-range options (shard size 0, val ppm > 1e6, bad --until, missing probe, not a job) ended in a traceback or failed late | checked before anything starts -> exit 2 | run_shard_size_zero, run_bad_until, run_missing_probe, run_not_a_job, prepare_val_ppm_range (2) |
| F7 | low | normalized input order was checked per file: two files could repeat a (source, source_row) | the order check runs across all files | prepare_normalized_overlap (2); two ordered files = one file (rows.tsv cmp) |
- Dev test script: **48 / 48 PASS** (logs/test_relabel2_dev_R14B-I2-1.log; 15:22-15:23 at Idle on CPUs 2-3), incl. a
  mini kill / resume (1,200 rows, 20k nodes, hard exit after 5 s inside shard 4, resume, assemble): train.txt, val.txt and
  labels.tsv byte-identical to the uninterrupted job.
- Not changed (judged fine): game-boundary rule (merging neighbours is leak-safe), label checks in label_shard, resume
  re-hash of published shards, status.json written by atomic replace (own status file).
- Open: game ids are defined per job (`s<origin>g<n>`): prepare a whole dataset in one job; never merge the outputs of two
  jobs that share an input file (written into RELABEL_HANDOFF.md).

## Usability and cost checks (15:30-15:35, while the proof runs)
| check | result | evidence |
|---|---|---|
| the FPOS converter earlier jobs used (sha256 24cb2e78...; not checked against the live supervisor's) takes the output: `F:\opus_scratch\rescore_d8\bin\fen2bin.exe in.txt out.pos` (the self-play text -> FPOS tool) on `final/train.txt` of the dev test job (1,200 rows, 20k-node labels) | `lines=1200 records=1200 bad=0`; in the .pos (FPOS: 16-byte header, 32-byte boards, int16 scores, meta) the score column equals the new labels 1,200 / 1,200 (1,180 of them differ from the old score), side to move 1,200 / 1,200, result 1,200 / 1,200 (tokens `1.0` / `0.0` / `0.5` kept as in the self-play file) | D:\o14b\r2\conv_check |
| would a per-job label cache (search each distinct FEN once) save searches? | **no**: the 1M sample has 999,921 distinct full FENs in 999,921 rows (0 duplicates, also 0 when the clocks are ignored): the self-play pipeline already deduplicates, so the idea was dropped | count over proof jobA/rows.tsv |

## Improvement in the dev copy: prepare with two checking processes (`prepare --jobs 2`, 15:35-15:40)
- Why: prepare checks every row with python-chess (Astra's records.py builds and validates a board, relabel2 builds
  a second one for the legal-move test); 1M rows took ~10.5 min per job at Idle next to the trainer, so a 50M job
  needs hours of prepare before the first label. `--jobs 2` (default 1) hands blocks of 4,096 self-play lines to two
  spawned worker processes (Idle and the CPU mask are inherited) that run the same parse_line + check_row code; this
  process keeps the order, the counters, the origins and the game rule, with at most 2 * jobs + 1 blocks in flight.
  `--normalized` input stays single-process (its source-order check needs the global order); `--jobs` > 2 is refused.
- Dev test script (logs/test_relabel2_dev_jobs2.log): **67 / 67 PASS**: rows.tsv of --jobs 2 = --jobs 1 for a whole
  file, a `--rows` cut and 30,000 lines (8 blocks); bad rows give the same error text naming the same row (4 kinds);
  normalized input / 3 jobs refused (exit 2); all earlier cases unchanged.
- Speed and the 1M check (rows.tsv = the proof's eefb1662... with --jobs 1 and --jobs 2) follow after the proof:
  `measure_rates.sh prepare` (order 1 2 2 1) and `bridge_check.sh`. Dev copy sha256 1af5d768...;
  everything in `patches/post_proof_changes.patch`.

## Finding F8 (15:42, high for R8 v5 data): games run across R8 v5 shard files - fixed in the dev copy
- R8 v5 self-play (`selfplay_out_r8v5_20261029`, the live pipeline) writes fixed 1M-position shards: shard 271 ends
  with `8/3p4/3k4/8/1PP5/2K5/4b3/8 b - - 12 57` and shard 272 continues the same game with `... w - - 13 58`. The
  frozen relabel2.py starts a new game at every input-file change, so such a game would get two game ids and its two
  halves could land in train and val (a leak). The old `selfplay_out` files used in the proof end and start at game
  boundaries (001 ends at move 99 of a game, 002 starts at move 5), so the proof is not affected.
- Fix (dev copy): all inputs are one stream in the given order and only the game rule splits games (a game takes the
  origin of its first row; rows.tsv keeps each row's own origin and line); `--selfplay` files must be given in name
  order (= the order they were written), else exit 2.
- Tests (dev script, logs/test_relabel2_dev_straddle.log): **73 / 73 PASS**, new: good.txt cut inside its first game
  into two files -> the same game partition as the whole file, rows 29 / 30 (the two sides of the cut) one game id,
  --jobs 2 identical; the two files in the wrong order -> exit 2.
- Real data (dev copy): the last 5,000 rows of `forge_selfplay_fast_271.dedup.txt` + the first 5,000 of `_272` ->
  10,000 rows in 117 games, the game across the cut is one id (`s0g57`: row 4999 = origin 0 line 5000, row 5000 =
  origin 1 line 1), games start at ply 8-16 (median 8). C:\o14b\r2\r8v5chk.

## What the 1M proof covers in the post-proof code (written before the bridge runs)
- The proof ran relabel2.py 5c88438f. The code that ships after it differs, so the link is shown, not assumed:
  `fn_diff.py` (logs/fn_diff_frozen_vs_post_proof.txt, re-made at promotion) compares the two function by function.
  The labelling and resume path is **identical source**: `label_shard`, `read_shard_rows`, `row_offsets`,
  `verify_shard`, `load_prepare`, `write_new`, `append_log`, `file_hash`, `lower_priority`, `new_game`,
  `board_stats`. At promotion (17:55) `cmd_run` differed only by the job lock, the tool-hash pin and two log lines;
  since 19:15-19:27 its shard loop also has the disk-floor check before each shard and publishes through
  `move_retry` (the same rename, retried on a transient PermissionError), and `write_status` retries / skips a locked
  status file. `cmd_assemble` gains the lock, writes the manifest before the rename and checks the disk floor.
  `cmd_prepare` / `iter_rows` changed (input checks, one input stream, `--jobs 2`). (Updated 19:40 after the advisor
  pointed out that the earlier wording had gone stale; the diff is re-made at the code freeze.)
- What the bridge proves (`bridge_check.sh`, after `finish`): prepare of the proof's sample with the post-proof code
  gives the proof's rows.tsv byte for byte with `--jobs 1` and `--jobs 2`; `run --accept-new-tool` re-verifies all
  100 published shards of a copy of job A; `assemble` on that copy gives job A's train.txt / val.txt / labels.tsv.
- What the dev tests prove on the post-proof code itself: the mini kill / resume (1,200 rows, 20k nodes, a hard exit
  inside a shard) gives byte-identical final files, plus every exit-code case.
- Thread-budget note (honest record): the dev test runs at 15:22, 15:38, 15:43 and from 15:48 ran as a third Idle
  process on CPUs 2-3 next to the two proof probes (inside the 2-CPU mask, but three processes, over the "<= 2
  threads" rule); nothing further CPU-bound is started until the proof ends.

## R17 (16:00, review R14B-I2-2 in progress): only inputs that were read must stay unchanged
- prepare hashed every input before reading and re-hashed all of them at the end. With `--rows`, files after the cut
  are never read; if one of them is the live self-play file (still growing), hours of prepare would end with exit 2
  for rows that were not used. Fix (dev copy): each input records `"read": true/false` in prepare.json and only read
  inputs must be unchanged. The message for a job without prepare.json now says what to do (prepare again into a new
  folder). Dev test script: **75 / 75 PASS** (logs/test_relabel2_dev_final.log; new: an input after the cut grows ->
  exit 0 and `"read": false`). The run took 39 min instead of ~2 min: Idle, starved next to the two proof probes and
  Astra's two BelowNormal jobs.

## Review milestone R14B-I2-2 (15:55-16:30; structured self-review, NOT independent)
- Candidate: dev copy `D:\o14b\r2\dev\relabel2.py` sha256 63be772c... (= `patches/post_proof_changes.patch`), with
  test_relabel2.sh, measure_rates.sh, bridge_check.sh, label_stats.py; compared function by function with the frozen
  5c88438f (logs/fn_diff_frozen_vs_post_proof.txt).
- Read: every changed function (cmd_prepare, iter_rows, iter_rows_parallel / check_block, input_sources, check_args,
  lock_job / open_job, cmd_run, cmd_assemble, main) plus the bridge / measurement scripts and the probe build scripts.
- Findings and fixes: F8 (R8 v5 games across shard files; high for that data; fixed, real-data check), R17 (unread
  inputs re-hashed; medium usability; fixed + test), R25 (the "not a prepared job" message gives no next step; low;
  fixed). Checked and kept: --jobs 2 order / error / counter equivalence (tests), bounded blocks in flight (<= 5 x
  4,096 lines), pool shutdown on a --rows cut (`rows.close()`), lock handle not inherited by probes or workers
  (Python handles are non-inheritable), memory of a 50M job (games sets ~0.6M ids, offsets 5,000 entries).
- Not changed, documented instead: game ids are per job (one job per dataset; RELABEL_HANDOFF.md); sort_normalized.py
  holds its input in memory (split by source; its docstring says so); an interrupted prepare is redone in a new folder.
- Checks: dev tests 75 / 75 PASS; scoped diff shows the labelling / resume path unchanged.
- Next action: after the proof's `finish` (frozen code): bridge_check.sh, then promotion, then the full test script
  from the branch copy.

## Improvement 2: LTO and LTO+PGO builds of the relabel probe (17:36-17:46; speed and label identity follow)
- `build_probe_opt.sh OUT TRAIN` on CPU 2 (BelowNormal), MinGW g++ 15.2, lock source copy `C:\o13\p5\lock`, the
  branch's probe source (sha256 d7e146be..., the same file R13 built from).
- Toolchain check: R13's exact command rebuilt -> differs from the probe in use (`C:\o13\p5\forge_data_probe.exe`,
  ed76de96...) in 5 bytes only, at offsets 137-139 and 217-218 (PE link time stamp and checksum), in both builds.
- LTO exe sha256 565ddbf8230b7c57... in two separate builds (17:37 and 17:45): reproducible.
- First PGO attempt (C:\o14b\pgo1) failed silently and was caught by the script's counters: with
  `-fprofile-dir=C:\o14b\pgo1\prof` MinGW GCC 15 joins the directory with the absolute aux path
  (`C:\o14b\pgo1\prof\C:\o14b\pgo1\w\fdp-forge_data_probe.gcda`), the instrumented exe prints
  `profiling:...:Cannot create directory` / `Skip` and writes nothing; "profile files: 0" and 8 missing-profile warnings
  in the use build (logs/probe_pgo/build_pgo1_profile_dir_failed.log, pgo1_train_err_profile_dir.txt). That exe is
  not used. Fix: no `-fprofile-dir`; the .gcda files land next to the work exe (same `-o` in both phases), and the
  script now stops when no profile was written.
- Second build (C:\o14b\pgo2, logs/probe_pgo/build_pgo2.log): instrumented exe answered the 2,000 training positions
  (rows 0-1999 of the proof sample, 20k nodes) and wrote 8 profiles (one per source file), 0 profiler messages; PGO
  exe sha256 08299f9f6f4bb802... with 0 missing-profile warnings.

## Bridge check PASSED and promotion (17:46-17:55)
`bridge_check.sh /d/o14b/r2/proof C:/o14b/r2/bridge` with the post-proof code (sha256 63be772c..., logs/bridge_check.log;
load before the run in logs/bridge_load_before.txt):
| check | result |
|---|---|
| prepare of the proof's sample (same 4 inputs, `--rows 1000000`), `--jobs 1` | exit 0 in 196 s; rows.tsv byte-identical to the proof's (sha256 eefb1662...) |
| the same with `--jobs 2` | exit 0 in 63 s; rows.tsv byte-identical (single runs, Idle next to crew work: not a speed measurement; measure_rates.sh does that) |
| `run --accept-new-tool` on a copy of job A (rows.tsv, prepare.json, run_config.json, 100 published shards) | exit 0: all 100 shards re-verified, nothing left to do (`session_rows=0`, sessions.log names the new code hash) |
| `assemble` on that copy | train.txt, val.txt, labels.tsv byte-identical to the proof's job A |

Promotion: relabel2.py, test_relabel2.sh, measure_rates.sh, bridge_check.sh, label_stats.py copied from the dev copy
(= patches/post_proof_changes.patch); relabel2.py on the branch is now 63be772c...; logs/fn_diff_frozen_vs_post_proof.txt
re-made against the frozen file from git (5c88438f): the labelling / resume path is identical source.

## Improvement 2 results: same labels, faster probe (17:53-18:05)
| check | R13 probe (ed76de96, in use) vs LTO (565ddbf8) | R13 probe vs LTO+PGO (08299f9f) |
|---|---|---|
| answers on 10,000 positions (rows 900,000-909,999 of the proof sample, 20k nodes, Hash 1 MB; every field but timing: score, best move, depth, nodes, hce, flags) | **10,000 / 10,000 identical** | **10,000 / 10,000 identical** |
| speed: palindromic ABBA, 10 pairs, 1,000 positions per run (rows 500,000-500,999), CPU 2 BelowNormal with its SMT sibling CPU 3 idle on our side (Astra's BelowNormal job on all CPUs: load files) | B/A median 1.080, mean 1.053, 95% CI 1.009-1.097; answers identical in all 20 runs | **B/A median 1.094, mean 1.075, 95% CI 1.044-1.106**; answers identical in all 20 runs |
- So the LTO+PGO probe labels the same positions the same way about 7.5 % faster (ADVISORY: one core, one load
  situation; QA times officially). Training input of the profile: the proof sample's rows 0-1,999 (disjoint from both
  test sets). Evidence: logs/probe_pgo/ (identity_runs.txt, abba_r13_vs_pgo.txt, abba_r13_vs_lto.txt, load files).
- Still to show (post_chain.sh, running): a second PGO build gives the same sha256; relabel2 run end to end with the
  PGO probe reproduces the proof's labels.tsv prefix byte for byte.

## Measurements after the proof (18:06-18:25, `post_chain.sh`; logs/measure/post_chain.log with the load before every step)
Machine fact found on the way: CPUs 2-3 (the job's mask 0xC) are the two SMT threads of ONE physical core (AMD Ryzen 7
9850X3D, 8 cores / 16 threads, siblings (0,1) (2,3) ...). Both proof runs shared that core. During these runs one of
Astra's BelowNormal jobs (affinity all CPUs) used about one core somewhere on the PC.
| measurement | result |
|---|---|
| PGO build reproducible | second build (C:\o14b\pgo3) PGO exe sha256 08299f9f... = the first (C:\o14b\pgo2) |
| 1 vs 2 probe workers, 19,927 rows (forge_selfplay_003, not in the proof), 20k nodes, R13 probe, Idle, mask 0xC, order W1 W2 W2 W1 | W1 372,632 and 373,234 rows/h; W2 622,149 and 615,475 rows/h: **2 workers = 1.66x one worker** (both SMT threads of one core); labels.tsv md5 4939068e... identical in all four (labels do not depend on the worker count) |
| node counts, 1 worker, 9,929 rows | 5,000 nodes: 1,194,436 rows/h (mean nodes 4,999); 10,000 nodes: 736,776 rows/h (9,997); 20,000 nodes (W1 above): ~373,000 rows/h |
| prepare, 200,000 rows, order 1 2 2 1 (code 63be772c) | `--jobs 1` 36.5 s / 38.3 s; `--jobs 2` 12.6 s / 12.6 s; rows.tsv identical in all four; the two workers seen at Idle with affinity 0xC. The 2.96x of two workers on one physical core pointed at waste in the one-process path: see R27 |
| end to end with the PGO probe: relabel2 prepare (proof inputs, `--rows 20000`) + run (2 workers) + assemble | **labels.tsv (19,945 rows) byte-identical to the first 19,945 rows of the proof's labels.tsv (R13 probe)** |
| item 1: what the trainer gets, old loader w4 (the live layout) vs fast loader, 2,000 batches = 32.8M positions each | total-variation distance piece count 0.00048, side to move 0.00027, outcome 0.00007, queen bucket 0.00013, score (100-cp bins) 0.00057; mean score difference -1.17 SE: the same distribution (recorded in item 1's RESULTS too) |

## R27 (18:25, found by the measurements): a filesystem call per row in the one-process prepare - fixed
- The 2.96x of `--jobs 2` on one physical core was too good: the one-process path (`iter_rows`) called
  `str(p.resolve())` for every row (added with the origin fix; the frozen code and the `--jobs 2` path resolve once
  per file). `Path.resolve()` costs 76.7 us per call on this PC (20,000 calls: 1.53 s) = 15.3 s per 200,000 rows.
  Fix: resolve once per file. Output unchanged by construction and checked: 75 / 75 tests, the 1M prepare gives the
  proof's rows.tsv byte for byte again (87 s now, 196 s before the fix), logs/measure/resolvefix_check.log.
- Prepare speed, 200,000 rows, order F J1 J2 J2 J1 F, same rows.tsv (f4ba9e93...) in all six
  (logs/measure/prep_baseline_vs_current.log; nothing else of ours running, load sample in the log):
  | code | run 1 | run 2 | rows / hour (mean) | vs the frozen proof code |
  |---|---|---|---|---|
  | frozen proof code 5c88438f (baseline, one process) | 16.0 s | 16.6 s | 44.2M | 1.00 |
  | current bf714c67, `--jobs 1` | 16.7 s | 17.0 s | 42.7M | 0.97 (the added input checks: hashing twice, FEN text check) |
  | current bf714c67, `--jobs 2` | 10.8 s | 11.1 s | 65.7M | **1.49x** |

## R28 (18:25, found in the same step): test_relabel2.sh run from its own folder tested nothing
- The script changed into the scratch folder before locating itself from `$0`; called as `bash test_relabel2.sh DIR`
  (relative `$0`) it looked for relabel2.py in the scratch folder, and 32 "expect exit 2" cases passed for the wrong
  reason (python: file not found = exit 2). Fix: locate first, then `cd`; refuse to start when relabel2.py, python or
  the self-play sample is missing. Relative call now 75 / 75 PASS (logs/test_relabel2_branch_r27_r28.log); missing
  input -> "not found: ..." exit 2. The other R14-B scripts locate themselves before any `cd` (checked).

## The LTO+PGO probe with 2 workers (18:33-18:40, logs/measure/w2_pgo.log; light crew load on CPUs 2-3)
- 19,927 rows, 20k nodes, 2 workers on mask 0xC (one physical core), order R P P R: R13 probe 662,337 / 663,485
  rows/h, LTO+PGO probe 687,266 / 694,693 rows/h = **1.042x at 2 workers** (the single-thread ABBA gave 1.075x; two
  SMT threads share one core). labels.tsv md5 4939068e... in all four (and in the four jobs of the worker
  measurement). Input hashing speed: 645 MB in 0.45 s (1,443 MB/s, cached).
- RELABEL_HANDOFF.md rewritten with these measured numbers (50M rows at 20k nodes, 2 workers: 75.4 h with the R13
  probe, 72.4 h with the LTO+PGO probe, in this load; prepare 0.8 h with `--jobs 2`; ~17.1 GB on disk).

## Review milestone R14B-I2-3 (18:45-18:55; structured self-review, NOT independent)
- Candidate: relabel2.py bf714c67 (branch head), test_relabel2.sh, build_probe_opt.sh, measure_rates.sh,
  bridge_check.sh, label_stats.py, RELABEL_HANDOFF.md (rewritten 18:41), skill forge-relabel-job.
- Read: the R27 change (path / origin resolved once per file; error messages unchanged because str(p) == path), the
  R28 change (self-location before cd, input guard), the PGO build changes (no -fprofile-dir, stop when no .gcda),
  every number in RELABEL_HANDOFF.md against its log (all rates, the 50M divisions, prepare means 65.70M / 42.77M
  rows/h, 1,443 MB/s, 89.7 + 93.5 + 157.8 = 341 MB, the eight identical labels md5s, label statistics).
- Finding: the handoff pointed at the PGO exe in Opus's scratch folder without saying to copy it and check its
  sha256 -> fixed (full sha256 given; `run` pins the probe sha256 per job). No code finding.
- Checks: 75 / 75 tests (relative call), 1M prepare rows.tsv = the proof's, bridge PASS, measurement logs.
- Next action: final report draft with the before / after table; bug hunt 02:30.

## Bug hunt #1 (19:05-19:12, a short first pass; the hourly 20-minute hunts start at 20:00; self-review, NOT independent)
Scope: everything written since ~17:00 (probe_bench.py, build_probe_opt.sh, measure_rates.sh, bridge_check.sh,
label_stats.py, the R27 / R28 changes, the reason checks, item 1's fl_acceptance.sh and fl_abba.py).
| # | finding | fix | check |
|---|---|---|---|
| R29 | probe_bench.py `abba` (and item 1's fl_abba.py) used Student t only for exactly 10 pairs and 1.96 otherwise: a too narrow CI for fewer pairs (every recorded result used 10 pairs, so they stand) | t table for 1-30 degrees of freedom, checked against scipy.stats.t.ppf(0.975): 0 mismatches | unchanged result for 10 pairs (t = 2.262) |
| R30 | probe_bench.py and build_probe_opt.sh found lowrun.ps1 through `../../../o14b-l1/...`, a path into the fast-loader WORKTREE of this PC: in any other checkout of this branch both tools fail | own copy `opus_r14b/item2/lowrun.ps1` (same file, sha256 2c7fa58f...), both tools use it | probe_bench.py run on 20 positions: 20 answers |
| - | item 1's b5_checks.sh has an absolute tools path on purpose (it is run as a copy elsewhere) | made overridable (`FL_TOOLS`) | bash -n |

No other script reaches outside its own branch folder (grep for worktree paths: none left).

## Improvements for use in Forge (19:12-19:25; tests run once the full PGO run frees the core)
| # | what | why | change |
|---|---|---|---|
| I1 | disk floor `--min-free-gb` (default 50 GiB) for prepare / run / assemble | PC rule (C: and D: >= 50 GB); a 50M job writes ~17 GB (assemble ~8.5 GB at once) while crew jobs also fill C: | prepare (needs ~1.5x its input) and assemble (~170 B per row) refuse to start a write that would cross the floor (exit 3, message says what to do); run checks before every shard and stops there (logged; resume later). Quick check: floor 100000 -> exit 3 and nothing created; default on C: (129.7 GiB free) -> exit 0; negative -> exit 2. Tests: 3 cases + reasons |
| I2 | `status` prints one readable line | the old output was raw JSON + a shard count; a non-job printed `{}` with exit 0 | "N/M shards, rows done / total (%), final published?, last session's rows/h and ETA, unpublished attempt dirs, free disk"; a non-job is exit 2. Tests: partial job "2/3 shards, 200/240 rows", finished job "final published", non-job exit 2 |
| I3 | build_probe_opt.sh self-sufficient | it compiled from Opus's scratch copy `C:\o13\p5\lock` and needed a training file from `D:\o14b` | lock source exported from this repository (`git archive d4f4312 src include`, all 20 files identical to the scratch copy), training file committed (`pgo_train_2k.tsv`, sha256 5c1af57a...) and used by default; the R13 comparison is skipped with a message when that exe is absent |
| R31 | a fresh clone on grok-pc (git's global `core.autocrlf=true`) wrote every .sh / .py / .md with CRLF, so the sha256 values the documents give for tool files would not match a crew checkout | `opus_r14b/.gitattributes` on all three branches: code, scripts, docs and committed inputs LF in every checkout; logs, patches, raw outputs byte-exact | fresh clone with the default settings: scripts LF, relabel2.py sha256 = the branch's, training file 5c1af57a... |

## Runtime dependencies of the probes (19:27, works in Forge)
- R13 / LTO / PGO probe exes are static: `objdump -p` of the PGO exe lists only KERNEL32.dll and the Windows UCRT API
  sets; it answered a request with PATH = `C:\WINDOWS\system32;C:\WINDOWS` only. No MSYS2 / Git folder is needed at run
  time (only for building).
- Publish renames retry a transient PermissionError (virus scanners / indexers / readers hold handles on Windows) and a
  status.json that stays locked is skipped with a warning (a873b269; tests added: a shard publish failing twice, a
  status file that never unlocks).

## More "works in Forge" fixes (19:26-19:31)
| # | finding | fix | check |
|---|---|---|---|
| R32 | prepare under a Python without python-chess reported `BAD INPUT: <file>:1: No module named 'chess'`, i.e. blamed the first input line | the imports are checked once before any input is read: "python-chess is needed ...; use C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe" (exit 2) | simulated missing module: exit 2, message, no job folder; test + reason check |
| R33 | sort_normalized.py holds its input in memory (~2.2x the file size): sorting Astra's 9.2M-row set would take ~3.7 GB and could push the PC below the RAM floor at which the crew's guards stop training | free physical RAM is checked before reading (`--min-free-ram-gb`, default 8): refuse with "split the input by source" when the sort would cross it | impossible floor: exit 2 before reading, nothing written; a randomly shuffled copy sorts back byte for byte; tests + reason check |
| I4 | a rebuilt or new probe could only be checked against the R13 answers with Opus's scratch files | committed `probe_ref_500.tsv` (500 positions, rows 900,000-900,499 of the proof sample) + `probe_ref_500_r13.jsonl` (the R13 probe's answers, 20k nodes, Hash 1 MB): `probe_bench.py run --exe <probe> --req probe_ref_500.tsv --out new.jsonl` then `probe_bench.py compare probe_ref_500_r13.jsonl new.jsonl` (exit 0 = all 500 identical) | ids and FENs of the two files match; used in the fresh-clone check |

## Bug hunt #2 (19:41-19:47 by the PC clock; self-review, NOT independent)
Scope: every change since hunt #1 - relabel2.py (disk floor, status line, move_retry / write_status, python-chess
check), test_relabel2.sh (new cases and reason checks), build_probe_opt.sh (git export of the lock source, committed
training file), sort_normalized.py (RAM check), item 1's install_fast_loader.py / fl_acceptance.sh / fl_abba.py,
tools/hash_sweep.py, the .gitattributes files, and the documents against the code.
| # | finding | fix | check |
|---|---|---|---|
| H2-1 | with the test scratch on a drive below 50 GB free (D: hovers at 52-56 GB), relabel2's own disk floor would fail case after case with a confusing cascade | test_relabel2.sh checks the scratch drive first (>= 51 GB) and stops with one message | bash -n; full suite in the next chain |
| H2-3 | install_fast_loader.py --loader-dll printed "would copy" lines in a real install (its validation pass) | the validation pass is silent unless --check | check / install / second install on fresh copies of the live config.py + train.py: "would copy" only with --check, files copied with sha256 9eb29b7d... / 39af47b0..., second install exit 2; the fresh install is byte-identical to the tested trainer copy (config.py 5c41d7a7..., train.py d9c3ccef...) |
| H2-4 | the documents called `F:\opus_scratch\rescore_d8\bin\fen2bin.exe` "Forge's own" converter; it is the build earlier Opus / R11 jobs used (sha256 24cb2e78...), its source is not in this repository and the live supervisor's converter was not compared | wording in RELABEL_HANDOFF.md, RESULTS.md, the skill and FINAL_REPORT.md | hash_sweep |
| H2-6 | docs as tests: the RELABEL_HANDOFF.md command block run as written (placeholders filled, 300 rows, 5k nodes, 2 workers): prepare / run / run again / assemble / status all exit 0 - but a run on a job with every shard published still started its probes before finding nothing to do | `run` returns at once when all shards are published and re-verified ("nothing left to label" in sessions.log, no probe started) | test run_complete_job |

Checked and kept: move_retry retries PermissionError only (an existing target still fails at once); every floor check
runs before its write; the status line handles jobs never run (no run_config.json); the simulated-contention tests
patch only the calls they target.

## Bug hunt #3 (20:04-20:09 and 20:17-20:21 by the PC clock; self-review, NOT independent, + the advisor's read)
Scope: what hunts 1 and 2 did not read - relabel2.py run / assemble / prepare internals (shard loop, failure paths,
game rule, split, input checks, status), the R13 probe client's failure behaviour (forge_probe.py, unchanged copy),
and item 1's trainer path (does the trainer copy a batch before the fast loader reuses its memory?).
| # | finding | fix | check |
|---|---|---|---|
| H3-1 | a probe that dies, times out or answers wrongly stopped `run` with a bare traceback (exit 1) and NO line in sessions.log: an operator resuming a 70-hour job could not see why the last session ended | the shard loop is wrapped: any such error writes "run stop run_id=.. tool=.. after N new shards: <type>: <message> (exit 1; published shards stay, ...)" to sessions.log and re-raises (exit 1 as documented); the disk floor keeps its own stop line | new test: a job run with `whoami.exe` as the "probe" -> exit 1, the stop line with ProbeError, attempt dir shard_00000.part.1 kept, nothing published (suite run after the full PGO run frees the core) |
| H3-2 | `run` lowered itself to Idle on the CPU mask only after hashing rows.tsv, the probe and itself: for a 50M job that is ~4.5 GB of sha256 at the caller's priority on any CPU (Normal when started from a normal shell) | main() lowers priority for prepare, run and assemble before the command starts (as prepare / assemble already did) | code read; suite |
| H3-3 | the docstring says every sessions.log line names the code hash; the disk-floor stop line did not | both stop lines carry tool=<sha256 prefix> | test greps the new line with its tool hash |
| H3-4 | (advisor, 20:17) the new stop line said "exit 1" for every error, but a BadInput / IntegrityError raised inside the shard loop leaves with exit 2 / 4 | the line names the exit code main() will return | code read |
| H3-5 | (advisor, 20:17) `--mask` above the PC's CPUs (e.g. 0x10000 on 16 CPUs) passed check_args and died with a SetProcessAffinityMask traceback (abba.py had this fix, relabel2.py not) | exit 2 "names a CPU this PC does not have" before anything starts, for prepare / run / assemble | 3 tests + reasons: run with `xyz`, run and prepare with 0x10000000000 (nothing created) |

Checked, no finding: shard publish by directory rename (FileExistsError is not retried, so a published shard is never
replaced); verify_shard on every published shard at start and twice in assemble; the game rule cannot split a game;
the split hash; `--rows` cuts at a game boundary and closes the --jobs workers; inputs hashed before and after
reading; item 1: the trainer's `_pin_and_move` copies every batch block into a new tensor (also for device "cpu")
before `FastSparseBatchProvider` releases the ring slot, and the packed-index path that skips the copy needs
native_owned + CUDA without HIP, which this ROCm trainer never takes - no use-after-release.
Docs: exit code 1 described in RELABEL_HANDOFF.md and the skill forge-relabel-job.

## After hunt #3: a launcher that reported success for a program that never started (20:24-20:27)
| # | finding | fix | check |
|---|---|---|---|
| L1 (20:25, found while converting the full 1M output) | `lowrun.ps1` (the launcher every R14-B tool uses to run a program at low priority on CPUs 2-3) ended with exit 0 when Start-Process could not start the program (missing file), and ran it with an invalid handle when a redirect folder did not exist - a caller trusting the exit code would count a program that never ran as a success | exit 127 with a message in both cases and for a missing stdin file; the program's own exit code otherwise. Same fixed file (sha256 cc7f28dd...) in all three branches | missing exe 127, missing stdout / stderr folder 127, missing stdin 127, `cmd /c exit 3` 3, echo with redirect 0 + output, stdin redirect works, Idle 0 |

Every caller in item 2 (build_probe_opt.sh, probe_bench.py) also checks its outputs, so no recorded result was affected (the probe builds and the probe answers are checked by sha256 and by comparing answers).

## The full 1M proof sample with the LTO+PGO probe (18:48-20:24) and through Forge's converters (20:27)
- `relabel2.py` (bf714c67 for prepare / run, the 20:2x branch code for assemble) on the proof's inputs (`--rows
  1000000 --jobs 2`, rows.tsv = the proof's), probe `C:\o14b\pgo2\pgo\forge_data_probe.exe` (LTO+PGO, sha256
  08299f9f...), 20k nodes, 2 workers, CPUs 2-3 Idle: **train.txt / val.txt / labels.tsv identical to the proof's
  (R13 probe) files** - md5 6e9e4e5a... / 8e639f41... / 2614e82d...: all 999,921 labels are the same with both probes.
  Evidence: `logs/pgo_full_1M.log` (copy of C:\o14b\r2\pgo_full.log, with the load samples at start and end).
- Rate under real load: 100 shards in 5,666 s of labelling = **635,344 rows/h** (per 10,000-row shard median 55.6 s,
  50.1-81.6 s; quarters 665k / 625k / 604k / 650k rows/h); mean nodes 19,992. At the end the live npt trainer's Idle
  python (affinity 0xF, so also CPUs 2-3) used 1.3 cores; at 18:48 the CPUs were nearly free. 50M rows at this rate:
  **78.7 h** (the 72.4 h of the short 18:33-18:40 measurement was a light-load window).
- Forge's FPOS / HCE converters (the builds earlier jobs used, `F:\opus_scratch\rescore_d8\bin`, fen2bin sha256
  24cb2e78..., hce_dump a88e519d...) on the full output: fen2bin train 991,077 lines = 991,077 records, bad 0; val
  8,844 = 8,844, bad 0 (35 bytes per record); hce_dump train 991,077 records, bad_fen 0, clamped 0; val 8,844, 0, 0
  (`logs/conv_full_1M.txt`). Before: 1,200 rows of a test job.

## Found by the verify chain's fresh-clone step (20:33-20:36)
| # | finding | fix | check |
|---|---|---|---|
| C1 | `build_probe_opt.sh` (since I3 at 19:18) ran `git -C <its own folder> archive d4f4312 src include`; git reads those paths relative to the folder it runs in (`opus_r14b/item2/src`), so the lock export failed ("pathspec 'src' did not match") and the script stopped (set -e / pipefail) - in a fresh clone and in the worktree alike. The I3 check had exported from the repository root by hand, not through the script | archive from the repository's top level (`git rev-parse --show-toplevel`) and require exactly 20 exported files | export from the item2 folder: 20 files, identical to `C:\o13\p5\lock`; the probe builds from a fresh clone run again after the chain |
| C2 | the chain's adoption rehearsal called `robocopy SRC DST /E ...` from Git Bash, which rewrote `/E` into `E:/` (robocopy exit 16, nothing copied; the manifest, installer and acceptance failures that followed were consequences) | `MSYS_NO_PATHCONV=1` for that call (fresh_checkout_checks.sh; item 1 HANDOFF notes it for Git Bash users) | 382 / 382 files copied, exit 1 (= files copied); the rehearsal runs again after the chain |

## Verify chain 20:29-20:39 on the freeze candidate (`opus_r14b/checks/verify_chain.sh 2030`; logs/chain_2030/)
Candidate: relabel2.py sha256 88454db6e17cf4e72cfa651ea253c9fc8599d1317a553d25d14dd96685570545 (commit f414e2d8, 20:20).
| step | result |
|---|---|
| 1 suite from the worktree | **150 PASS / 0 FAIL** (incl. the hunt-3 cases: dead probe -> exit 1 + stop line, masks, run on a finished job) |
| 2 bridge to the 1M proof | **PASS**: prepare `--jobs 1` (91 s) and `--jobs 2` (59 s) rows.tsv = the proof's; `run --accept-new-tool` on a copy of proof job A re-verified 100 shards ("nothing left to label"); assemble = the proof's train / val / labels byte for byte |
| 3 fresh clone (f366e8eb, default core.autocrlf=true; same relabel2.py) | suite 150 / 0; loader DLL rebuilt = b5; acceptance 261 / 261; **probe builds FAILED (C1) and adoption rehearsal FAILED (C2)** - both fixed above, re-run below |
| 4 loader ABBA, live thread setting | item 1 RESULTS (6.25x) |
| 5 prepare of R8 v5 shards 271 + 272 (`--jobs 2`) | exit 0 in 106 s: 1,825,791 rows, 21,490 games (val 214 games / 18,253 rows) = 62.0M rows/h |
| 6 R8 v5 end to end | prepare `--rows 3000` (cut at a game boundary: 2,859 rows) -> 3 shards at 20k nodes, PGO probe, 2 workers -> assemble -> status "3/3 shards ... final published" -> fen2bin: 2,804 train records = 2,804 rows, 0 bad (val 55 rows) - **PASS** |

## Code freeze (after the verify chain)
relabel2.py is frozen at sha256 88454db6e17cf4e72cfa651ea253c9fc8599d1317a553d25d14dd96685570545 (commit f414e2d8):
suite 150 / 0 in the worktree and in two fresh clones (20:33, 20:39), bridge PASS, every labelling function identical
to the proof's code (logs/fn_diff_frozen_vs_88454db6.txt: file_hash, label_shard, load_prepare, new_game,
board_stats, read_shard_rows, row_offsets, verify_shard ...; changed: cmd_* / iter_rows / main / write_status for the
checks, logging and disk floor). The whole 1M sample with the PGO probe also matched the proof (run on bf714c67,
assembled with the branch code of 20:2x). Any later change to relabel2.py: `opus_r14b/checks/refreeze.sh TAG` (suite
in the worktree and a fresh clone, bridge, function diff, new sha256) and the new sha256 in RELABEL_HANDOFF.md, this
file, the skill, FINAL_REPORT.md and the memory note. Tools around it (build_probe_opt.sh, probe_bench.py,
lowrun.ps1, ...) can change without touching the freeze; their checks are listed with each change.

## Fresh-clone checks again after C1 / C2 (20:39-20:42; logs/chain_2030/fresh_checkout_rerun_2039.log): 0 failures
Clone of this branch at 7fac1de1 (default core.autocrlf=true): suite 150 / 0; `build_probe_opt.sh` with its defaults
(lock source exported from git: 20 files; committed pgo_train_2k.tsv: 2,000 training answers, 8 profile files):
plain = R13's exe except the 5 PE timestamp / checksum bytes (137-139, 217-218), **LTO 565ddbf8... and PGO
08299f9f... = the tested exes byte for byte**; the clone-built PGO probe answered probe_ref_500 **500 / 500 identical**
to the R13 reference. (Item 1's part of the same run - DLL, self-test, acceptance, adoption rehearsal: item 1
RESULTS.) With this, every step of the verify chain has passed on the frozen code.

## 50M runbook added to RELABEL_HANDOFF.md (21:17-21:19)
- R8 v5 rows counted read-only (BelowNormal, CPUs 2-3): shards 001-057 = 50,524,643 rows, 001-056 = 49,599,490, so
  `--rows 50000000` ends inside 057; per-phase times from the measured rates (prepare ~0.8 h, run ~79 h at the whole-1M
  rate, assemble minutes, converters minutes), disk ~17.1 GB + outputs.
- Docs as a test: the runbook's prepare command exactly as written (57 inputs, `--jobs 2 --drop-terminal`), only
  `--rows 3000` and a scratch job folder changed: exit 0, 57 inputs accepted in name order, 1 read (the cut), 2,973 rows
  (whole games), `terminal_dropped: 0`; `status` prints "not run yet". C:\o14b\runbook_dry_2120.
