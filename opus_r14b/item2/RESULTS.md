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
| 1,000,000-row proof: A uninterrupted vs B hard-killed twice and resumed. Both kills are self-inflicted hard exits (os._exit from a watchdog thread at an arbitrary moment: no cleanup, no flush), because the session permissions block terminating processes and stopping a background task ends only its outer shell. Code frozen for the proof: relabel2.py sha256 5c88438f... (in both jobs' run_config.json) | RUNNING since 14:23 (A on CPU 2, B on CPU 3, Idle, 1 probe each). Exit 1: session 1 ended with 137 at 14:48:59 inside shard 14 (14 published); `shard_00014.part.1` kept, session 2 started 14:49:01 and redoes it as `.part.2`; no orphaned probe (only run A's and session 2's alive). Exit 2 due ~15:34 | `D:/o14b/r2/proof`, runB.log, job sessions.log |
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
