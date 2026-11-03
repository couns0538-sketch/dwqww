# RELABEL_HANDOFF - for Engine NNUE (R14-B item 2; UNPROVEN as training data, the 50M run is NOT started)

## State (2026-11-02, updated 22:47 PC clock)
- `relabel2.py` on branch `opus-r14b-relabel` (folder `opus_r14b/item2/`), **frozen at sha256
  e01caaf1cf8814771033b3deb71727fd0d2eb45f39ee9b27ae54c7d2970f1602** (commit a3470e08). Check the file you run
  against it. Earlier freezes: 88454db6... (20:41), 0a81dd5f... (22:03, after fuzzing prepare: an input score outside
  -32767..32767 is exit 2), 56eef0a6... (22:22, after the damaged-job harness `job_damage.py`: a run_config.json lost
  while shards are published is exit 4 instead of being re-created; damaged job files are exit 4 with the file named
  instead of a Python traceback); re-frozen 22:46 after shards started to record their settings (node limit, hash,
  probe sha256), so that an edited run_config.json cannot mix two settings in one job. The 1M kill / resume proof ran
  on 5c88438f and PASSED (A uninterrupted vs B hard-exited twice: train.txt / val.txt / labels.tsv md5 identical). The
  functions that compute labels and game ids are identical source to the proof's (label_shard, new_game, board_stats,
  row_offsets, read_shard_rows, file_hash; logs/fn_diff_frozen_vs_e01caaf1.txt; load_prepare / verify_shard changed
  only in how damaged or mismatched files are reported), and the frozen version reproduced the proof's rows.tsv and
  final files byte for byte (bridge, again in the re-freeze 22:43-22:46, including a resume of a copy of proof job A,
  whose older shards record no settings). Suite: 155 PASS / 0 FAIL in the worktree and in a fresh clone (re-freeze);
  the verify chain 20:29-20:39 (RESULTS.md) also ran the R8 v5 prepare and an end-to-end job through fen2bin. Tests:
  `test_relabel2.sh SCRATCH` (exit codes with their reasons, `--jobs 2`, a game across two files, disk floor, mini
  kill / resume, a dead probe, a busy job, 105 damaged-job runs); run it after any change, and after a change to
  relabel2.py run `opus_r14b/checks/refreeze.sh` (branch opus-r14b-status) and write the new sha256 here.
- Probes (same labels, checked): the R13 probe `C:\o13\p5\forge_data_probe.exe` (sha256 ed76de96...) or its LTO+PGO
  build `C:\o14b\pgo2\pgo\forge_data_probe.exe` (sha256 08299f9f...; rebuild with
  `build_probe_opt.sh NEW_OUT_DIR`: lock source from git, PGO profile from the committed `pgo_train_2k.tsv`; two builds
  gave the same sha256). 10,000 / 10,000 answers
  identical, and the whole 1M proof sample relabelled with it gave train / val / labels files byte-identical to the
  proof's (all 999,921 labels; 2026-11-02 18:49-20:24, logs/pgo_full_1M.log). All probe exes are static
  builds for this PC's CPU (`-march=znver5`; only Windows DLLs imported): on another CPU rebuild and run the probe
  reference check (probe_ref_500) before trusting the labels. `C:\o14b` is Opus's scratch
  folder: copy the exe to a folder you own (or rebuild it) and check sha256 08299f9f6f4bb8026900ff7111a0b0e7461f77c18e5b01eeefcb05498d3546e7
  before a long run; `run` pins the probe's sha256 in run_config.json, so a job keeps the probe it started with.

## What you get
`relabel2.py` relabels self-play positions with a fixed-node search of the lock engine (lock source d4f4312, state
cleared before every search, 1 thread, Hash 1 MB), keeps the **original FEN** (castling, en passant, clocks; the probe
echoes the FEN and the tool checks it), splits validation **by game** (no game in both), and can be stopped at any
moment and resumed with the same command. Outputs per job: `final/train.txt`, `final/val.txt` (self-play text format
`FEN | new stm cp | white result`), `final/labels.tsv` (row id, game id, split, FEN, new and old score, result, depth,
nodes), `final/MANIFEST.json` (md5 + sha256). The FPOS converter earlier jobs used, `F:\opus_scratch\rescore_d8\bin\
fen2bin.exe in.txt out.pos` (sha256 24cb2e78...; its sibling `hce_dump.exe` reproduces the production .hce exactly per
R11), turns the text into .pos files with the new scores (checked on 1,200 rows: 0 bad lines; score, side to move and
result columns equal), and `hce_dump.exe in.txt out.hce` (sha256 a88e519d...) makes the .hce. On the full 1M output:
fen2bin 991,077 + 8,844 records = every train / val row, 0 bad; hce_dump the same counts, 0 bad FEN, 0 clamped
(logs/conv_full_1M.txt). Whether the live supervisor uses these same binaries was not checked. Exit codes: 2 bad input,
3 configuration differs / job busy / target exists / disk floor, 4 integrity (a published file changed), 1 anything
else, e.g. a probe that died, timed out or answered wrongly (`run` first writes "run stop ... <error>" to
sessions.log; published shards stay; the same command resumes once the cause is fixed).

## Commands (PC rules: Idle, CPU mask, <= 2 probe workers; nothing is deleted or overwritten)
```bash
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe   # python-chess 1.11.2
R=<branch opus-r14b-relabel>/opus_r14b/item2/relabel2.py
$PY -I -B $R prepare --job C:/<new job dir> --run-id <id> --rows 50000000 --jobs 2 \
    --selfplay <finished self-play files in name order, one folder> [--val-ppm 10000] [--salt <salt>]
$PY -I -B $R run --job C:/<job dir> --run-id <id> --probe <probe exe> --nodes 20000 --workers 2 --mask 0xC \
    [--until "YYYY-MM-DD HH:MM"]                     # the same command again = resume
$PY -I -B $R assemble --job C:/<job dir> --run-id <id>
$PY -I -B $R status --job C:/<job dir>          # one line: shards, rows (%), last rate, ETA, free disk
```
- `--mask` picks the CPUs: 0xC = CPUs 2-3 = ONE physical core (SMT pair) on this PC, Opus's R14-B budget; agree the
  production CPUs with the crew. `--workers` is 1 or 2 (the brief's limit; one constant in cmd_run / check_args).
- prepare needs python-chess (the venv above); a Python without it gets one clear message (exit 2).
- `--min-free-gb` (default 50) on prepare / run / assemble keeps the PC's disk floor (see Rules).
Astra's filter (`filter_positions.py`, branch astra-r8-datafilter) runs before or after as Engine NNUE decides; its
normalized JSONL output is accepted with `--normalized` when sorted by (source, source_row) (`sort_normalized.py`,
which holds its input in RAM, ~2.2x the file size, and refuses when that would leave less than `--min-free-ram-gb`
(default 8) free: then sort per source and give the sorted files in source order).

## Rules for the big job
- ONE job per dataset: game ids (`s<origin>g<n>`) and the split are per job; merging two jobs that share an input
  file could put a game in train and val.
- Finished self-play files only (the newest file is still being written). Each input that is read is hashed before
  and after reading; a change is exit 2. The same file or the same content twice is exit 2.
- R8 v5 self-play (`D:\grok-pc-data\selfplay_out_r8v5_20261029\forge_selfplay_fast_NNN.dedup.txt`, 286 shards at
  20:22 on 2026-11-02, one new shard every ~21 min (273 finished 15:36, 286 at 20:12); 894,187 rows in shard 001,
  913,141 in 272, so 50M rows = ~55 shards) writes fixed 1M-position shards: a game runs from one shard into the
  next (271 ends at move 57 of a game that 272 continues). relabel2 treats the inputs as one stream and only its
  game rule splits games, so give the files in name order from one folder (any other order is exit 2). The old `selfplay_out\forge_selfplay_NNN.txt` files end and start at game boundaries.
- Disk floor: prepare, run and assemble take `--min-free-gb` (default 50 = the PC rule for C: and D:). prepare (~1.5x
  its input) and assemble (~170 bytes per row: ~8.5 GB for 50M rows) refuse to start a write that would cross it;
  run stops before the next shard (exit 3, logged in sessions.log; published shards stay, the same command resumes).
- One process per job (`job.lock`; a second one stops with exit 3). The session tools on this PC cannot stop a
  process: bound a session with `--until` and run the same command again later.
- Leave the job folder's files as relabel2 wrote them. A damaged or missing job file (rows.tsv, prepare.json,
  run_config.json, a published shard's labels / manifest / summary) is exit 4 with the file named, and nothing more is
  labelled or published. run_config.json pins probe, nodes, hash and shard size: if it is lost after shards were
  published, `run` refuses (exit 4) rather than re-create it from the command line, because a resume with other
  settings would mix labels. A copy of run_config.json and prepare.json kept next to the job (they are small and never
  change) makes that case a one-file restore. `status` only warns on damaged status / config files.
- Every shard's summary.json records the node limit, hash size and probe sha256 it was labelled with; run and assemble
  refuse (exit 4) a shard whose settings differ from run_config.json, so an edited run_config.json cannot mix two
  settings in one job either (shards of versions before e01caaf1, such as the 1M proof's, do not record them).
- A published shard that fails its check (exit 4 naming `shard_K`, e.g. a disk error after a power cut): rename that
  folder aside (e.g. `shard_K.bad`; never delete it) and run the same `run` command - it labels that shard again in a
  new attempt folder and publishes it; then `assemble`.

## 50M runbook - an example on R8 v5 (Engine NNUE picks the inputs, the node count and the probe; NOT started)
Inputs, counted 2026-11-02 21:17 (read-only): R8 v5 shards 001-057 hold 50,524,643 rows (001-056: 49,599,490), so
`--rows 50000000` ends at a game boundary inside shard 057. All 57 are finished files (286 shards existed at 20:22; the
newest one is still being written). Shards 271 + 272 (1.83M rows) held no position without a legal move
(`terminal_dropped: 0`); `--drop-terminal` is still given below, so that one such row cannot stop a 50M prepare (it
cannot get a search label; prepare.json counts what was dropped).
```bash
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
R=<branch opus-r14b-relabel>/opus_r14b/item2/relabel2.py       # sha256 e01caaf1...
P=<your copy of the LTO+PGO probe>                               # sha256 08299f9f... (or the R13 probe ed76de96...)
S=/d/grok-pc-data/selfplay_out_r8v5_20261029
J=C:/<your folder>/relabel_r8v5_50m                              # a NEW folder on a drive with > 70 GB free
sha256sum "$R" "$P"                                              # compare with the values above first (a path with
                                                                 # backslashes makes sha256sum print a leading "\")
$PY -I -B "$R" prepare --job "$J" --run-id r8v5-50m --rows 50000000 --jobs 2 --drop-terminal \
    --selfplay $(for i in $(seq -f %03g 1 57); do echo "$S/forge_selfplay_fast_$i.dedup.txt"; done)
$PY -I -B "$R" run --job "$J" --run-id r8v5-50m --probe "$P" --nodes 20000 --workers 2 --mask 0xC \
    --until "YYYY-MM-DD HH:MM"                                   # the same command again resumes
$PY -I -B "$R" status --job "$J"                                 # progress, last rate, ETA, free disk
$PY -I -B "$R" assemble --job "$J" --run-id r8v5-50m             # final/train.txt, val.txt, labels.tsv, MANIFEST.json
F:/opus_scratch/rescore_d8/bin/fen2bin.exe "$J/final/train.txt" <out dir>/train.pos   # and val.txt; hce_dump.exe for .hce
```
| phase | expected (measured basis) |
|---|---|
| prepare `--jobs 2` | ~0.8 h (65.7M rows/h on 200k rows; R8 v5 271 + 272: 1.83M rows in 106 s = 62M rows/h) |
| run, 20k nodes, 2 workers on CPUs 2-3 (one core), PGO probe | **~79 h** (the whole-1M rate 635k rows/h under real load; ~10 sessions of 8 h with `--until`) |
| assemble | minutes (1M rows: a few seconds) |
| fen2bin / hce_dump on the output | ~3 min / ~4 min (1M: 3 s / 5 s) |
| disk on the job's drive | ~17.1 GB (rows.tsv ~4.5, shards ~4.7, final ~7.9) + .pos ~1.75 GB (35 B per row) + .hce ~0.1 GB |

A stop of any kind during `run` - `--until`, a reboot, a power cut, a crash - loses at most the shard in progress
(published shards are fsynced and renamed into place in one step; the 1M proof stopped B twice with a hard exit and
the output was byte-identical): after a reboot, run the same `run` command again; it re-verifies every published
shard and redoes the interrupted one in a new attempt folder (the old one is kept).

Checks before using the output: MANIFEST.json md5s, `game_overlap: 0`, train + val rows = prepare.json's rows, fen2bin
`records` = lines with `bad=0`, hce_dump `bad_fen=0 clamped=0` (as on the 1M proof sample, logs/conv_full_1M.txt).
All of them in one read-only command: `$PY -I -B verify_job.py "$J" --convert <new out dir>` (MANIFEST bytes / md5 /
sha256, counts, every labels row once and in order, train.txt / val.txt = exactly those rows, no game in both splits,
shards re-hashed against MANIFEST, shard settings = run_config.json, then fen2bin + hce_dump; exit 0 = all PASS, 4 =
a named mismatch). The whole 1M PGO job: all PASS in under 2 s without `--convert` (logs/verify_job/).

## Cost (measured 2026-11-02, labels identical in every comparison; load on CPUs 2-3 logged next to every number)
CPUs 2-3 (mask 0xC) are the two SMT threads of ONE physical core of the Ryzen 7 9850X3D: "2 workers" = 2 threads
sharing one core.
| quantity | measured | 50M rows | source |
|---|---|---|---|
| **20k nodes, 2 workers, LTO+PGO probe, the whole 1M proof sample (18:49-20:24), real load (at the end the npt trainer's Idle python, affinity 0xF, used 1.3 cores)** | **635,344 rows/h** (quarters 665k / 625k / 604k / 650k) | **78.7 h** | logs/pgo_full_1M.log |
| 20k nodes, 2 workers, R13 probe, light crew load (18:33-18:40) | 662,337 / 663,485 rows/h | **75.4 h** | logs/measure/w2_pgo.log |
| 20k nodes, 2 workers, LTO+PGO probe, same window, order R P P R | 687,266 / 694,693 rows/h (1.042x of R13) | **72.4 h** | same |
| 20k nodes, 2 workers, R13, with one crew BelowNormal job on all CPUs (18:08-18:15) | 622,149 / 615,475 rows/h | 80.8 h | logs/measure/post_chain.log |
| 20k nodes, 1 worker, R13, same load | 372,632 / 373,234 rows/h | 134.1 h | same |
| 10k nodes, 1 worker, R13, same load | 736,776 rows/h (mean nodes 9,997) | 67.9 h (1 worker) | same |
| 5k nodes, 1 worker, R13, same load | 1,194,436 rows/h (mean nodes 4,999) | 41.9 h (1 worker) | same |
| the proof itself: 2 single-worker jobs on the two SMT threads, shards 0-28 (before most crew load) | 104-118 s per 10,000 rows each, ~340k rows/h each | - | proof shard summaries |
| prepare, 200k rows, `--jobs 2` / `--jobs 1` (current code) | 65.7M / 42.7M rows/h (10.8-11.1 s / 16.7-17.0 s) | **0.8 h** / 1.2 h | logs/measure/prep_baseline_vs_current.log |
| input hashing (twice per read input) | 1,443 MB/s (645 MB in 0.45 s, cached) | ~55 shards x 60 MB x 2: about 5 s | logs/measure/w2_pgo.log |
| disk per 1M rows (proof job A) | 341 MB: rows.tsv 89.7 MB + shards 93.5 MB + final 157.8 MB | **~17.1 GB**: put the job on C: (keep >= 50 GB free; D: sat at 52-56 GB on 2026-11-02) | du of the proof job |
- Labels do not depend on the worker count: labels.tsv md5 4939068e... in all eight 19,927-row jobs (1 and 2 workers,
  both probes).
- 50M wall times are rows / measured rate; the real rate depends on crew load (Idle work yields to everything). Plan
  with the whole-1M figure (78.7 h on CPUs 2-3 with the PGO probe): it ran 94 minutes through changing crew load,
  while the 72-75 h figures come from 7-minute light-load windows.

## Labels of the 1M proof sample (descriptive only; `label_stats.py`, logs/label_stats_proof_1M.txt)
999,921 rows, mean nodes 19,992, depth mostly 8-11 (17.0 / 42.0 / 25.3 / 8.1 %); |new - old| median 52 cp (p90 330,
p99 866); Pearson r(new, old) 0.9768 on rows with both |score| < 2000; same sign 95.1 %; mate-range labels
(|score| >= 30000) new 2,717, old 0; on decisive games the score sign (White's view) matches the result for 90.1 %
(new) vs 89.8 % (old). Whether the new labels train better is for Engine NNUE to test.
