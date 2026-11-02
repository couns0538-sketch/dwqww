# R13 Phase 5 - relabel pipeline - job1 STOPPED (labels on reconstructed FENs); R14 fix PROVEN on 1,000 rows (UNPROVEN as data)

Branch `opus-r13-p5-nnue-data` (from main). No Elo claim; Engine NNUE decides whether any of these labels are used.

## What job1 did (R13, run id r13p5-20261101-a)
| item | value | evidence |
|---|---|---|
| input | Astra's filtered 10M slice `D:\grok-pc-data\r11_nnue\astra\forge_filtered.pos` (FPOS v1, 9,206,371 rows, sha256 2019bf8e560e4821...) | logs/job1_job.json |
| probe | `C:\o13\p5\forge_data_probe.exe` (forge_data_probe.cpp built on the lock source d4f4312, znver5, static; TT + histories + caches cleared before every search) | logs/job1_job.json |
| settings | 20,000 nodes, Hash 1 MB, 1 worker (= 1 thread), CPU 3 (mask 0x8), Idle, shards of 20,000 rows | logs/job1_job.json |
| run | started ~11:10 PC clock 2026-11-01 (02:10 PT), stopped itself through `--until` at 12:25:07 PC clock (03:25 PT) | logs/job1_status.json |
| done | 22 of 461 shards = **440,000 rows** in 4,475.6 s = 353,917 positions/h; per-shard output sha256 in shards.tsv | logs/job1_status.json, logs/job1_shards.tsv |
| outputs | `C:\o13\p5\job1\shards\shard_00000 .. shard_00021` (.pos / .hce / .fen + manifest), kept, nothing deleted | - |

**The 440,000 job1 labels were searched on RECONSTRUCTED positions.** The .pos format stores only board, side to move,
score and result; without the FEN sidecar the job used `--allow-reconstructed` (forge_pos.board_to_fen policy
`no-castling-no-ep-clocks-0-1`): every position lost its **castling rights**, its **en-passant square** and its **halfmove
clock** (fullmove set to 1). summary.json of every job1 shard says `state_origin: reconstructed_no_castling_no_ep_clock0`,
`exact_label_rows: 0`. Measured on the original FENs (audit below): 360,474 of the 440,000 job1 rows (81.9 %) had state that
was lost - castling rights 96,839 (22.0 %), en passant 15,756 (3.6 %), halfmove clock > 0 311,454 (70.8 %). Engine NNUE
decides whether the old labels are usable; they are not deleted or overwritten.

## R14 fix: carry the original FEN through
- The original FENs exist: Astra's release archive (`D:\grok-pc-data\r11_nnue\astra_dl\forge_astra_a1_data_results_20261030.tar.gz.part000000/1`)
  has the member `completed/full10m/forge_filtered.fen`, which R11 did not extract. extract_sidecar.sh: whole archive
  sha256 148803c5a45a5e291c18f667b918100ec1fa1a8e08d5a74dfe430651b3f1418f (= Astra's receipt), only that member streamed
  (`tar --occurrence=1`) to `D:\o14a\p5\forge_filtered.fen.part`, sha256 beb3c31d377d4f5f610c2fa2b877fe434177230197e074ee54a35b59f7d41c97
  and 483,989,105 bytes (= Astra's manifest), then renamed; 9,206,371 lines; 15 s at Idle on CPUs 2-3 (logs/extract_sidecar.log).
- The relabel tools already had the right path: `relabel_job.py run --sidecar <fen> --sidecar-origin original_full_fen`
  (relabel_positions checks board + side to move of every selected row against the .pos, that the sidecar has exactly the
  .pos row count, and that the engine's echoed FEN equals the requested FEN). job1 simply ran without the sidecar.
- Code change (relabel_job.py): a NEW job refuses `--allow-reconstructed` unless `--accept-lossy-labels` is also given;
  job.json and status.json now record `state_origin`. The existing resume check already pins sidecar / origin /
  allow_reconstructed per job dir, so one job dir cannot mix origins (job1 stays resumable as it was).
- New tool prove_sidecar.py (own code): `audit` (all rows) and `compare` (fixed vs old labels).

## Proof (2026-11-02, run_fix1k.sh, Idle, CPUs 2-3)
| check | result | evidence |
|---|---|---|
| guard: new job with `--allow-reconstructed` and no `--accept-lossy-labels` | refused, exit 1, no job dir created | logs/run_fix1k.log |
| fixed relabel, rows 0-999 (fresh job `D:\o14a\p5\job_fix1k`, run id r14p5-20261102-fix1k, 20k nodes, 1 worker, Hash 1 MB) | exit 0, 11.9 s; `state_origin: original_full_fen`, `exact_label_rows: 1000` | logs/job_fix1k_*.json |
| (b) engine FEN echo = requested original FEN | 1000 / 1000 (the relabel run aborts on the first difference) | logs/run_fix1k.log |
| new output .fen = sidecar lines 0-999 | 1000 / 1000 | logs/compare_fix1k.json |
| (c) rows 0-999 with state the reconstruction loses | 841 (castling 211, en passant 35, halfmove > 0 737); job1's reconstructed FENs of the same rows: 0 with castling or ep | logs/compare_fix1k.json |
| (d) control rows (no castling, no ep, halfmove 0: the old FEN differs only in the fullmove number) | **159 / 159 identical labels** (the fixed path changes nothing else) | logs/compare_fix1k.json |
| (d) affected rows: label changed | 208 / 841; mean abs delta 6.16 cp, median 0, max 231; castling rows 199 / 211 changed (mean 22.9, median 17, max 231); ep rows 21 / 35 (mean 12.1); halfmove rows 123 / 737 (mean 4.3) | logs/compare_fix1k.json |
| full alignment audit, all rows: sidecar board + side to move = .pos record, row count equal | **9,206,371 / 9,206,371 PASS** | logs/audit_full.json |
| state lost by reconstruction, whole file | any 7,534,409 (81.8 %): castling 2,045,996, ep 331,705, halfmove > 0 6,499,246 | logs/audit_full.json |
The 1,000 fixed labels are in `D:\o14a\p5\job_fix1k\shards\shard_00000` (scratch; hashes in logs/job_fix1k_shards.tsv).
A new full relabel run is not part of R14 (Couns: no relabel-run work); the command for it is
`relabel_job.py run --pos <pos> --probe <probe> --job <new dir> --run-id <id> --sidecar D:\o14a\p5\forge_filtered.fen --sidecar-origin original_full_fen [--until ...]`.

### Review milestone R14-P5-1 (structured self-review, NOT independent - no sub-agents in R14)
- Reviewed: relabel_job.py diff, prove_sidecar.py, the run log and both result files; candidate = data tooling only
  (no engine change; probe exe unchanged, sha256 in job.json).
- Findings: (1) my first guard created the job dir before refusing - fixed before the run (mkdir after the guard; the guard
  check shows "job dir created: no"). (2) relabel_positions re-reads the whole 484 MB sidecar for every shard (it streams
  to the selected rows): fine for this proof, ~5-10 s per 20k-row shard in a full run - noted, not changed (Astra's code,
  unchanged copy). (3) prove_sidecar compare reads the first start+count sidecar lines into memory: fine for 1,000.
- Checks after: run_fix1k.sh results above. Next: none for P5 in R14 (Engine NNUE decides on old vs new labels).

### Review milestone R14-P5-2 (20-minute review pass, structured self-review, NOT independent)
- Reviewed again: relabel_job.py, prove_sidecar.py, this file's claims against the logs, the skill text.
- Found + fixed: (1) relabel_job.py wrote `state_origin: original_full_fen` for ANY --sidecar, also with
  `--sidecar-origin reconstructed` (a relabeler-emitted reconstructed .fen) - now reconstructed / original_full_fen / auto
  follow --sidecar-origin (the shard summaries were always right; only the job-level label was affected; job_fix1k used
  original_full_fen, so its records are correct). Re-checked: script parses, the guard still refuses a new
  --allow-reconstructed job (exit 1, no job dir). (2) Skill forge-nnue-data said "changes 81.8 % of rows" - it is 81.8 % of
  rows that LOSE state (labels changed for 208 / 841 affected rows in the sample): reworded.
- Verified claims: all 22 job1 shard summaries say `reconstructed_no_castling_no_ep_clock0`; job1 created 11:10:32 PC clock.
