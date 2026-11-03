# RELABEL_HANDOFF - for Engine NNUE (R14-B item 2; UNPROVEN as training data, the 50M run is NOT started)

## State (2026-11-02, updated 19:20 PC clock)
- `relabel2.py` on branch `opus-r14b-relabel` (folder `opus_r14b/item2/`): use the branch head; its sha256 is written
  here once the code is frozen (planned for tonight, after the next full check run). The 1M kill / resume proof ran
  on the frozen 5c88438f and PASSED (A uninterrupted vs B hard-exited twice: train.txt / val.txt / labels.tsv md5
  identical). Later versions keep the labelling functions as identical source (logs/fn_diff_frozen_vs_post_proof.txt;
  the shard loop adds a disk-floor check and a retrying publish rename) and reproduced the proof's rows.tsv and final
  files byte for byte (bridge_check.sh, RESULTS.md; re-run on the frozen code). Tests:
  `test_relabel2.sh SCRATCH` (exit codes with their reasons, `--jobs 2`, a game across two files, disk floor, mini
  kill / resume) - run it after any change.
- Probes (same labels, checked): the R13 probe `C:\o13\p5\forge_data_probe.exe` (sha256 ed76de96...) or its LTO+PGO
  build `C:\o14b\pgo2\pgo\forge_data_probe.exe` (sha256 08299f9f...; rebuild with
  `build_probe_opt.sh OUT D:\o14b\r2\pgo_req\train_2k.tsv`, two builds gave the same sha256). 10,000 / 10,000 answers
  identical, and relabel2 with it reproduced the proof's first 19,945 labels byte for byte. `C:\o14b` is Opus's scratch
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
result columns equal), and `hce_dump.exe in.txt out.hce` makes the .hce (1,200 records, 0 bad). Whether the live
supervisor uses these same binaries was not checked. Exit codes: 2 bad input,
3 configuration differs / job busy / target exists, 4 integrity (a published file changed).

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
- R8 v5 self-play (`D:\grok-pc-data\selfplay_out_r8v5_20261029\forge_selfplay_fast_NNN.dedup.txt`, 273 shards on
  2026-11-02; 894,187 rows in shard 001, 913,141 in 272, so 50M rows = ~55 shards) writes fixed 1M-position shards:
  a game runs from one shard into the next (271 ends at move 57 of a game that 272 continues). relabel2 treats the
  inputs as one stream and only its game rule splits games, so give the files in name order from one folder (any
  other order is exit 2). The old `selfplay_out\forge_selfplay_NNN.txt` files end and start at game boundaries.
- Disk floor: prepare, run and assemble take `--min-free-gb` (default 50 = the PC rule for C: and D:). prepare (~1.5x
  its input) and assemble (~170 bytes per row: ~8.5 GB for 50M rows) refuse to start a write that would cross it;
  run stops before the next shard (exit 3, logged in sessions.log; published shards stay, the same command resumes).
- One process per job (`job.lock`; a second one stops with exit 3). The session tools on this PC cannot stop a
  process: bound a session with `--until` and run the same command again later.

## Cost (measured 2026-11-02, labels identical in every comparison; load on CPUs 2-3 logged next to every number)
CPUs 2-3 (mask 0xC) are the two SMT threads of ONE physical core of the Ryzen 7 9850X3D: "2 workers" = 2 threads
sharing one core.
| quantity | measured | 50M rows | source |
|---|---|---|---|
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
- 50M wall times are rows / measured rate; the real rate depends on crew load (Idle work yields to everything).

## Labels of the 1M proof sample (descriptive only; `label_stats.py`, logs/label_stats_proof_1M.txt)
999,921 rows, mean nodes 19,992, depth mostly 8-11 (17.0 / 42.0 / 25.3 / 8.1 %); |new - old| median 52 cp (p90 330,
p99 866); Pearson r(new, old) 0.9768 on rows with both |score| < 2000; same sign 95.1 %; mate-range labels
(|score| >= 30000) new 2,717, old 0; on decisive games the score sign (White's view) matches the result for 90.1 %
(new) vs 89.8 % (old). Whether the new labels train better is for Engine NNUE to test.
