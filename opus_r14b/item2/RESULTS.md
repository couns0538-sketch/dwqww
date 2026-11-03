# R14-B item 2 - resumable relabel with original FENs and a game-level validation split - IN PROGRESS, UNPROVEN

Branch `opus-r14b-relabel` (from `opus-r13-p5-nnue-data`). Own code `relabel2.py`; unchanged copies of R13's probe
client `forge_probe.py` (sha256 980c20cc...) and Astra's `astra/records.py` (from astra-r8-datafilter 8ebcf115,
sha256 444e854e...). Labels come from the R13 probe `C:\o13\p5\forge_data_probe.exe` (sha256 ed76de96..., lock
source d4f4312; transposition table, histories and caches cleared before every search). Engine NNUE decides whether
any of these labels are used; nothing here is a strength claim. The 50M run is not started.

## What R13 had and what is new
| R13 / R14 P5 (`opus_r13/p5/`) | R14-B `relabel2.py` |
|---|---|
| input .pos + FEN sidecar (sidecar fix proven on 1,000 rows) | input = self-play text (`FEN | stm cp | white result`) or Astra normalized JSONL: the original FEN with castling / en passant / clocks is the input itself |
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
| found by that test, fixed after the proof (relabel2.py is frozen while the proof runs): for normalized input rows.tsv records the JSONL line instead of the record's own source / source_row, and a change of the record's source is not a game boundary by itself (it was in the first, non-streaming version) | PENDING (after the proof is assembled) | - |
| 1M sample prepared twice (jobs A and B, `prove_resume.sh prepare`): `forge_selfplay_001.txt` (466,506 lines) + the start of `_002.txt`, cut at a game boundary | **999,921 rows in 10,880 whole games**; train 991,077 rows / 10,781 games, validation 8,844 rows / 99 games (1 % of games); game length 2-276 (median 85, p99 227); every game starts at ply 8-15 (no fragment); 0 terminal positions; rows.tsv A = B byte for byte (sha256 eefb1662...); 21 min wall for both at Idle next to BelowNormal training | `D:\o14b\r2\proof\job{A,B}\prepare.json` |
| 1,000,000-row proof: A uninterrupted vs B hard-killed twice and resumed. Both kills are self-inflicted hard exits (os._exit from a watchdog thread at an arbitrary moment: no cleanup, no flush), because the session permissions block terminating processes and stopping a background task ends only its outer shell. Code frozen for the proof: relabel2.py sha256 5c88438f... (in both jobs' run_config.json) | RUNNING since 14:23 (A on CPU 2, B on CPU 3, Idle, 1 probe each). Exit 1: session 1 ended with 137 at 14:48:59 inside shard 14 (14 published); `shard_00014.part.1` kept, session 2 started 14:49:01 and redid it as `.part.2`; no orphaned probe (only run A's and session 2's alive). Exit 2: session 2 ended with 137 at 15:34:20 inside shard 36 (36 published); `shard_00036.part.1` kept, session 3 started 15:34:20 and redoes it as `.part.2`; 20 s later only two probes alive (pid 3052 under run A's python 9568, pid 9372 under session 3's python 7980): none left behind by session 2 (python 13856). Session 3 runs to the end (~17:40) | `D:/o14b/r2/proof`, runB.log, job sessions.log |
| RELABEL_HANDOFF.md (positions / hour, 50M cost) | TODO | - |

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
| Forge's own converter takes the output: `F:\opus_scratch\rescore_d8\bin\fen2bin.exe in.txt out.pos` (the self-play text -> FPOS tool) on `final/train.txt` of the dev test job (1,200 rows, 20k-node labels) | `lines=1200 records=1200 bad=0`; in the .pos (FPOS: 16-byte header, 32-byte boards, int16 scores, meta) the score column equals the new labels 1,200 / 1,200 (1,180 of them differ from the old score), side to move 1,200 / 1,200, result 1,200 / 1,200 (tokens `1.0` / `0.0` / `0.5` kept as in the self-play file) | D:\o14b\r2\conv_check |
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
  `verify_shard`, `load_prepare`, `write_new`, `write_status`, `append_log`, `file_hash`, `lower_priority`, `new_game`,
  `board_stats`. In `cmd_run` only the job lock, the tool-hash pin and the two log lines differ (the shard loop with
  its `.part.N` attempts and the publish rename is unchanged); `cmd_assemble` only gains the lock and writes the
  manifest before the rename. `cmd_prepare` / `iter_rows` changed (input checks, one input stream, `--jobs 2`).
- What the bridge proves (`bridge_check.sh`, after `finish`): prepare of the proof's sample with the post-proof code
  gives the proof's rows.tsv byte for byte with `--jobs 1` and `--jobs 2`; `run --accept-new-tool` re-verifies all
  100 published shards of a copy of job A; `assemble` on that copy gives job A's train.txt / val.txt / labels.tsv.
- What the dev tests prove on the post-proof code itself: the mini kill / resume (1,200 rows, 20k nodes, a hard exit
  inside a shard) gives byte-identical final files, plus every exit-code case.
- Thread-budget note (honest record): the dev test runs at 15:22, 15:38, 15:43 and from 15:48 ran as a third Idle
  process on CPUs 2-3 next to the two proof probes (inside the 2-CPU mask, but three processes, over the "<= 2
  threads" rule); nothing further CPU-bound is started until the proof ends.
