---
name: guardband-split-proof
description: Use when building a contiguous guard-band train/validation split of relabelled Forge self-play rows (jobA) at an UNREACHABLE chain link, proving such a split independently against holdouts 013/014, writing sep\GUARDBAND_SEPARATION.json, or deciding whether the staged export may be promoted; also when reading SPLIT.json / PROOF.json / DROPPED.tsv.
---

# Guard-band split and proof (R14 finish Job 3)

Flow: build (`opus_guardband.py`) -> independent proof (`opus_guardband_proof.py`) -> record
(`opus_guardband_record.py`) -> owner-only promotion (`opus_promote_export.py --confirm-owner-decision`).
`LOW` = `D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_lowrun.py --mask 0x4 -- D:\a14\runtime\python\python.exe -I -B`
(R14 runtime, Idle, CPU 2, GPU hidden). Inputs are read-only and md5-pinned inside the tools: D:\o14b\r2\proof\jobA\rows.tsv,
...\final\labels.tsv, D:\a14\sep\segments-joba01\REPORT.json (+ its pairs maps), the probe listing SHARED.jsonl.
Large outputs go to C:\a14x (D:\a14 stays under 5 GB).

## Commands (checked 2026-11-04: --help of all four tools, the promotion refusal without the flag, verify-report on PROOF.json; steps 1-3 were not re-run, their guardband01 records were re-verified instead)

1. Build (seconds; writes SPLIT.json + DROPPED.tsv into a NEW --out, candidate rows into a NEW --stage-dir):
   `LOW D:\a14\tools\opus_guardband.py --out D:\a14\sep\guardbandNN --shared D:\a14\sep\boardstm-probe01\SHARED.jsonl --shared-md5 ea9d1e3024daf1fe0a3e70d11207e36b --stage-dir C:\a14x\guardbandNN_stage [--k 8] [--val-fraction 0.01]`
2. Proof (about 11 minutes: re-reads both holdouts twice; needs 8 GiB free RAM and 50 GiB free on C: and D:):
   `LOW D:\a14\tools\opus_guardband_proof.py --split D:\a14\sep\guardbandNN\SPLIT.json --out D:\a14\sep\guardbandNN\PROOF.json --big-dir C:\a14x\guardbandNN_proof`
   Exit 0 only when every scoped check is PASS and no input changed.
3. Record (fixed paths: sep\guardband01\SPLIT.json + PROOF.json -> sep\GUARDBAND_SEPARATION.json; refuses an
   existing file; edit the three constants for another run folder):
   `LOW D:\a14\tools\opus_guardband_record.py`
4. Re-check every md5 cited by a record: `LOW D:\a14\tools\opus_seal.py verify-report D:\a14\sep\guardbandNN\PROOF.json`
5. Promotion is the owner's decision only; without the flag the tool refuses (exit 1):
   `LOW D:\a14\tools\opus_promote_export.py --confirm-owner-decision [--split ...] [--proof ...] [--out D:\a14\export]`

## What the builder does

Rows stay in jobA order (source 001 then 002, contiguous lines - checked). Links between adjacent rows come from the
pinned pairs maps: UNREACHABLE codes 1-3 start a conservative component; REACHABLE / UNKNOWN never do. The cut is the
component start closest to a 1 % validation suffix. Dropped with a reason each (DROPPED.tsv, row ids are 0-based,
line = row_id + 1): `guard_left` / `guard_right` (within K plies of the cut endpoints, via r14_scan.guard_selection;
both cut components must have strictly increasing plies or the tool fails closed), `holdout_board_stm` (key in
SHARED.jsonl), `val_board_stm` (train row sharing a board+stm key with a retained val row), `mate_score`
(|score| >= 30000). SPLIT.json carries input md5s, the cut, components, guard rows, counts, WDL and score histograms,
staged file md5s and `authentic_game_ids: UNVERIFIED`.

## What each proof check proves - and does not

- accounting: every row id is exactly one of train / val / dropped, train < cut <= val, counts equal SPLIT.json.
- payload: every staged row equals rows.tsv (FEN, result) and labels.tsv (score); no mate row.
- holdout: three keys (board+stm, raw 4-field, EP-normalised 4-field) of every row of the complete 013/014 files
  (md5 of every byte = pin, bad rows 0) vs every staged row; hash hits are resolved exactly.
- train_val: no staged train row shares one of the three keys with a staged val row.
- chain: the cut link is UNREACHABLE; the components are re-derived from the maps; every retained row of the two cut
  components is more than K plies from its endpoint. Scope: observed adjacent-row links only - nothing about
  interleaved games, omitted continuations or non-adjacent relations.
- audit: npt-data-holdout-check audit_exports.py on JSONL exports (source, train, both holdouts). game_id is null for
  every row, so the audit returns UNVERIFIED (exit 2); only its failure counters (position, game, state) are usable.
`scoped_checks` PASS = the five checks; `audit_failure_counters_zero` = the audit counted nothing.

## Why the verdict stays UNVERIFIED

No row of forge_selfplay_001-039 carries an authentic game ID (sep\WRITER_EVIDENCE.md). r14_scan.final_verdict with
authenticated=False cannot return PASS, and the audit cannot either. The record therefore says status UNVERIFIED,
scoped_checks PASS, export not built; the owner decides whether that evidence suffices for training.

2026-11-04 numbers (sep\guardband01): cut row 989,931 = forge_selfplay_002.txt line 523,426 (nonpositive_ply_gap,
UNREACHABLE); 987,194 train / 9,951 val / 2,776 dropped (5 guard_left, 7 guard_right, 47 holdout_board_stm,
2,685 + 32 mate_score); min retained ply distance 11 / 9 (K = 8); audit rows 17,385,720, all without game_id.

## Pitfalls

- The input pins (paths + md5) are constants in opus_guardband.py; a new jobA needs new constants, never a bypass.
- SPLIT.json, PROOF.json and the record are written with mode 'x': pick a new folder or a new name, never delete.
- The record tool reads guardband01 by constant; check `evidence.proof.md5` against `md5sum PROOF.json`.
- opus_promote_export.py refuses unless scoped_checks is PASS with no problems, `audit_failure_counters_zero` is true
  (review finding F-014: the audit's position / game / state counters must all be 0), SPLIT.json still has the
  proof's md5 and every staged file still has its SPLIT.json md5; the rules are `check_proof()` and are tested on
  fixtures by tests\test_opus_promote_export.py. The audit's own status stays UNVERIFIED while game_id is null.
- The proof's holdout pass writes 16.4 M JSONL rows to --big-dir (about 1.5 GB); keep it on C:\a14x.
- A proof PASS is about separation of the staged rows; it is not a training-gain or Elo claim.
