---
name: boardstm-overlap-triage
description: Use when a Forge train/holdout position scan reports shared board+side-to-move keys and you must list every shared row, classify each pair (en-passant formatting, real en-passant, castling) and recount the overlap with a legal-capture-only en-passant field, or when you must read or re-check a PROBE.json / TRIAGE json / SHARED.jsonl record under D:\a14\sep.
---

# Board+stm overlap triage (R14 finish Job 2)

Three own tools under D:\a14\tools (standard library + numpy; python-chess only as a test oracle):
`opus_ep.py` (EP normaliser), `opus_boardstm_probe.py` (independent fast probe that lists every shared key with all
rows), `opus_boardstm_triage.py` (pair classifier + EP-normalised recount). Every command below runs with the R14
runtime at Idle on CPU 2 through the launcher; `LOW` stands for
`D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_lowrun.py --mask 0x4 -- D:\a14\runtime\python\python.exe -I -B`.
Inputs (D:\grok-pc-data\selfplay_out, D:\a14\evidence\r14\input-pins-all.jsonl) are read-only; outputs go to a NEW
folder below D:\a14\sep (every tool refuses an existing --out).

## Commands (checked 2026-11-04: --help of all three tools and the unit tests in a suite run; steps 2-4 were not re-run, their 2026-11-04 records were re-verified instead)

1. Unit tests first (seconds):
   `LOW -m pytest D:\a14\tests\test_opus_ep.py D:\a14\tests\test_opus_boardstm_probe.py D:\a14\tests\test_opus_boardstm_triage.py -q -p no:cacheprovider --basetemp <new folder under D:\a14\evidence\test_logs\r14>`
2. Probe (production defaults: holdouts 013 + 014, train 001-039 without 013/014, the pins file; about 6.5 minutes
   for 305 M train rows, RSS stays below 2 GiB, needs 8 GiB free RAM):
   `LOW D:\a14\tools\opus_boardstm_probe.py --out D:\a14\sep\boardstm-probeNN [--seconds 7200]`
   Fixture runs: add `--holdout <file> --train <file> --train <file> --pins <pins.jsonl>` (each repeatable).
3. Triage of the listing (seconds):
   `LOW D:\a14\tools\opus_boardstm_triage.py --probe D:\a14\sep\boardstm-probeNN\PROBE.json --expect <keys>,<train_rows>,<holdout_rows> --out <new .json> --rows <new .tsv>`
   Add `--report <r14_overlap REPORT.json that carries keys.board_stm.shared_keys>` to cross-check both listings; they
   must be identical or the triage is UNVERIFIED. `--expect` takes the production scan's counts (2026-11-04:
   `7610,7700,7612`).
4. EP self-check of the normaliser against the oracle on a real file (only the EP field is compared):
   `LOW D:\a14\tools\opus_ep.py --oracle D:\grok-pc-data\selfplay_out\forge_selfplay_013.txt --limit 300000`

## Reading PROBE.json

- `status` COMPLETE and `problems` empty, else nothing below counts. `complete` false + `error` = the probe stopped
  (pin mismatch, a row without six FEN fields, deadline, RAM/RSS/disk guard).
- `receipts[]`: per file `actual_md5` must equal `pin_md5`, `unchanged` true, `bad_rows` 0 (size and mtime are
  compared before and after the read).
- `shared_exact_keys`, `train_overlap_rows`, `holdout_overlap_rows`, `hash_candidate_train_rows`,
  `hash_collision_train_rows` (hash hits that were not exact matches; 0 on 2026-11-04). `holdout_unique_keys` is the
  index size.
- `ep_census[file]`: `ep_rows` = rows with an EP square, split into `legal` / `no_capture` / `invalid`. (`none` is a
  placeholder that stays 0.) About 3.6 % of rows carry an EP square and about 98 % of those allow no capture: the
  producer writes the square after every double pawn push.
- `shared_listing` = SHARED.jsonl (one line per key: `key` = raw "placement side", `train` and `holdout` rows with
  path, line, fen) and its md5; the triage refuses the listing if that md5 changed.

## Reading the triage json

- `status` COMPLETE only when: totals equal `--expect`, listings agree (if two), no `invalid_ep` pair and no
  `identical_4field` pair. Otherwise UNVERIFIED with `reasons` - never "fix" an invalid EP square by hand.
- Classes per key (`keys_per_class`) and per train x holdout pair (`pairs_per_class`):
  `ep_format_diff` = raw EP fields differ but both normalise to the same field (same chess position);
  `real_ep_diff` = after normalisation they still differ (one row allows a legal en-passant capture);
  `other` = castling rights differ (`key_reasons.castling_diff`), `mixed` pairs, or the two fail-closed cases.
- `normalised_4field_recount` = shared keys / train rows / holdout rows on board + side + castling (KQkq order) +
  legal-capture-only EP. This is the exact recount over all rows because a normalised 4-field match implies a
  board+stm match and the board+stm listing is complete.
- `raw_ep_patterns`, `per_holdout_file`, `per_train_file`, `per_piece_count` are breakdowns; the `--rows` TSV has one
  line per listed row (key, class, reason, side, path, line, fen, ep_status, normalised_4field).
- 2026-11-04 result (sep\boardstm-probe01\TRIAGE_probe_only.json): 4,070 ep_format_diff + 8 real_ep_diff + 3,532 other
  (3,514 castling_diff, 18 mixed) = 7,610 keys; EP-normalised recount 4,088 keys / 4,118 train / 4,090 holdout rows.

## Why the raw "placement side" prefix is an exact key

Every pinned file was parsed with key fill rate 1.0 by r14_scan.parse_row, which rejects consecutive empty-square
digits and wrong rank widths, so each raw placement string is the unique FEN spelling of its board. The probe hashes
`placement + " " + side` bytes and resolves every hash hit by comparing the exact strings. The triage expands digits
to dots (`expanded_key`) only to compare with r14_overlap's listing keys.

## Pitfalls

- Python `hash()` differs per process: hashes are never written, only exact keys and (path, line, fen).
- `--out` must be a new folder below D:\a14; `--rows` of the triage overwrites an existing file (use a new name).
- A raw 4-field PASS is not a position-identity PASS: rows that differ only in a non-capturable EP square are the
  same position (see the recount). Castling-right differences stay "other": they are different positions.
- The probe counts a row that does not split into six fields as bad and ends INCOMPLETE; check the pins file first.
- Keep SHARED.jsonl with its md5: opus_guardband.py takes it (`--shared`, `--shared-md5`) to drop every train row whose
  board+stm key is shared with the holdouts.
