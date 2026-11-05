# R14 finish: production overlap triage, jobA guard-band split, review, tests and the owner's fix list

Finished by Opus for Astra's R14 (Astra is out of usage). Branch `opus-astra-r14-finish`, created from
`7636122b71ff27a5b4b781b6775757f926f8fdc4` (tip of `astra-r14-20261103`, which was not rewritten). Work dir `D:\a14`;
big outputs in `C:\a14x`. Repository: https://github.com/couns0538-sketch/dwqww/tree/opus-astra-r14-finish
This file replaces the R13 report that the branch inherited at `FINAL_REPORT.md` (R13 copy, 9,305 bytes, md5
e9132aa24b6563326e3c45bd6110e144 at 7636122b; its content stays in the history).

Last content commit of the branch: `179430bd73cfe2097b3657bca60037942eb97886` (17:52 Vienna). The final head is the commit that adds
this report; a file cannot carry its own md5 or its own commit hash, so both are given in the hand-back message and
can be read with `git -C D:/a14 log -1` and `git -C D:/a14 ls-remote origin refs/heads/opus-astra-r14-finish`. A first
version of this report (commit 3daa18ffa6c5294972f878243178a91c6d93871d, 14:06, pushed at 14:07) is superseded by this
one as a new commit - two verify statements of the fix-list table were corrected after running them literally - with no
history rewritten; every other file is identical in both commits.

Times (Vienna = PC clock, every figure from the clock or from commit times): Astra's R14 started 2026-11-03 12:41:11
(evidence/R14_PROGRESS.md). This finish: Step 0 2026-11-04 09:20 (PLAN.md), first commit aa78a56 09:24:54; the owner's
fix list (items 0-8, `C:\a14x\cr_fixlist_20261104_from_owner.txt`, md5 ab620242623a045eba6500357802bc3c) arrived at
13:27 and moved the hard end to 18:15; fix commit 87ef93ee 13:45:35; last content commit 17:52; this report
written 2026-11-04 17:54:00 (`date` at the final write). No training, no GPU, no engine change, no production-data change, no
rating claim.

## Is the npt data unblocked?

**No.** The overlap is not resolved. Three independent reasons, each from a sealed record:

1. **Position overlap (FAIL).** The npt training rows (forge_selfplay_001-039 without 013/014: 304,999,573 rows) share
   7,610 board+side-to-move keys with the holdouts 013/014 (16,388,575 rows): 7,700 train rows and 7,612 holdout rows,
   7,700 hash candidates, 0 hash collisions, key fill rate 1.0 on both sides. The raw 4-field key shares 0 keys, but
   that "PASS" is an en-passant formatting artefact: with the en-passant field kept only when a legal capture exists,
   **4,088 of the 7,610 keys are still shared** (4,118 train rows, 4,090 holdout rows). Record:
   `D:\a14\sep\PROD_SEPARATION.json` (md5 3bccfa9b074a3050d436f08a29dd1b7e, status **FAIL**, schema 2, regenerated
   13:43 at the tip by `tools\opus_prod_separation.py --replace-committed`; the raw key is labelled inside the record as
   "PASS on the raw 4-field key only ... an en-passant artifact, not a separation PASS"; the 11:14 version, md5
   75956771b88f4c30898f5a895b7a18c5, stays in the history).
2. **Game identity (UNVERIFIED).** No row of 001-039 carries an authentic game ID, so game-level separation is
   UNVERIFIED for every split, including the guard-band candidate.
3. **jobA guard-band candidate (UNVERIFIED).** Every scoped check passes (`D:\a14\sep\GUARDBAND_SEPARATION.json`, md5
   1b4b901e91f03622d94df39907ba5f2e: scoped_checks PASS, status UNVERIFIED), but the npt-data-holdout-check audit cannot
   return PASS when game_id is null for all 17,385,720 rows. The candidate covers only the 999,921-row jobA set. No
   export was delivered: `D:\a14\export` was not created (a tool test of the promotion command left a copy of the
   staged candidate at `C:\a14x\promote_tooltest01`, see Job 3). The owner decides whether guard-band evidence is
   enough; the one command that promotes the staged candidate is
   `D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_promote_export.py --confirm-owner-decision`, and it was
   not run in this job.

What would clear (1): drop the 7,700 listed train rows (path and line of every one in
`D:\a14\sep\BOARDSTM_TRIAGE_ROWS.tsv`, md5 ec05042753b0f4466e36dfc0a148c064) and rebuild the npt data. That was not
done here. Nothing here can clear (2) for the existing shards; `D:\a14\sep\GAMES_SIDECAR_PROPOSAL.md` (md5
5a911c209c7d3039fbbd1d33311274ea) covers future data.

## Verdicts (every number read from the named record)

| check | scope | result | fill rate | status | record (md5) |
|---|---|---|---|---|---|
| board+stm overlap | 304,999,573 train rows vs 16,388,575 holdout rows | 7,610 keys / 7,700 train / 7,612 holdout rows, 7,700 hash candidates, 0 collisions | 1.0 / 1.0 | FAIL | overlap-production03 REPORT.json (1607d19e2b66dbe3512d0997942523c4); full-listing re-scan overlap-production04 REPORT.json (d74118d6690d3af75838f62fc605e73f): same counts, listing_complete true, 5,758 s; independent probe boardstm-probe01 PROBE.json (ef049b82dce36eeb92e8434467612af6): same counts, 388.1 s |
| raw 4-field overlap | same | 0 keys | 1.0 / 1.0 | an en-passant artefact, not a PASS (next row) | same reports; labelled in PROD_SEPARATION.json (four_field_raw) |
| EP-normalised 4-field overlap | same, exact over all rows | 4,088 keys / 4,118 train / 4,090 holdout rows | 1.0 | FAIL | BOARDSTM_TRIAGE.json (e18f8fe3dd2880f9d3d1235278abfd84), folded into PROD_SEPARATION.json (four_field_ep_normalised) |
| production chain scan | 013 + 014 in full (10,000,000 + 6,388,575 rows), 100,000-row edges of 012 and 015, K = 8, node limit 100,000 (boundary 1,000,000) | 293,783 segments (293,784 ranges); adjacent pairs 16,294,792 REACHABLE (legal_witness) / 189,211 UNREACHABLE (result_mismatch 121,467, nonpositive_ply_gap 67,730, exhaustive_no_path 14) / 104,569 UNKNOWN (node_limit 68,112, gap_exceeds_k 36,457) | valid_key_rows = scanned rows in all four sources | UNVERIFIED | segments-production02 REPORT.json (fcb488f8c726326e013f648e1d202760); 25 maps sealed by MAPS_SEAL.json (9b708a8994edc0f87ad8283c783440bb), verify-seal PASS |
| train/holdout file seams | 012 line 2,625,970 -> 013 line 1; 014 line 6,388,575 -> 015 line 1 | both UNREACHABLE (result_mismatch; nonpositive_ply_gap); the 013 -> 014 seam (holdout to holdout) is REACHABLE | - | no observed link at the two seams; adjacent rows only, no all-pairs search | same |
| guard band: holdout overlap, 3 keys (board+stm, raw 4-field, EP-normalised 4-field) | 987,194 staged train + 9,951 staged val rows vs every row of 013 and 014 (md5 = pins, 0 bad rows) | 0 hash candidates, 0 exact rows for every key and side | 1.0 / 1.0 | PASS | guardband01 PROOF.json (04da3cfa633aceeccd89dda67edf6837) |
| guard band: train/val overlap, 3 keys | staged train vs staged val | 0 / 0 / 0 | 1.0 | PASS | same |
| guard band: chain | cut link code 1 nonpositive_ply_gap (UNREACHABLE) between conservative components | 0 cross-split links within K; nearest kept rows 11 (left) and 9 (right) plies from the cut, K = 8 | - | PASS | same |
| guard band: accounting and payload | 999,921 jobA rows | 987,194 train + 9,951 val + 2,776 dropped; 0 payload mismatches, 0 mate rows staged | - | PASS | same; SPLIT.json (f2304604a07ceab3d8baca0da3661a26) |
| npt-data-holdout-check audit | 999,921 source / 997,145 training / 10,000,000 + 6,388,575 holdout rows (JSONL exports under C:\a14x\guardband01_proof) | position, game and state counters 0; 17,385,720 rows without a game ID; exit 2 | - | UNVERIFIED | same (audit.json md5 1556e010d237d3e7b9f952bb50a8a305) |
| authentic game IDs | all data | none exist | - | UNVERIFIED | PROD_SEPARATION.json, GUARDBAND_SEPARATION.json |

## Step 0 and Job 1 - inputs and PC-only work (09:20-09:37)
- Step 0 (09:20-09:25): all seven input md5s matched, and the 25 segments-production02 maps matched their REPORT
  (`opus_seal.py verify-report`, 38 entries). Because two of the seven inputs were changed on purpose by later commits
  (PROD_SEPARATION.json regenerated, PLAN.md time fixed) the check was repeated at 11:29 from the committed blobs:
  `D:\a14\evidence\test_logs\r14\opus-step0-recheck01\output.log` (md5 9fb54b953117ac8c9f7566b39179e28f;
  `tools\opus_step0_verify.py`: "step 0 re-check PASS: 7 files, 0 mismatches", each line names the blob and the pin) and
  `maps_verify_report.log` (md5 89de0eef0029342bc6a8b553bed9e867). The maps log ends with "verify-report FAIL: 38 file
  entries, 2 problems": all 25 maps are exact; the 2 problem lines are the two tool identities the scan recorded
  (`tools\r14_segments.py` 97c8a96a44eeeaacda45e3e4d04938ac, `tools\r14_qualification\qualify.py`
  ea7b9145ff0e3e5549434120eded3358), both changed later in Job 4 (43516dd, 17db812, de1a1cd); the 7636122b blobs of
  both files hash to exactly those recorded md5s (`git show 7636122b:<path> | md5sum`, re-done for this report).
- Job 1 committed the PC-only results as found (aa78a56 09:24): overlap-production03 (REPORT, progress, log);
  segments-production02 (REPORT, progress, stderr, log; the 25 maps total 156,935,550 bytes and stay on the PC,
  listed with bytes, md5 and sha256 in `D:\a14\sep\segments-production02\MAPS_SEAL.json`); R14_OPEN_ISSUES.md;
  RETRY_PLAN.md; milestones; test logs. Astra's untracked tools and tests went in a separate commit (c2e61fe 09:25).
  Test `tmp/` folders are ignored (`.gitignore`).
- `PROD_SEPARATION.json` is generated from the two scan reports and the triage by `tools\opus_prod_separation.py`
  (every number read, none typed; md5-pinned inputs): 09:36 (64d3a7e), 11:14 with the cross-checked triage folded in
  (a9ef81e), 13:43 at the tip with the labelled raw key and the mode-x writer (87ef93ee, owner's items 1 and 2).

## Job 2 - the 7,610 board+stm keys (09:37-11:14)
- (a) `tools\r14_overlap.py` now lists every shared key with all of its train and holdout rows (path, line, raw FEN);
  the listing is withheld, never truncated, when a cap is hit (three tests). The full re-scan
  `D:\a14\sep\overlap-production04\REPORT.json` (started 09:37 on CPU 3 at Idle, 5,758 s, every input md5 = pin, both
  listings complete) and the independent fast probe `D:\a14\sep\boardstm-probe01\PROBE.json` (own second
  implementation: raw-prefix hash index in RAM, exact resolution, md5 of every byte vs the pins, 09:44:42-09:51:10,
  388.1 s) give identical counts, and the triage found the two listings identical key for key and row for row.
- (b, c) Triage `D:\a14\sep\BOARDSTM_TRIAGE.json` (status COMPLETE, no reasons, written 11:13; one row per listed
  train/holdout row in `D:\a14\sep\BOARDSTM_TRIAGE_ROWS.tsv`, 15,313 lines = header + 7,700 + 7,612):

| class (per key) | keys | train rows | holdout rows | pairs | meaning |
|---|---|---|---|---|---|
| ep_format_diff | 4,070 | 4,100 | 4,072 | 4,120 | raw EP fields differ; the same position after legal-capture-only EP |
| real_ep_diff | 8 | 8 | 8 | 8 | a legal en-passant capture exists in one row only |
| other: castling_diff | 3,514 | 3,592 (all "other") | 3,532 (all "other") | 3,574 (all "other") | same board, different castling rights |
| other: mixed | 18 | | | | pairs of different classes under one key |

- EP-normalised 4-field recount: 4,088 keys / 4,118 train rows / 4,090 holdout rows. It is exact over all rows because
  a normalised 4-field match implies a board+stm match and the board+stm listing is complete. The earlier probe-only
  triage (`sep\boardstm-probe01\TRIAGE_probe_only.json`, 09:51) gives the same 4,088, and its rerun with the tip tool
  (`TRIAGE_probe_only_tip.json`, md5 495d50516a677db302396502fe0b09f5, 13:44) reproduces every count.
- Why the raw 4-field count is exactly 0: the writer dedups on a hash of the raw first four FEN fields with one
  seen-hash database per output folder (`sep\WRITER_EVIDENCE.md`) and writes an EP square after every double pawn
  push. Rows that differ only in a non-capturable EP square or in castling rights pass that dedup as distinct positions.
- Every one of the 39 files writes EP squares the same way (PROBE.json `ep_census` per file, row counts from its
  `receipts`): 11,793,425 of 321,388,148 rows (3.67 %) carry an EP square and only 222,407 of those (1.89 %) allow a
  legal capture, 0 invalid EP fields. Train (37 files, 304,999,573 rows): 11,195,835 EP rows = 3.671 %, 98.11 % of them
  without a legal capture; holdout (013 + 014, 16,388,575 rows): 597,590 EP rows = 3.646 %, 98.12 % without a legal
  capture (013: 3.643 %, 014: 3.652 %). Per file the EP share ranges 3.51-3.76 % and the no-capture share 98.03-98.22 %.
  So QA's "always vs legal-only writers" hypothesis (a writer that records EP only when a capture is legal) is not
  supported: train and holdout files were written by the same rule.
- QA's "all 3-7 piece endgames" came from the 100 examples that `tools\r14_overlap.py` publishes per key kind:
  `sorted(matched[name])[:100]` (line 155) over the board+stm key bytes, which are the 64 expanded squares with `.` for
  an empty square (`tools\r14_scan.py`, EXPAND) followed by the side; `.` (0x2E) sorts before every piece letter, so
  boards with empty top ranks - endgames - come first. The full `per_piece_count` in `sep\BOARDSTM_TRIAGE.json` over all
  7,610 keys shows the real spread: ep_format_diff keys are mostly 3-7 pieces (2,525 keys) or 32 pieces (1,241 keys);
  the castling-rights keys lie between 19 and 32 pieces (openings and early middlegames, 2,337 of them at 32 pieces).
  Per holdout file: 013 has 2,471 ep_format_diff / 4 real_ep_diff / 2,210 other rows; 014 has 1,601 / 4 / 1,322.

## Job 3 - jobA guard-band split (09:52-10:24; plan `sep\GUARD_BAND_PLAN.md`)
- Built by `tools\opus_guardband.py` (09:52:24-09:52:29): a contiguous split of the 999,921 pinned jobA rows
  (inputs pinned in SPLIT.json: `D:\o14b\r2\proof\jobA\rows.tsv` md5 57a6742279339282763dff17e97670ce and
  `D:\o14b\r2\proof\jobA\final\labels.tsv` md5 2614e82d55bc5e9572c24d3900a8810a - R14-B outputs outside D:\a14, read
  only; chain map report `D:\a14\sep\segments-joba01\REPORT.json` md5 77b76a460e569e50196da08f083e95d4, unchanged on
  this branch; probe listing `D:\a14\sep\boardstm-probe01\SHARED.jsonl` md5 ea9d1e3024daf1fe0a3e70d11207e36b), 10,880
  conservative components, cut at row 989,931 (forge_selfplay_002.txt line 523,426; an observed UNREACHABLE link,
  ply 123 -> 8; validation target 9,999 rows).
  - Guards drop 5 train and 7 val rows (K = 8 plies inside the two cut components, plies strictly increasing).
  - 47 train rows share a board+stm key with 013/014 (the complete Job 2 listing); 0 train rows share a key with the
    kept val rows.
  - Mate rows dropped: 2,685 (train) + 32 (val) = 2,717, the same count R13 flagged for the jobA rows ("2,717 new and
    1,001 old" at `abs(score_stm) >= 30000` in the R13 report, `git -C D:/a14 show 7636122b:FINAL_REPORT.md`); 0 mate
    rows are staged.
  - Kept: 987,194 train, 9,951 val; dropped 2,776, every one by id and reason in `D:\a14\sep\guardband01\DROPPED.tsv`
    (md5 b134521039739137e02d59e2eb7f4fd5). Record `D:\a14\sep\guardband01\SPLIT.json` (f2304604a07ceab3d8baca0da3661a26).
- Proved by a separate tool, `tools\opus_guardband_proof.py` (09:55:11-10:06:06, 654.5 s; reads only pinned inputs and
  the staged rows, shares no state with the builder): accounting, payload, holdout 3-key, train/val, chain and the
  npt-data-holdout-check audit - scoped checks PASS, audit UNVERIFIED (exit 2, all failure counters 0, every row
  without a game ID). Result `D:\a14\sep\guardband01\PROOF.json` (04da3cfa633aceeccd89dda67edf6837, produced by the
  3b43d18 build of the tool, see `sep\TOOL_MD5_CHAIN.md`); record `D:\a14\sep\GUARDBAND_SEPARATION.json`
  (1b4b901e91f03622d94df39907ba5f2e, written 10:24; verdict by r14_scan.final_verdict with authenticated=False).
- Export: no export was delivered - step 6 needs a PASS proof, and `D:\a14\export` (the tool's default output) was not
  created. The staged candidate is `C:\a14x\guardband01_stage` (train.txt 2ab776b02dc100c52d4a741bcd3c6fa0,
  train.rowids c3171e3882f31cfb1ffd0103548c06bb, val.txt 2b02b68e7f558ea226885ae0c8135c1b, val.rowids
  3edab5f17bfc86406f5aecd11e64e622; every md5 re-checked by the proof and by `opus_seal.py verify-report`). A tool test
  of the promotion command (`--confirm-owner-decision`, 10:24) wrote a byte-identical copy of those four files (same
  four md5s) plus `MANIFEST.json` (md5 f4c9028d98101947011be2a560672eec, owner_decision "export promoted by explicit
  --confirm-owner-decision", authentic_game_ids UNVERIFIED) to `C:\a14x\promote_tooltest01`. That folder is a test of
  the tool, not the export: no record references it and nothing used it. It is kept (this job deletes nothing) as a
  PC-only tool-test artifact, marked by `C:\a14x\promote_tooltest01\README_TOOL_TEST_NOT_AN_EXPORT.txt` (written 11:30:
  "TOOL TEST ONLY - NOT AN EXPORT ... Do not use these files for training"), and it is listed file by file in the
  appendix. The owner may discard the folder. The promotion command was not run again after 10:24 (owner's rule).
- Step 7: `D:\a14\sep\GAMES_SIDECAR_PROPOSAL.md` (text only; nothing in the self-play writer changed; it now states the
  4,088-key residual overlap and that the npt data stays BLOCKED).

## Job 4 - QA notes, CR SHOULD, sweep, review, tests
- `tools\r14_qualification\qualify.py --fixture` refuses output in `D:\a14\sep`; the only production launcher never
  passes `--fixture`; consumers require the production scope; three tests (tests\r14_qualification).
- Silent error-swallowing sweep (`tools\opus_silent_sweep.py`; definition: Python `except` bodies that are only
  `pass`, `...` or `continue`; PowerShell empty `catch {}`, `-ErrorAction SilentlyContinue` / `Ignore`,
  `trap { continue }`): 7 sites in R14 files, all fixed (abort paths now report to stderr). After the fix the R14 range
  has 0 sites over 42 scripts (`D:\a14\evidence\r14\opus_silent_sweep_r14_range.json`,
  2620cfee40919426d0cd57828dc5a4f0); the remaining 48 sites in older, non-R14 folders are listed in
  `D:\a14\evidence\r14\opus_silent_sweep_after.json` (46d756edee6119af37ee812194edf7b9). Constructs outside that
  definition (contextlib.suppress, `except: return`) are not covered by the sweep.
- CR SHOULD in `tools\Setup-R14Runtime.ps1`: every download SHA256-pinned (MD5 kept where it existed); the build wheels
  SHA256-pinned and installed with `--no-index`; the main install with `--require-hashes`
  (`tools\requirements-r14-hashes.txt`, 13 pins, each `name==version --hash=sha256:<64 hex>`, made by
  `tools\opus_pypi_hashes.py`). Proof of the 13 pins: `pip download --require-hashes --no-deps --no-build-isolation
  --no-cache-dir -r tools\requirements-r14-hashes.txt -d D:\a14\tmp\r14-wheels-verify01` (R14 runtime, Idle on CPU 2,
  run before 3b43d18 at 10:06) exited 0 with all 13 distributions downloaded and hash-checked by pip:
  `D:\a14\evidence\test_logs\r14\opus-pip-require-hashes01\output.log` (md5 45bd3448f7bc2cfcb1a462a0746e4bc9) and
  `command.txt` (md5 f125861d5d1f77c17cdcdbf05b2d6635). The installed runtime was not touched; the review confirmed
  that the embed zip and get-pip.py on disk match both the MD5 and the new SHA256 pins
  (`evidence\review\r14cont_independent\bytes_check.out`). The new bootstrap-wheel path has not been executed on this
  PC (the runtime predates it).
- Review: reviewer agent started by the owner's allowance, scope 7636122b..0883cee, not covering de1a1cd3 or the
  as-found tools (`D:\a14\evidence\review\r14cont_independent\REVIEW.md`, md5 671fbf66b8d8935afee7df1f5a60b84f, with
  its helper scripts and outputs in the same folder; the correction line of 2026-11-04 states that scope, and PLAN.md
  says the same). No independence is claimed beyond that scope: the commit de1a1cd3 (F-001 fix, F-013, F-014, F-015,
  opus_inventory.py, the three skills) and Astra's as-found tools and tests were not re-reviewed. The author's own
  checks were a structured self-review at each milestone. Findings and dispositions:

| ID | severity | finding | disposition |
|---|---|---|---|
| F-001 | BLOCKER | `[Environment]::SetEnvironmentVariable($k,$null,'Process')` left unset caller variables as "" (Setup-R14Runtime.ps1, R14-OwnedJob.ps1, Invoke-R14Suite.ps1) | fixed in de1a1cd with `[NullString]::Value` (three changed lines, one per file, in the de1a1cd diff); the env-restore test passes (`evidence\test_logs\r14\opus-envrestore-fix-green01\output.log`, 65cc78a98dc11d88d53bbd262ba9a0f7: 7 passed, 1 failed = F-006; `NOTE_FAILURES.md` beside it) and in the final run below |
| F-002 | SHOULD | PROD_SEPARATION.json and the sidecar proposal referenced a triage file that did not yet exist | resolved in a9ef81e: `sep\BOARDSTM_TRIAGE.json` (cross-checked against the production04 listing) and the regenerated PROD_SEPARATION.json; every path cited by the record exists (owner's item 1 verify, 13:43) |
| F-003 | SHOULD | Astra's selected-suite runner (as found) fails its own fixture test under pytest 9.2's built-in subtest accounting; three more of its tests refuse CPU admission when the CPU they pick (cpu_affinity()[0]) is the one the suite itself runs on | accepted, not changed; the runner stays UNVERIFIED; no suite-pass claim is made from it (R14_OPEN_ISSUES.md) |
| F-004 | SHOULD | the prescribed "inherited plus R14" command cannot collect in D:\a14 with the R14 runtime | accepted; this report cites the R14 scope (runs 3 and final, below), never "603 + 60" or D:\a13's 603 |
| F-005 | NIT | two pre-existing tests\r14_native failures against the default native exe (`4k3/8/8/8/8/8/8/4K111` answered UNREACHABLE instead of UNKNOWN; no interactive reply within 2 s); reproducible alone (`full-suite-r14cont01\rerun-single-files\native.log`, 22a07b65ec80226db6d226868b2f3877: 2 failed, 13 passed) | accepted; the default exe is not the pinned r03 exe; not touched by this branch; owner item in R14_OPEN_ISSUES.md |
| F-006 | NIT | test_live_refusal_stops_only_owned_process_tree[guard] fails under the Idle one-CPU launcher (the guard fires after one 500 ms poll before the Idle probe child wrote child.json; parent.json shows the correct refusal and restored environment) | timing, reproducible alone on CPU 2 (`rerun-single-files\runtime_setup.log`, a9f681f3352a1ebcbc41054d2a294a94); final run on CPU 1: still fails on the quiet CPU 1 at Idle (FileNotFoundError: child.json not yet written after one 500 ms poll); accepted as the known timing item |
| F-007, F-009, F-011, F-013, F-014, F-015 | NIT / SHOULD | PLAN.md time, proof docstring, triage --rows mode, assert-based pins in opus_prod_separation.py, promotion without the audit-counter check, top-level-only launcher scan | fixed in de1a1cd (tests of the changed tools: `evidence\test_logs\r14\opus-review-fixes-green01\output.log`, 71240553f423c00a3c284d95e0db05e3, 32 passed; the exact command in `command.txt`, 2fbefeb7ba6b72ccd39d95b192e694a8); the F-014 rules are now `check_proof()` with 5 fixture tests (`tests\test_opus_promote_export.py`, owner's item 7) |
| F-008, F-012 | NIT | eaten spaces in R14_OPEN_ISSUES.md; committed pytest scratch folders | F-008 fixed in 87ef93ee ("has3982", "by100k", "final30-minute"); F-012 as found (Astra's logs) |
| F-010 | NIT | probe EP census key `none` always 0 | harmless, documented |
| F-016 | NIT | sweep definition | stated above |
| F-017 | NIT | TOOLS.md had no section for the new tools | fixed: section "R14 finish helper tools" appended once by `tools\opus_tools_md.py` (between the clock readings 12:36 and 12:45) and refreshed after the item-2 tool change (87ef93ee); `D:\a14\TOOLS.md` is 10,940 bytes, md5 e08fa2572c12fe9991464c119c507faf at 87ef93ee and 89f181ae43a42bbe76422569f5d2d64b after the fix-list-2 refresh in 78d83508; `opus_tools_md.py --check` PASS both times (18 tools, 0 mismatches) |

- Full suite. The prescribed scope `D:\a14\astra_r8\datafilter\tests D:\a14\tests` (the R13 command) cannot be
  collected in one pytest process in this tree with the independent R14 runtime, for three reasons that are all
  outside this branch's diff: the runtime has no torch (the datafilter conftest imports it for every test;
  AGENTS.md forbids protected imports); the module name `filter_positions` exists in astra_r8\datafilter and in
  tools\data; the test basename `test_converter.py` exists in two folders without `__init__.py`. Totals, all through
  `tools\opus_lowrun.py` (Idle, one CPU, GPU hidden), TEMP/TMP = D:\a14\tmp, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1,
  OMP/OPENBLAS/MKL_NUM_THREADS=1, `-q -p no:cacheprovider --basetemp <folder>\tmp`; the exact command of every run is
  in its folder (command.ps1 / command.txt):

| run | scope | result | log (md5) |
|---|---|---|---|
| 1 (prescribed; CPU 2) | astra_r8\datafilter\tests + tests | interrupted at collection: 10 errors, 0 tests run, exit 2 (10:30:19-10:30:21) | `D:\a14\evidence\test_logs\r14\full-suite-r14cont01\output.log` (5e29b6281dc5a8b18eb305d93a44ccb2) |
| 2 (same + --continue-on-collection-errors; CPU 2) | same | 48 failed, 452 passed, 30 skipped, 555 errors, 119 subtests passed, 82.97 s (10:33:19-10:34:42) | `full-suite-r14cont01\run2-continue-on-collection-errors\output.log` (cea1c863645375f42c9059fd981498f8) |
| 3 (R14 scope at 0883cee; CPU 2) | every D:\a14\tests\test_*.py (25 files) + tests\r14_native + tests\r14_qualification (331 tests; list in `selected_files.txt`, 261c954b128ecda36ffbe86aaba4ae60) | 8 failed, 323 passed, 67 subtests passed, 64.44 s (10:37:02-10:38:07); the 8 = F-001 (1, fixed since), F-006 (1), F-003 (4), F-005 (2) | `full-suite-r14cont01\run3-r14-scope\output.log` (371de062db01a986b7c7e30b8b0db081; no commit id in the log, the tree was 0883cee) |
| after the fixes (CPU 2) | tests\test_r14_runtime_setup.py | 7 passed, 1 failed (F-006), 18.10 s | `opus-envrestore-fix-green01\output.log` (65cc78a98dc11d88d53bbd262ba9a0f7) |
| after the fixes (CPU 2) | tests of the changed tools | 32 passed, 0.41 s | `opus-review-fixes-green01\output.log` (71240553f423c00a3c284d95e0db05e3) |
| **final (R14 scope at the tip 87ef93e; CPU 1)** | same selection rule, now 26 test_*.py files (+ tests\test_opus_promote_export.py) + the two folders = 28 paths | **5 failed, 331 passed, 67 subtests passed in 72.10s (0:01:12)** (13:54:30-13:55:42, exit 1) | `D:\a14\evidence\test_logs\r14\full-suite-r14cont02\output.log` (9288da127aa2e43b37a687838c872883; first line = `git rev-parse HEAD` = 87ef93eeab1830f3c1c78c242af6b77d813323e3); command in `command.txt` (daff245380bf6fe6357d4be983d6d61c) |
| rerun after fix list 2 item 7 (tip 78d8350; CPU 6, see the addendum) | same selection rule, 28 paths | **8 failed, 328 passed, 67 subtests passed in 64.54s (0:01:04)** (17:50:11-17:51:16, exit 1) | `full-suite-r14cont03\output.log` (0e607316e0b09f1b746bf56c6d894b30; first line = 78d83508c7291321330ab356f14d8e1a9f8602f5); `command.txt` (d6b82f9ba2cf4ba480ce700139c568e5) |

  Final run triage: 5 failed = F-003 (1: test_r14_suite.py::test_real_pytest_receipts_are_exact_and_fixture_scoped[False], pytest 9.2 subtest accounting; the three CPU-admission cases of F-003 passed this time on the quiet CPU 1), F-005 (2: the two tests\r14_native cases, the default exe), F-006 (1: test_live_refusal_stops_only_owned_process_tree[guard], child.json not yet written when the guard fired) and one NEW environmental failure not caused by the R14 finish: tests\test_r14_preflight.py::test_floor_breach_after_hash_writes_no_receipt (`assert 0 != 0`; neither the test nor tools\Verify-R14Inputs.ps1 changed on this branch and the test passed in run 3). Diagnosis in `D:\a14\evidence\test_logs\r14\full-suite-r14cont02\TRIAGE.md` and R14_OPEN_ISSUES.md: in Windows PowerShell 5.1 Get-FileHash is a function exported by Microsoft.PowerShell.Utility, and the script's `New-Object` line auto-imports that module into the running scope, replacing the test's script-scope Get-FileHash mock with the real function (reproduced alone at 13:59 and by three minimal scripts at 14:00-14:02); the real hashes match every pin, the mocked floor never breaches and the script exits 0. A verified one-line fix (import the two modules before defining the mocks) is proposed, not applied (as-found test outside the R14-finish diff). F-004, F-008 and F-017 are findings, not tests: F-004 accepted, F-008 and F-017 fixed. Run 3's eight failures minus the fixed F-001 and the three admission cases that now pass, plus the new one, give the five.
  CPU check before the final run (read-only, `tmp\opus_cpu01_check.ps1`): at 13:54:05 no forge_ltopgo / fastchess / kit-build process had CPU 0 or 1 in its affinity (CPU 0 14.1 %, CPU 1 9.4 %), which was the coordinator's state condition (the Item B kit build had finished early; at 13:57 the coordinator reserved CPU 1 for this suite and started a sanity match on CPU 0 - after the run); at 13:56:09, after the run, still none (CPU 0 12.4 %, CPU 1 8.5 %).
  Every new or changed test of this branch passed in run 3 and in the final run (test_opus_ep, test_opus_boardstm_probe,
  test_opus_boardstm_triage, test_opus_promote_export, the r14_overlap listing tests, the qualification fixture-guard
  tests, test_r14_boundary*). The inherited launcher tests write receipt folders under
  `evidence\test_logs\r14\launchers\` during a suite run; this run added four receipt folders (`cap-775a1c98f349`, `cap-bf0744e3d3ba`, `launcher-2b23a4050998`, `pipes-c8fb63676302`; command records, empty or 15-byte logs and two 60 KB receipt.json files; their `tmp` subfolders are git-ignored) and the health probes written by test_observation_has_monotonic_clock_on_ps51 (`D:\a14\evidence\r14\health-ps51-1fc845190287.json` from the suite and `health-ps51-d748073904c2.json` from the 13:59 isolated rerun of tests\test_r14_preflight.py), all committed in the same commit as the log, like the reviewer's receipts of run 3.
- Telemetry (`D:\a14\evidence\r14\opus_telemetry.md`, b15163ab1bc4c113f80f78dd168182f6): read-only checks of the npt
  trainer and gate throughput before and during the work; no throttle line was crossed. Free space at draft time
  (11:21): D: 54.9 GB, C: 95.6 GB, RAM 21.2 GB free; at 13:44: D: 52.6 GB, C: 95.6 GB (PLAN floors: D: 50 GB, C: 30 GB,
  owned storage below 5 GB; D:\a14 is 727 MB).

## Owner's fix list of 2026-11-04 (items 0-8; items 9-13 belong to the 30-h job and were not touched)
Source: `C:\a14x\cr_fixlist_20261104_from_owner.txt` (md5 ab620242623a045eba6500357802bc3c, read in full at 13:27).
Rules kept: tooling, evidence and docs only; every fix a new commit (87ef93ee at 13:45:35, then 179430b at
17:52 for the suite log, receipts and counts); nothing pushed was rewritten; the promotion command was not
run. Pre-edit md5s were taken with `certutil -hashfile` and compared with the list's b221b71f blob md5s: PLAN.md
(5eae7d72), REVIEW.md (9a9cab81), SKILL.md (b4b16296) and opus_prod_separation.py (a56624db) matched; PROD_SEPARATION.json
did not (75956771 on disk vs 7ae9cc04 in the list: regenerated at 11:14 in a9ef81e, after the review) and was re-read
before the change; R14_OPEN_ISSUES.md (a485ab07), GAMES_SIDECAR_PROPOSAL.md (6726c6d9), opus_promote_export.py
(fb8a392b) and TOOLS.md (a4389c71 at b221b71f, 7fd51990 after the first append between the clock readings 12:36 and
12:45) have no md5 in the list.

| item | done in | changed files (new md5) | verify output |
|---|---|---|---|
| 0 | 87ef93ee | statement added to `D:\a14\sep\PROD_SEPARATION.json`, `D:\a14\sep\GAMES_SIDECAR_PROPOSAL.md` (5a911c209c7d3039fbbd1d33311274ea), `D:\a14\evidence\R14_OPEN_ISSUES.md`, `D:\a14\R14_STATUS.md` (589debc45017d648baa0f82c5ad955fe) and this report | "shared keys after EP normalisation: 4088 status FAIL" (tmp\opus_item1_verify.py); the overlap is NOT resolved, npt data BLOCKED |
| 1 | 87ef93ee | `D:\a14\sep\PROD_SEPARATION.json` (3bccfa9b074a3050d436f08a29dd1b7e; schema 2; `four_field` renamed `four_field_raw` with status "PASS on the raw 4-field key only (0 shared raw keys): an en-passant artifact, not a separation PASS; EP-normalised FAIL (4,088 keys), see four_field_ep_normalised"); `D:\a14\sep\GAMES_SIDECAR_PROPOSAL.md` (5a911c209c7d3039fbbd1d33311274ea, 4,088 + BLOCKED stated; every file it cites exists: `Test-Path` True at 14:08 for sep\FUTURE_GAME_IDS.md, sep\WRITER_EVIDENCE.md, sep\boardstm-probe01\PROBE.json, sep\BOARDSTM_TRIAGE.json, sep\PROD_SEPARATION.json, tools\opus_ep.py and .agents\skills\npt-data-holdout-check\scripts\audit_exports.py) | `tmp\opus_item1_verify.py` (the prescribed `python -c` one-liner needs a backslash path inside `-c`, which this job's rules forbid; the helper does the same): 7 cited paths ok, 3 four-field statuses labelled, "item 1 verify PASS"; `Test-Path` True for all 6 distinct cited paths; `grep -i "four.field.*PASS" sep\*.json sep\*.md` returns only PROD_SEPARATION.json line 7 "raw PASS (0 keys) is an en-passant artifact; EP-normalised FAIL (4,088 keys)" |
| 2 | 87ef93ee | `D:\a14\tools\opus_prod_separation.py` (17ffcc20834142754443853db772e752: `--out` refused if it or its `.part` exists, `.part` opened with mode 'x', flush + fsync, rename; `--replace-committed` only for a git-tracked output unchanged since HEAD; `--test-hold-seconds` test hook; the "PASS (not yet settled)" wording removed, BOARDSTM_TRIAGE.json mandatory) | scratch run 1: "written D:/a14/tmp/prodsep_verify01/PROD_SEPARATION.json d950bb9744cabe14a5fae81561e2d161"; run 2: "refusing: ... exists (pick a new --out ...)", exit 1, md5 still d950bb9744cabe14a5fae81561e2d161; mid-write test (`tmp\opus_killtest.py`: own child started with a 25 s hold after the `.part` was written, then terminated): ".part exists during hold: True / final exists: False", after the kill ".part exists: True / final exists: False", "RESULT PASS"; a rerun into that folder refuses because the `.part` exists |
| 3 | 179430b | `D:\a14\evidence\test_logs\r14\full-suite-r14cont02\output.log` (9288da127aa2e43b37a687838c872883), `command.txt` (daff245380bf6fe6357d4be983d6d61c), `command.ps1` (efffacc683cd949138a8f31d88f0dccd), `selected_files.txt`, `timing.txt`, `exit.txt`; counts in `R14_OPEN_ISSUES.md` (97913e353b975b300ddb692c0a8ce376) and in this report | first log line = 87ef93eeab1830f3c1c78c242af6b77d813323e3 = the tip the suite ran on (87ef93ee, the fix commit; the later commits add only logs, counts and this report); summary "5 failed, 331 passed, 67 subtests passed in 72.10s (0:01:12)"; known failures listed: F-003 / F-005 / F-006 (test failures), F-004 / F-008 / F-017 (findings, not tests: F-004 accepted, F-008 and F-017 fixed) |
| 4 | 87ef93ee | `NOTE_FAILURES.md` beside the four listed logs - `opus-envrestore-fix-green01` (c4038b5872315366ff439556ccd4e633, F-006), `preflight-green01` (751296bc68e60fef662a2c6ed3467a2a), `preflight-green02` (d6734a236bf8f0ab8397541ac454a894), `suite-runner-green01` (70e2338557d78de229479b7e9571b194, owner's pointer F-006 and the review's F-003) - and beside the six other committed "green" logs with failures that the verify condition covers: `qc\launcher-cap-green01` (891918cd783cf0d0fdb7b9cc748b501d), `qc\launcher-cap-green02` (b6618c21b59b426ad6ffa23ad4847a56), `qc\launcher-cap-green03` (07b6d726c2ac6e33efd2b90e54d75656), `qc\setup-green02` (86356657d26d29529c7c04f0699720d1), `qc\setup-pipe-green01` (7c1fdfc8ca3f2db9dcb5552025391b88), `qc\setup-pipe-green02` (b9772761415ee44fead3bc325c971bc4); all under `D:\a14\evidence\test_logs\r14\`; the logs themselves are unchanged and nothing was renamed (no deletes) | the four logs were found by md5 (65cc78a9..., 439c5f5c..., 3600cf60..., 5121aa92...); every committed `*green*` log with "N failed" > 0 now has a note beside it: 10 of 10 "noted", 0 "MISSING" |
| 5 | 87ef93ee | `D:\a14\PLAN.md` (d7c20b402a5619255ea457cc5d135e6f, lines 135-137), `D:\a14\evidence\review\r14cont_independent\REVIEW.md` (671fbf66b8d8935afee7df1f5a60b84f, dated correction lines 7-12 before "## Scope"; findings unchanged) | `grep -n -i independent` shows PLAN.md:136 and REVIEW.md:11 with the same wording "reviewer agent started by the owner's allowance, scope 7636122b..0883cee, not covering de1a1cd3 or the as-found tools" (grep of that exact string hits both files); REVIEW.md's original title and line 3 stay as the record, qualified by the correction |
| 6 | 87ef93ee | `D:\a14\sep\boardstm-probe01\TRIAGE_probe_only_tip.json` (495d50516a677db302396502fe0b09f5, rerun with the tip triage tool 63e82e3a820a5495c258fa25efcd2b8f; the old file kept); `D:\a14\sep\TOOL_MD5_CHAIN.md` (290295317497eb12062486549c8c01b2 at 87ef93ee; 038647fcf3ffe3763f3f31c6416ca444 after the fix-list-2 update in 78d83508) naming the build of every record | recorded tool md5 inside TRIAGE_probe_only_tip.json = certutil of `tools\opus_boardstm_triage.py` at the tip (63e82e3a820a5495c258fa25efcd2b8f); every count identical to the 09:51 record. NOT done: the PROOF.json rerun - it writes about 2 GB below --big-dir, C:\a14x is read-only for this job and D: had 52.6 GB free against the 50 GB floor; PROOF.json keeps the 3b43d18 build identity 37319c6e103b508d0fdcc23a17b035ad (tip 6c974b2e446182ba875a74a4a32fb334, docstring-only change, diff in the chain note) |
| 7 | 87ef93ee | `D:\a14\.agents\skills\guardband-split-proof\SKILL.md` (b7f7728af02b22e7b88e34d24fa8dfdb, stale line replaced); `D:\a14\tools\opus_promote_export.py` (0bc94d4267529aec152a8ad92927c7db, the refusal rules moved unchanged into `check_proof()`); `D:\a14\tests\test_opus_promote_export.py` (36ba9f2f79a5f5d1ec0505edec86c659) | `grep -n -i audit SKILL.md` lines 69-72 state the F-014 behaviour; `pytest tests\test_opus_promote_export.py`: "5 passed in 0.06s" (bad audit counters refused, missing counter field refused, non-PASS / problems refused, changed SPLIT refused, flag-less command refuses before reading anything). The CLI was NOT run with `--confirm-owner-decision` (binding rule); the counter refusal is proven at the function level on fixtures |
| 8 | 87ef93ee + 179430b | `D:\a14\evidence\R14_OPEN_ISSUES.md` (97913e353b975b300ddb692c0a8ce376): the three eaten spaces fixed, the accepted list (F-003, F-004, F-005 accepted with reasons; F-006 per the final run; F-008 and F-017 fixed), the export-scope note (999,921-row jobA set only; audit UNVERIFIED, game_id null in all 17,385,720 rows), the final suite counts | counts in R14_OPEN_ISSUES.md = the log summary "5 failed, 331 passed, 67 subtests passed in 72.10s (0:01:12)"; `grep -n "by100k\|has3982\|final30" evidence\R14_OPEN_ISSUES.md` prints exactly two lines, 37-38, which are the dated fix note quoting the three names ("Three eaten spaces fixed above ("has3982", "by100k" = review finding F-008, "final30-minute") ..."); the three original lines (8, 13, 25) no longer contain them |

The overlap (4,088 shared keys after EP normalisation) is still unresolved; nothing in this list changed that.

## Unfinished / UNVERIFIED
- Authentic game IDs for 001-039 do not exist and cannot be recovered here; every game-level verdict stays UNVERIFIED.
- The npt data stays blocked at the position level until the 7,700 listed train rows are removed and the data rebuilt
  (not done: no production-data change in this job).
- 104,569 UNKNOWN adjacent pairs in the production chain scan; the deeper jobA retry (`sep\RETRY_PLAN.md`,
  a8f908df1306da233f8edd0ae6fff4e1) is designed, not implemented.
- The guard-band export is not built; promotion is the owner's decision (one command, refuses without the flag).
- Astra's selected-suite runner (tools\r14_suite.py, Invoke-R14Suite.ps1, tests\test_r14_suite.py) stays UNVERIFIED
  (F-003, accepted); the two tests\r14_native failures (F-005) are open and pre-existing; F-006: see the final run above.
- The PROOF.json rerun with the tip tool (owner's item 6) was not done for lack of safe disk space; the build that
  produced it is named in `sep\TOOL_MD5_CHAIN.md`.
- The new `--no-index` bootstrap-wheel path of Setup-R14Runtime.ps1 was never executed on this PC; the pip
  `--require-hashes` proof covers the 13 pins, not that path.
- Not sealed inside the repository: this report's own md5 and the hash of the commit that adds it (hand-back message);
  a seal file added after the report would itself fall outside the appendix, so none was added.
- PC-only artifacts outside the repository: `C:\a14x\guardband01_stage`, `C:\a14x\guardband01_proof`,
  `C:\a14x\promote_tooltest01` and `D:\a14\sep\segments-production02\maps` are listed file by file in the appendix;
  `C:\a14x\inventory_test01.md` (68,026 bytes, md5 7a0d016e45797cef3c525dbec9034f92; a test run of opus_inventory.py at
  10:31) and `C:\a14x\r14_changed_files.txt` (48,216 bytes, md5 43a27e270df95ef3916ecf4c0e597e36; byte-identical to the
  committed `D:\a14\evidence\r14\r14_changed_files_11d38208_7636122b.txt`) are scratch copies, kept. Scratch helpers
  of this finish live in `D:\a14\tmp` (git-ignored): the report drafts and number sheets, opus_probe_shares.py,
  opus_tools_append.py / opus_tools_refresh.py, opus_cite_check.py, opus_assemble_report.py, opus_values_fill.py,
  opus_item1_verify.py, opus_killtest.py, opus_write_notes.py, opus_cpu01_check.ps1, opus_push.ps1, and the scratch
  outputs prodsep_verify01 / prodsep_verify02 (the `.part` left by the terminate test) / promote_test01.

## Tools
Own tools under `D:\a14\tools` (standard library + numpy; python-chess only as a test oracle): opus_lowrun.py,
opus_seal.py, opus_prod_separation.py, opus_ep.py, opus_boardstm_probe.py, opus_boardstm_triage.py, opus_guardband.py,
opus_guardband_proof.py, opus_guardband_record.py, opus_promote_export.py, opus_silent_sweep.py, opus_pypi_hashes.py,
opus_step0_verify.py, opus_tools_md.py, opus_inventory.py - full paths and md5s in the appendix; purpose and verify
command per tool in `D:\a14\TOOLS.md` (section "R14 finish helper tools", md5 89f181ae43a42bbe76422569f5d2d64b since
78d83508; e08fa2572c12fe9991464c119c507faf at 87ef93ee). Tests
of the own tools: tests\test_opus_ep.py, test_opus_boardstm_probe.py, test_opus_boardstm_triage.py,
test_opus_promote_export.py. Three skills for the next person: `D:\a14\.agents\skills\boardstm-overlap-triage\SKILL.md`
(9f93465b3bb1bbfaf4fa207930bb890b), `guardband-split-proof\SKILL.md` (b7f7728af02b22e7b88e34d24fa8dfdb),
`r14-finish-helpers\SKILL.md` (3edfb1a6d982a0c8b803dde9ab26c52f).

## Commits on the branch (git log 7636122b..HEAD, author Opus, times Vienna)
aa78a56 09:24 R14 results that existed only on the PC | c2e61fe 09:25 Astra's uncommitted tools and tests as found |
212697d 09:25 seal/verify and Idle-launcher tools | 64d3a7e 09:25 PROD_SEPARATION.json final scan counts, FAIL |
28c3260 09:37 r14_overlap full listing | e48cd20 09:44 EP normaliser + probe | b1cdfab 09:45 -text attributes |
06e6925 09:47 triage classifier | 5912299 09:53 probe + preliminary triage, guard-band split | 43516dd 09:59 QA note,
sidecar proposal | 17db812 10:01 sweep fixes | 9df2fe0 10:01 sweep evidence | 3b43d18 10:06 proof | 0883cee 10:24
GUARDBAND_SEPARATION.json | de1a1cd 11:01 review by the reviewer agent + fixes, suite logs, skills | b221b71 11:02 -text
for the skills and review folder | a9ef81e 11:14 full listing scan, cross-checked triage, PROD_SEPARATION settled |
f1df9ca 11:30 evidence gaps of the draft (Step 0 re-check, pip hash proof, test command) | 87ef93ee 13:45 owner's fix
list items 1-2 and 4-8 | e3957e1 14:04 final suite log at the tip 87ef93ee, receipts, counts (item 3) | 3daa18f 14:06
first version of this report | cdc487a 14:10 report with two verify cells corrected (reviewed tip of fix list 2) |
78d8350 16:11 owner's fix list 2 items 6-7 (relpath refusal, Import-Module before the mocks) | 179430b
17:52 suite rerun log full-suite-r14cont03 at the tip 78d8350, receipts, open-issues entry | then the
commit that adds this report (final head).

## Addendum - owner's fix list 2 of 2026-11-04 (items 6-7; items 1-5 belong to the 30-h job and were not touched)
Source: `C:\a14x\cr_fixlist2_20261104_from_owner.txt` (md5 f494be7a6adca9582c80b45853840702, read in full at 16:08).
Pre-edit `certutil -hashfile` md5s equalled the list's cdc487a8 blobs for both files (opus_prod_separation.py
17ffcc20834142754443853db772e752, test_r14_preflight.py abb6be63083824b00aa69d31a1116af9). Promotion not run.

| item | done in | changed files (new md5) | verify output |
|---|---|---|---|
| 6 | 78d83508c7291321330ab356f14d8e1a9f8602f5 (16:11:00) | `D:\a14\tools\opus_prod_separation.py` (7f0a3ae03e02a2b8ee551c3548aef782: `os.path.relpath(OUT, A14)` wrapped in try/except ValueError -> `need(False, f'refusing: {OUT} not under {A14}')`; the helper definitions moved above the argument block so `need` exists there); `D:\a14\TOOLS.md` (89f181ae43a42bbe76422569f5d2d64b, section refreshed, `--check` PASS 18/18); `D:\a14\sep\TOOL_MD5_CHAIN.md` (038647fcf3ffe3763f3f31c6416ca444, PROD_SEPARATION row names the new build) | `D:\a14\evidence\test_logs\r14\opus-prodsep-relpath01\output.log` (0875daed9ceff901fd078458ea9bcc30) + `command.txt` (23c39367611781287d3ccb04a3d1ee5c): `--out C:\a14x\prodsep_relpath_test\x.json --replace-committed` against an existing dummy (md5 d11d325009336b0f249138a1abea9fdf) -> exit 1, exactly one line "refusing to write PROD_SEPARATION.json: refusing: C:/a14x/prodsep_relpath_test/x.json not under D:/a14/", no traceback, dummy md5 unchanged, folder listing unchanged (no .part), "RESULT PASS". The C:\a14x path was used instead of the list's C:\Users\Administrator\scratch because C:\a14x is this job's allowed scratch and is still on another drive than D:\a14. A scratch run of the new build into D:\a14\tmp\prodsep_verify03 reproduces the committed record except updated_vienna, and a second run refuses. |
| 7 | 78d83508c7291321330ab356f14d8e1a9f8602f5 + 179430b | `D:\a14\tests\test_r14_preflight.py` (dfdf6235e5d88aed5f99bbfd2464cd51: `Import-Module Microsoft.PowerShell.Utility, Microsoft.PowerShell.Management` as the first line of the mock prefix, on the owner's order); suite rerun `D:\a14\evidence\test_logs\r14\full-suite-r14cont03\output.log` (0e607316e0b09f1b746bf56c6d894b30; first line = `git rev-parse HEAD` = 78d83508c7291321330ab356f14d8e1a9f8602f5), `command.txt` (d6b82f9ba2cf4ba480ce700139c568e5), `command.ps1`, `selected_files.txt`, `timing.txt`, `exit.txt`; `R14_OPEN_ISSUES.md` (97913e353b975b300ddb692c0a8ce376) | new log starts with the tip SHA 78d83508c7291321330ab356f14d8e1a9f8602f5; "8 failed, 328 passed, 67 subtests passed in 64.54s" (CPU 6 at Idle, 17:50:11-17:51:16); test_floor_breach_after_hash_writes_no_receipt PASSED, so the floor rule is proven again and no "does not prove the floor rule" label was needed. The eight failures: F-003 (1), F-005 (2), F-006 (1) as before, plus four tests/test_r14_launcher.py cases (test_child_environment_and_parent_preserved, test_owned_cap_after_child_never_allocates_receipt[during] and [after], test_exited_child_cannot_leave_descendant_holding_pipes) that failed on the launcher CPU-admission guard ("CPU admission refused", Invoke-R13.ps1 line 55: PercentProcessorTime > 70 on the CPU the child picks, which is the CPU the suite itself occupies) - they passed on CPU 1 (13:54) and CPU 2 (10:37) and are the same cases as in Astra qc/launcher-cap-green0* logs; environmental, not caused by items 6-7. The record also names the health probe evidence/r14/health-ps51-f3a987e49960.json written by the run. |

The 4,088-key residual overlap is unchanged by this list; npt data stays BLOCKED.

## Appendix - every file by full PC path and md5
Generated by `D:\a14\tools\opus_inventory.py` at 17:52 (after the last content commit 179430bd), after the last content commit 179430b:
`--base 7636122b71ff27a5b4b781b6775757f926f8fdc4 --extra C:\a14x\guardband01_stage --extra
D:\a14\sep\segments-production02\maps --extra C:\a14x\guardband01_proof --extra C:\a14x\promote_tooltest01 --exclude
D:\a14\FINAL_REPORT.md`: 712 entries, 2,463,112,592 bytes. Every file of `git diff --name-only 7636122b HEAD`
plus every file below the four extra folders, sorted by path; FINAL_REPORT.md is excluded because it cannot list itself.
The 92 entries marked "deleted on the branch" are pytest's `...current` pointer entries of the as-found
boundary and launcher logs (git mode 120000 symlinks), which are not regular files on disk.

| file (full PC path) | bytes | md5 |
|---|---|---|
| C:\a14x\guardband01_proof\audit\audit.json | 3021 | 1556e010d237d3e7b9f952bb50a8a305 |
| C:\a14x\guardband01_proof\audit\audit.sqlite | 295190528 | 2838f85f5863b6a5c877e02be668ce0c |
| C:\a14x\guardband01_proof\audit_stderr.txt | 0 | d41d8cd98f00b204e9800998ecf8427e |
| C:\a14x\guardband01_proof\audit_stdout.json | 2935 | e5fcf267c2211f6d50726d40c3a2dae8 |
| C:\a14x\guardband01_proof\forge_selfplay_013.jsonl | 1007875773 | 2bc1650b4977738fdbcfc429ee7ef124 |
| C:\a14x\guardband01_proof\forge_selfplay_014.jsonl | 643606965 | cf344aa9ab7234b8924c9f41511fda5c |
| C:\a14x\guardband01_proof\source.jsonl | 98882804 | fdfb3ad584260d5b2aeec330944ef871 |
| C:\a14x\guardband01_proof\train.jsonl | 98644525 | 1dc65dc50be8b3f18177233046bd7e39 |
| C:\a14x\guardband01_stage\train.rowids | 6799612 | c3171e3882f31cfb1ffd0103548c06bb |
| C:\a14x\guardband01_stage\train.txt | 63524376 | 2ab776b02dc100c52d4a741bcd3c6fa0 |
| C:\a14x\guardband01_stage\val.rowids | 69657 | 3edab5f17bfc86406f5aecd11e64e622 |
| C:\a14x\guardband01_stage\val.txt | 646288 | 2b02b68e7f558ea226885ae0c8135c1b |
| C:\a14x\promote_tooltest01\MANIFEST.json | 2713 | f4c9028d98101947011be2a560672eec |
| C:\a14x\promote_tooltest01\README_TOOL_TEST_NOT_AN_EXPORT.txt | 403 | 81e5bb10ab39f9340abd5f3ca37384a0 |
| C:\a14x\promote_tooltest01\train.rowids | 6799612 | c3171e3882f31cfb1ffd0103548c06bb |
| C:\a14x\promote_tooltest01\train.txt | 63524376 | 2ab776b02dc100c52d4a741bcd3c6fa0 |
| C:\a14x\promote_tooltest01\val.rowids | 69657 | 3edab5f17bfc86406f5aecd11e64e622 |
| C:\a14x\promote_tooltest01\val.txt | 646288 | 2b02b68e7f558ea226885ae0c8135c1b |
| D:\a14\.agents\skills\boardstm-overlap-triage\SKILL.md | 6310 | 9f93465b3bb1bbfaf4fa207930bb890b |
| D:\a14\.agents\skills\guardband-split-proof\SKILL.md | 6278 | b7f7728af02b22e7b88e34d24fa8dfdb |
| D:\a14\.agents\skills\r14-finish-helpers\SKILL.md | 5558 | 3edfb1a6d982a0c8b803dde9ab26c52f |
| D:\a14\.gitattributes | 778 | a663b37163cb438c92c954b3f9dca2ce |
| D:\a14\.gitignore | 517 | c5346f0fdc05a0a1fc3c48af3f125a29 |
| D:\a14\evidence\r14\health-ps51-17e1a25f927a.json | 5589 | fb87d4e31c626e689095f11f5a288ac6 |
| D:\a14\evidence\r14\health-ps51-1fc845190287.json | 6656 | 416c3a758701b2421754cb04ce967404 |
| D:\a14\evidence\r14\health-ps51-d0602b990d33.json | 5590 | 5327bbeb13066091fc226eb670bbbd73 |
| D:\a14\evidence\r14\health-ps51-d748073904c2.json | 7874 | 9f47023c6989a1ac9f3664440c9813e9 |
| D:\a14\evidence\r14\health-ps51-f3a987e49960.json | 7889 | d789947e3e78267b25616b748e1a9527 |
| D:\a14\evidence\r14\opus_silent_sweep_after.json | 7853 | 46d756edee6119af37ee812194edf7b9 |
| D:\a14\evidence\r14\opus_silent_sweep_r14_range.json | 35 | 2620cfee40919426d0cd57828dc5a4f0 |
| D:\a14\evidence\r14\opus_telemetry.md | 1171 | b15163ab1bc4c113f80f78dd168182f6 |
| D:\a14\evidence\r14\overlap-production03.log | 74104 | e2b0dbc61e5e056ac51782622f838491 |
| D:\a14\evidence\r14\overlap-production04.log | 142396 | 25d30542f80e35cf224af78c96eb2334 |
| D:\a14\evidence\r14\r14_changed_files_11d38208_7636122b.txt | 48216 | 43a27e270df95ef3916ecf4c0e597e36 |
| D:\a14\evidence\r14\segments-production02.log | 60656 | 4c90a81861d2cfb9fc973008b618594a |
| D:\a14\evidence\R14_OPEN_ISSUES.md | 8812 | 97913e353b975b300ddb692c0a8ce376 |
| D:\a14\evidence\review\r14cont_independent\bytes_check.out | 7664 | bcf2b7be8908d89241b2d9717097545f |
| D:\a14\evidence\review\r14cont_independent\diffs\modified_files.diff | 54801 | c481b9b47570261d532c7981f2707f21 |
| D:\a14\evidence\review\r14cont_independent\env_restore_probe.out | 266 | 4c83f278da7cfe49f383bff4b6def08b |
| D:\a14\evidence\review\r14cont_independent\help_opus_boardstm_probe.txt | 1816 | 042fa881c790f9f3c90518cd3cd5e0f5 |
| D:\a14\evidence\review\r14cont_independent\help_opus_boardstm_triage.txt | 2011 | 090991273eef6bdfe3e3973e9bcc3fac |
| D:\a14\evidence\review\r14cont_independent\help_opus_ep.txt | 1546 | 422e4c09458ff3f22f60229c966f67d8 |
| D:\a14\evidence\review\r14cont_independent\help_opus_guardband.txt | 2017 | b8fcc9fdbaf802a56bdd9fc7f55099c7 |
| D:\a14\evidence\review\r14cont_independent\help_opus_guardband_proof.txt | 2058 | fac1dd208058cb8bface305b57d2736f |
| D:\a14\evidence\review\r14cont_independent\help_opus_lowrun.txt | 183 | c43b7836d37c63075e39cec4723b8201 |
| D:\a14\evidence\review\r14cont_independent\help_opus_promote_export.txt | 1355 | 5418d0192d36ac9e7d47ee3d429e25a7 |
| D:\a14\evidence\review\r14cont_independent\help_opus_pypi_hashes.txt | 1014 | 8128a3aa73724c663028b2cc69075820 |
| D:\a14\evidence\review\r14cont_independent\help_opus_seal.txt | 1182 | b17c29f05bc1ef79f728751b3d26614b |
| D:\a14\evidence\review\r14cont_independent\help_opus_silent_sweep.txt | 902 | 62bc9ff21608f5627731324aeae7b9d1 |
| D:\a14\evidence\review\r14cont_independent\maps_seal_verify.out | 40 | 7f885c413fa1b268eeb21d9b371fa3e1 |
| D:\a14\evidence\review\r14cont_independent\proof_verify_report.out | 374 | 670dacead29b3a2fbaf0c5d2fd6a2bb1 |
| D:\a14\evidence\review\r14cont_independent\REVIEW.md | 35898 | 671fbf66b8d8935afee7df1f5a60b84f |
| D:\a14\evidence\review\r14cont_independent\scripts\bytes_check.py | 3063 | 1a6998818a10ed64fff2bb5085721aa9 |
| D:\a14\evidence\review\r14cont_independent\scripts\env_restore_probe.ps1 | 1183 | 27a31ba67e4b38994556446cd27885a5 |
| D:\a14\evidence\review\r14cont_independent\scripts\lowrun_child_probe.py | 189 | de551eac536190ac6cd1843f5277d71f |
| D:\a14\evidence\test_logs\r14\boundary\green01-admission-refused.txt | 363 | ec5f545bbb48e474f8008ae254cac96e |
| D:\a14\evidence\test_logs\r14\boundary\green02.log | 101 | d8bb79b04951c0a6657881fc7f63d919 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_binary_query_receipts_are0\parts\queries_0001.bin | 30 | e75402226e20f32e107ada6cee0cfa33 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_binary_query_receipts_are0\parts\queries_0002.bin | 15 | 0573c0f05ba76c45ac8578f3c3eae0ab |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_binary_query_receipts_arecurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_empty_window_has_no_full_0\source.txt | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_empty_window_has_no_full_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_endpoint_fill_does_not_cl0\source.txt | 83 | ed01f5cc25a43a8939f2a0e3da132817 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_endpoint_fill_does_not_clcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_filter_qualification_gate0\core.txt | 26 | 9fc261179189b518106c0cf885a648ad |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_filter_qualification_gate1\core.txt | 26 | 9fc261179189b518106c0cf885a648ad |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_filter_qualification_gate2\core.txt | 26 | 9fc261179189b518106c0cf885a648ad |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_filter_qualification_gate3\core.txt | 27 | ac5e5275b1942fa71a124247715a8f5b |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_filter_qualification_gatecurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_receipt_seal_can_resume_a0\parts\queries_0001.bin | 15 | 0573c0f05ba76c45ac8578f3c3eae0ab |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_receipt_seal_can_resume_acurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_window_reader_hashes_all_0\source.txt | 334 | a20eac6d85b0378f327f83906e2eb973 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_window_reader_hashes_all_1\source.txt | 334 | a20eac6d85b0378f327f83906e2eb973 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_window_reader_hashes_all_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_window_reader_pin_mismatc0\source.txt | 67 | 25eaabb318cab0429d6f67670f925bd2 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_window_reader_pin_mismatccurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_window_reader_preserves_i0\source.txt | 5142 | 129dbecd111af537112e04bffc7bb26f |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_window_reader_preserves_icurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_writer_hard_stop_abort_do0\parts\queries_0001.bin.part | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\boundary\pytest_green02\test_writer_hard_stop_abort_docurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_binary_query_receipts_are0\parts\queries_0001.bin | 30 | e75402226e20f32e107ada6cee0cfa33 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_binary_query_receipts_are0\parts\queries_0002.bin | 15 | 0573c0f05ba76c45ac8578f3c3eae0ab |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_binary_query_receipts_arecurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_empty_window_has_no_full_0\source.txt | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_empty_window_has_no_full_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_filter_qualification_gate0\core.txt | 26 | 9fc261179189b518106c0cf885a648ad |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_filter_qualification_gate1\core.txt | 26 | 9fc261179189b518106c0cf885a648ad |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_filter_qualification_gate2\core.txt | 26 | 9fc261179189b518106c0cf885a648ad |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_filter_qualification_gate3\core.txt | 27 | ac5e5275b1942fa71a124247715a8f5b |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_filter_qualification_gatecurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_receipt_seal_can_resume_a0\parts\queries_0001.bin.part | 15 | 0573c0f05ba76c45ac8578f3c3eae0ab |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_receipt_seal_can_resume_acurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_window_reader_hashes_all_0\source.txt | 334 | a20eac6d85b0378f327f83906e2eb973 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_window_reader_hashes_all_1\source.txt | 334 | a20eac6d85b0378f327f83906e2eb973 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_window_reader_hashes_all_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_window_reader_pin_mismatc0\source.txt | 67 | 25eaabb318cab0429d6f67670f925bd2 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_window_reader_pin_mismatccurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_window_reader_preserves_i0\source.txt | 5142 | 129dbecd111af537112e04bffc7bb26f |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_window_reader_preserves_icurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_writer_hard_stop_abort_do0\parts\queries_0001.bin.part | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red02\test_writer_hard_stop_abort_docurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red03\test_endpoint_fill_does_not_cl0\source.txt | 83 | ed01f5cc25a43a8939f2a0e3da132817 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red03\test_endpoint_fill_does_not_clcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red04\test_failed_close_with_closed_0\parts\queries_0001.bin | 15 | 0573c0f05ba76c45ac8578f3c3eae0ab |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red04\test_failed_close_with_closed_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red04\test_late_native_close_failure0\output\progress.jsonl | 428 | f0047892bb4de5cd09b3267efeb17925 |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red04\test_late_native_close_failure0\output\seam_012_013\parts\queries_0001.bin | 15 | 93bffbee31290a7dcf16cf89e28c46ae |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red04\test_late_native_close_failure0\synthetic-dependency.json | 2 | 99914b932bd37a50b983c5e7c90ae93b |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red04\test_late_native_close_failure0\synthetic-native.identity | 38 | ef3508ae617ffbe5775649ea50b8f1ef |
| D:\a14\evidence\test_logs\r14\boundary\pytest_red04\test_late_native_close_failurecurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\boundary\red01.log | 20410 | 78d60a25d0f099edfc48f7f0bbdcce4e |
| D:\a14\evidence\test_logs\r14\boundary\red02.log | 2811 | 20787d18fb0b1a483724a6af654b254b |
| D:\a14\evidence\test_logs\r14\boundary\red03.log | 2789 | 025fac6d989fa1b0dd19bc477e0c58b0 |
| D:\a14\evidence\test_logs\r14\boundary\red04.log | 9127 | f3e134bce23997eeefbfe692b0d23924 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\command.ps1 | 1339 | feab36cf1ac63ecf2970112de99d4b81 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\exit.txt | 8 | 46b5b2d52210b9d99d1bd66222e8612c |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\output.log | 6987 | 5e29b6281dc5a8b18eb305d93a44ccb2 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\native.log | 2668 | 22a07b65ec80226db6d226868b2f3877 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\runtime_setup.log | 3067 | a9f681f3352a1ebcbc41054d2a294a94 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\timing.txt | 89 | 012590b81a744acb236e592e3e595320 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_direct_exit_cannot_leave_0\child.json | 341 | 94111e648bbafb8702e6a05c093dd5df |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_direct_exit_cannot_leave_0\harness.ps1 | 1705 | 8892b725c1b62041f6335fceb0d25eca |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_direct_exit_cannot_leave_0\parent.json | 588 | bceed6fbd9d4d943b1a2cec1bca3bc06 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_direct_exit_cannot_leave_0\probe.py | 724 | 9a63f69a664395837a6644a839b0619a |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_direct_exit_cannot_leave_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_fixture_options_cannot_ac0\harness.ps1 | 1697 | bb5faa1fd9f1f8f55c238d697a42d0fa |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_fixture_options_cannot_ac0\parent.json | 627 | 241a82c1607aa54fd0f32cb96946152e |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_fixture_options_cannot_ac0\probe.py | 583 | d50613f9dfce554d0497d223cebe8c87 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_fixture_options_cannot_accurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_live_refusal_stops_only_o0\harness.ps1 | 1706 | 20e95d654076d55a2561ffe0ff585f37 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_live_refusal_stops_only_o0\parent.json | 610 | 499102d47ac9dd8728820be18c9d5cfb |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_live_refusal_stops_only_o0\probe.py | 726 | 8a86bfa9b2894a0e04f4a6054167a903 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_live_refusal_stops_only_o1\child.json | 342 | 172fc8f87785b817c46ef84b0f08047d |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_live_refusal_stops_only_o1\harness.ps1 | 1705 | 5e904999c03d50fee2eb1bcb870bc792 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_live_refusal_stops_only_o1\parent.json | 605 | abb681b2475313a74fbe0b3c84af9084 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_live_refusal_stops_only_o1\probe.py | 726 | d977d8e806ebbefa99069cf75e454c8f |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_live_refusal_stops_only_ocurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_resource_boundaries_and_a0\boundaries.json | 159 | fcc01ce509e8fd1f3ce73968d879ab3f |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_resource_boundaries_and_a0\probe.py | 6 | 5527939aca3e9e80d5ab3bee47391f0f |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_resource_boundaries_and_a0\resource-boundaries.ps1 | 1279 | 06c82f41d8e0683136680b08ae68f5aa |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_resource_boundaries_and_acurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_setup_preserves_caller_en0\child.json | 320 | 9a38c52be14fe19676622caede218f9f |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_setup_preserves_caller_en0\harness.ps1 | 1706 | caaa8df420b603e9c65d6f7dd5673dba |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_setup_preserves_caller_en0\parent.json | 588 | 40b7874ee3e7f9bd973c394dcb2d28cf |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_setup_preserves_caller_en0\probe.py | 583 | 3a50988000d9ce4cea92ef3f7d6f0729 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_setup_preserves_caller_en1\child.json | 320 | 203d7a84c4edf454e1847929d499f383 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_setup_preserves_caller_en1\harness.ps1 | 1706 | 00c2ca9c2626df0a2f85474e35c8487d |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_setup_preserves_caller_en1\parent.json | 679 | e170dc60e4e897a188e93f66f6659a09 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_setup_preserves_caller_en1\probe.py | 583 | 9add5197db9182a32a676538a124312a |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_setup_preserves_caller_encurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_unset_caller_environment_0\child.json | 319 | 9949c36ee8d051593e609e6d7c06c62c |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_unset_caller_environment_0\harness.ps1 | 1998 | 341f80ddf1a9a2b9a8b806daa9164df8 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_unset_caller_environment_0\parent.json | 350 | 4c8b971b7ba5ba29c2e922f661a8ba19 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_unset_caller_environment_0\probe.py | 583 | 77b5d2a959f687410771332e59f57961 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\rerun-single-files\tmp_runtime_setup\test_unset_caller_environment_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\run2-continue-on-collection-errors\command.ps1 | 1444 | 16f06c3767e0c50f5fa2f2783f4c0ab3 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\run2-continue-on-collection-errors\output.log | 669714 | cea1c863645375f42c9059fd981498f8 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\run2-continue-on-collection-errors\timing.txt | 74 | 39dc045fc814b27edd8ecd03d7eb8a60 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\run3-r14-scope\command.ps1 | 1776 | 47bfc1e4866d682eb1ee866a891091e6 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\run3-r14-scope\output.log | 13743 | 371de062db01a986b7c7e30b8b0db081 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\run3-r14-scope\selected_files.txt | 939 | 261c954b128ecda36ffbe86aaba4ae60 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\run3-r14-scope\timing.txt | 74 | 1889e5a6d8d41faeef62fbec36048edd |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont01\timing.txt | 73 | d95499d8b610bec9ea6f9bf1b7b7b21b |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont02\command.ps1 | 2532 | efffacc683cd949138a8f31d88f0dccd |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont02\command.txt | 1673 | daff245380bf6fe6357d4be983d6d61c |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont02\exit.txt | 8 | e5bc9ae3753e7edd5bc9b3ff42a6b9b7 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont02\output.log | 9447 | 9288da127aa2e43b37a687838c872883 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont02\selected_files.txt | 980 | 603a78b6be6a6a93ac5dc2076b5e6622 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont02\timing.txt | 74 | 2d62a5fc2a3973b5f69c3745f3975df5 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont02\TRIAGE.md | 4502 | 66fcb4303dc7f4eb6189a3d8cd5f464e |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont03\command.ps1 | 2565 | 9582fd39ef1c6c7fc89ac58dbea9a691 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont03\command.txt | 1675 | d6b82f9ba2cf4ba480ce700139c568e5 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont03\exit.txt | 8 | e5bc9ae3753e7edd5bc9b3ff42a6b9b7 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont03\output.log | 19537 | 0e607316e0b09f1b746bf56c6d894b30 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont03\selected_files.txt | 980 | 603a78b6be6a6a93ac5dc2076b5e6622 |
| D:\a14\evidence\test_logs\r14\full-suite-r14cont03\timing.txt | 74 | a975762e8e1afedf275f02ddb139302f |
| D:\a14\evidence\test_logs\r14\identity-ambiguity-command.ps1 | 1544 | 69673554529d0e3364c3f797169fe829 |
| D:\a14\evidence\test_logs\r14\IDENTITY_AMBIGUITY_MILESTONE.md | 3652 | 0cec85aad81cd4d04cfabe8c2e196749 |
| D:\a14\evidence\test_logs\r14\launcher-review-green01\output.log | 100 | 70af4de5f9373fa209f20b5906cff136 |
| D:\a14\evidence\test_logs\r14\launcher-review-red01\output.log | 5291 | 51a9a527b889330328fdb3d0c5fc6300 |
| D:\a14\evidence\test_logs\r14\launchers\cap-134a801474a3\child-command.json | 270 | 4b350b95761888982eb10dba54df43c1 |
| D:\a14\evidence\test_logs\r14\launchers\cap-134a801474a3\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-134a801474a3\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-3cd25fc33e06\child-command.json | 270 | 805a7f24b85f465a3435c99fd6a0568f |
| D:\a14\evidence\test_logs\r14\launchers\cap-3cd25fc33e06\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-3cd25fc33e06\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-548e3ddf0788\child-command.json | 299 | 85977077186d81656698ef824557233c |
| D:\a14\evidence\test_logs\r14\launchers\cap-548e3ddf0788\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-548e3ddf0788\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-775a1c98f349\child-command.json | 263 | 4947166c4a0fe79e95a3f21186b1ea72 |
| D:\a14\evidence\test_logs\r14\launchers\cap-775a1c98f349\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-775a1c98f349\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-83ac47533c0e\child-command.json | 279 | ef5d57e8f397517cc4162e3b16a2029e |
| D:\a14\evidence\test_logs\r14\launchers\cap-83ac47533c0e\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-83ac47533c0e\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-895f3c0de304\child-command.json | 299 | 68cb73c464d6fc19cc672e58e4cf8508 |
| D:\a14\evidence\test_logs\r14\launchers\cap-895f3c0de304\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-895f3c0de304\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-9a467c4e7e1e\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-9a467c4e7e1e\receipt.json | 25935 | 5dd5096c87cf9385d4f6c945fcbcecf8 |
| D:\a14\evidence\test_logs\r14\launchers\cap-9a467c4e7e1e\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-b16ed1ce2945\child-command.json | 279 | a8c129599bf28e13688750204800ae29 |
| D:\a14\evidence\test_logs\r14\launchers\cap-b16ed1ce2945\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-b16ed1ce2945\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-b2c735fb724a\child-command.json | 270 | c5229ebb394c2b8a53ad26da1ffeb09c |
| D:\a14\evidence\test_logs\r14\launchers\cap-b2c735fb724a\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-b2c735fb724a\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-ba950348034a\child-command.json | 270 | 7dca157d513207936390a750aaa79f33 |
| D:\a14\evidence\test_logs\r14\launchers\cap-ba950348034a\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-ba950348034a\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-bf0744e3d3ba\child-command.json | 263 | c0da38ce7283cb42216de47f6e0caa9f |
| D:\a14\evidence\test_logs\r14\launchers\cap-bf0744e3d3ba\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\cap-bf0744e3d3ba\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-09381178f188\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-09381178f188\receipt.json | 50915 | 4344189a46ff6907cf26081e79da8898 |
| D:\a14\evidence\test_logs\r14\launchers\launcher-09381178f188\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-2b23a4050998\child-command.json | 337 | 420e80afd09d3d0495f87be842285eff |
| D:\a14\evidence\test_logs\r14\launchers\launcher-2b23a4050998\output.log | 15 | b1a2d6941d2457770940d5e1b85def4a |
| D:\a14\evidence\test_logs\r14\launchers\launcher-2b23a4050998\receipt.json | 61673 | 1bb91890f7ddfbf5e35e724d8add3ffd |
| D:\a14\evidence\test_logs\r14\launchers\launcher-2b23a4050998\stderr.log | 15 | 31a783cbeda0852894e3ff5e5282b088 |
| D:\a14\evidence\test_logs\r14\launchers\launcher-64c24c48f53b\child-command.json | 373 | 34fd83f8fa9ef5736719df3b02501579 |
| D:\a14\evidence\test_logs\r14\launchers\launcher-64c24c48f53b\output.log | 15 | b1a2d6941d2457770940d5e1b85def4a |
| D:\a14\evidence\test_logs\r14\launchers\launcher-64c24c48f53b\receipt.json | 61283 | 299251a6f82087f13dad8dcc8343f4b3 |
| D:\a14\evidence\test_logs\r14\launchers\launcher-64c24c48f53b\stderr.log | 15 | 31a783cbeda0852894e3ff5e5282b088 |
| D:\a14\evidence\test_logs\r14\launchers\launcher-81c1ea991027\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-81c1ea991027\receipt.json | 50447 | 2ed7e61918fe9ad54828bafd2a00fe6f |
| D:\a14\evidence\test_logs\r14\launchers\launcher-81c1ea991027\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-98c660b45286\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-98c660b45286\receipt.json | 51303 | e361299f3c9b414300807aee2d2e2e9f |
| D:\a14\evidence\test_logs\r14\launchers\launcher-98c660b45286\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-b6925f1af4f1\child-command.json | 353 | 3cdcd0b33625f8d23facf00b2e1dfb4b |
| D:\a14\evidence\test_logs\r14\launchers\launcher-b6925f1af4f1\output.log | 15 | b1a2d6941d2457770940d5e1b85def4a |
| D:\a14\evidence\test_logs\r14\launchers\launcher-b6925f1af4f1\receipt.json | 61263 | 70feaaf8b4b4958ebc28adbaa8ebc3f4 |
| D:\a14\evidence\test_logs\r14\launchers\launcher-b6925f1af4f1\stderr.log | 15 | 31a783cbeda0852894e3ff5e5282b088 |
| D:\a14\evidence\test_logs\r14\launchers\launcher-ca2b8a0a121e\child-command.json | 344 | 1b963fce33c73a15890c9296c1595dd9 |
| D:\a14\evidence\test_logs\r14\launchers\launcher-ca2b8a0a121e\output.log | 15 | b1a2d6941d2457770940d5e1b85def4a |
| D:\a14\evidence\test_logs\r14\launchers\launcher-ca2b8a0a121e\receipt.json | 52176 | d458b1ae3711203fff36113951f96a04 |
| D:\a14\evidence\test_logs\r14\launchers\launcher-ca2b8a0a121e\stderr.log | 15 | 31a783cbeda0852894e3ff5e5282b088 |
| D:\a14\evidence\test_logs\r14\launchers\launcher-fc221f956777\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-fc221f956777\receipt.json | 50445 | b645d1cb5cedbb132aabfd14e06330ec |
| D:\a14\evidence\test_logs\r14\launchers\launcher-fc221f956777\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-fd2928db248d\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-fd2928db248d\receipt.json | 51113 | c9fe5c39634ae768c4a3e4b09135e888 |
| D:\a14\evidence\test_logs\r14\launchers\launcher-fd2928db248d\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-test_child_environment_and_par0\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\launcher-test_child_environment_and_par0\receipt.json | 50225 | acc24d14b37c13dadda6522444bcb94a |
| D:\a14\evidence\test_logs\r14\launchers\launcher-test_child_environment_and_par0\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\pipes-4f8602e4dc36\child-command.json | 304 | 356f68182c210fcc92c8497b7abb5e21 |
| D:\a14\evidence\test_logs\r14\launchers\pipes-4f8602e4dc36\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\pipes-4f8602e4dc36\receipt.json | 61211 | 27431404ffb08b4eaab1294974e00a0b |
| D:\a14\evidence\test_logs\r14\launchers\pipes-4f8602e4dc36\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\pipes-58051cc7fd79\child-command.json | 284 | 372278777e560745ba578b9db25d80c1 |
| D:\a14\evidence\test_logs\r14\launchers\pipes-58051cc7fd79\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\pipes-58051cc7fd79\receipt.json | 61191 | 12b6915dec02811c30494e9a7df33c65 |
| D:\a14\evidence\test_logs\r14\launchers\pipes-58051cc7fd79\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\pipes-85e0f15a1601\child-command.json | 275 | d93a2834d4c9b8fbb40409ffe65712cd |
| D:\a14\evidence\test_logs\r14\launchers\pipes-85e0f15a1601\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\pipes-85e0f15a1601\receipt.json | 52104 | 75db49c91bc113a2f878059c0c8b2324 |
| D:\a14\evidence\test_logs\r14\launchers\pipes-85e0f15a1601\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\pipes-c8fb63676302\child-command.json | 268 | 74aa266926cc42689e15f82cd2346155 |
| D:\a14\evidence\test_logs\r14\launchers\pipes-c8fb63676302\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\pipes-c8fb63676302\receipt.json | 61601 | 47aeafd1919fc415199240bb85308ba1 |
| D:\a14\evidence\test_logs\r14\launchers\pipes-c8fb63676302\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\pipes-d8f760a26d54\child-command.json | 275 | 8d5612f1e89ac9684af696373f489deb |
| D:\a14\evidence\test_logs\r14\launchers\pipes-d8f760a26d54\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\pipes-d8f760a26d54\receipt.json | 52104 | 92dba800d9d1230fea6c16fa3c26d74b |
| D:\a14\evidence\test_logs\r14\launchers\pipes-d8f760a26d54\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\storage-test\output.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\launchers\storage-test\receipt.json | 785 | 4b56c7e9f83dbded97d63099237b8aba |
| D:\a14\evidence\test_logs\r14\launchers\storage-test\stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\opus-envrestore-fix-green01\NOTE_FAILURES.md | 1080 | c4038b5872315366ff439556ccd4e633 |
| D:\a14\evidence\test_logs\r14\opus-envrestore-fix-green01\output.log | 1880 | 65cc78a98dc11d88d53bbd262ba9a0f7 |
| D:\a14\evidence\test_logs\r14\opus-ep-green01\output.log | 101 | 61f109fa02845b5187b20ed484eee9ac |
| D:\a14\evidence\test_logs\r14\opus-overlap-listing-green01\output.log | 101 | f63916044439bf77b60eccbde535b0b4 |
| D:\a14\evidence\test_logs\r14\opus-pip-require-hashes01\command.txt | 664 | f125861d5d1f77c17cdcdbf05b2d6635 |
| D:\a14\evidence\test_logs\r14\opus-pip-require-hashes01\output.log | 3328 | 45bd3448f7bc2cfcb1a462a0746e4bc9 |
| D:\a14\evidence\test_logs\r14\opus-probe-green01\output.log | 101 | e18ee4e6068e06f03667afa0482dc71c |
| D:\a14\evidence\test_logs\r14\opus-prodsep-relpath01\command.txt | 378 | 23c39367611781287d3ccb04a3d1ee5c |
| D:\a14\evidence\test_logs\r14\opus-prodsep-relpath01\output.log | 614 | 0875daed9ceff901fd078458ea9bcc30 |
| D:\a14\evidence\test_logs\r14\opus-qualify-fixture-green01\output.log | 101 | 870686becf8c3627a443f5bc843e3de7 |
| D:\a14\evidence\test_logs\r14\opus-review-fixes-green01\command.txt | 467 | 2fbefeb7ba6b72ccd39d95b192e694a8 |
| D:\a14\evidence\test_logs\r14\opus-review-fixes-green01\output.log | 101 | 71240553f423c00a3c284d95e0db05e3 |
| D:\a14\evidence\test_logs\r14\opus-silent-sweep-green01\output.log | 101 | 3ce676be4b84584c3c32e6b5864bff8a |
| D:\a14\evidence\test_logs\r14\opus-step0-recheck01\maps_verify_report.log | 4457 | 89de0eef0029342bc6a8b553bed9e867 |
| D:\a14\evidence\test_logs\r14\opus-step0-recheck01\output.log | 909 | 9fb54b953117ac8c9f7566b39179e28f |
| D:\a14\evidence\test_logs\r14\opus-triage-green01\output.log | 100 | d51fbe34aca170b98443be30b7271584 |
| D:\a14\evidence\test_logs\r14\overlap-publication-command.ps1 | 1130 | e13f065d06ee1c398480bb0162ad4c1a |
| D:\a14\evidence\test_logs\r14\overlap-review-green02\output.log | 101 | 19559d1729d06f473e84355a8ab848de |
| D:\a14\evidence\test_logs\r14\overlap-review-red02\output.log | 2419 | 37dd35f797b7605df629b6a16328b989 |
| D:\a14\evidence\test_logs\r14\preflight-green01\NOTE_FAILURES.md | 864 | 751296bc68e60fef662a2c6ed3467a2a |
| D:\a14\evidence\test_logs\r14\preflight-green01\output.log | 1716 | 439c5f5c8300af7628e4bcf00dd16d7a |
| D:\a14\evidence\test_logs\r14\preflight-green02\NOTE_FAILURES.md | 873 | d6734a236bf8f0ab8397541ac454a894 |
| D:\a14\evidence\test_logs\r14\preflight-green02\output.log | 2882 | 3600cf603222f5ed96c562951065d1f0 |
| D:\a14\evidence\test_logs\r14\preflight-red01\output.log | 6974 | e11776327f19f4376aef34a2fce65078 |
| D:\a14\evidence\test_logs\r14\qc-empty-runs-command.ps1 | 1220 | 309a1b631112bb7385d0e9f9b326e1ee |
| D:\a14\evidence\test_logs\r14\qc-empty-runs-green01\output.log | 109 | f95e10bd2c488e0d2d6baadc9cae4928 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\command.json | 354 | 3822a380fab8c662083584277c0de0a0 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\exit.json | 76 | 1cbe7c84b35c2918baa23c8329093953 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\NOTE_FAILURES.md | 916 | 891918cd783cf0d0fdb7b9cc748b501d |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\output.log | 6852 | a735e9bf0157ec8e037e137fd441fd4d |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_child_environment_and_par0\child.json | 310 | ebd831d211841ab0f19ae5d947fe86de |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_child_environment_and_par0\harness.ps1 | 1046 | 467b1d21cde5216f209bba21748fca42 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_child_environment_and_par0\parent.json | 251 | ee91ccf519797f72fb6b595b12876c3f |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_child_environment_and_par0\probe.py | 373 | 430bf07debf01e5840b7b7fca73ed1af |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_child_environment_and_parcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_owned_cap_after_child_nev0\post-cap.ps1 | 1498 | 092fe7a28277949bcc78145313578196 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_owned_cap_after_child_nev0\probe.py | 188 | 637fdf213d3e32c6c8bef82e718e41bd |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_owned_cap_after_child_nev1\post-cap.ps1 | 1498 | bdfae035536eb4034ddb031f4eceec8d |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_owned_cap_after_child_nev1\probe.py | 172 | 768404adf6548a719a3f9f2c822b16b2 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_owned_cap_after_child_nevcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_storage_cap_rejects_befor0\probe.py | 153 | c68a60371511db260d00b212484f60a0 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_storage_cap_rejects_befor0\storage.ps1 | 543 | e4b668c2f9082327c99ab9b3f23cfeb2 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\pytest\test_storage_cap_rejects_beforcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\command.json | 354 | f9c2bc7e1494a312cee87d3c64296147 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\exit.json | 76 | 9dc304cb41867974f75c2096def9f276 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\NOTE_FAILURES.md | 760 | b6618c21b59b426ad6ffa23ad4847a56 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_child_environment_and_par0\child.json | 367 | 8356a1b8c820de0867a1670faa3936ed |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_child_environment_and_par0\harness.ps1 | 1114 | 3bb6b98da4be0d6ba9e5d66df0d57e6f |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_child_environment_and_par0\parent.json | 251 | 62a6acbb85723a7df752e03ed9d2da65 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_child_environment_and_par0\probe with spaces.py | 460 | f62b660759e4386a2e05990ee1d8aea0 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_child_environment_and_parcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_exited_child_cannot_leave0\descendant.json | 14 | 38f91a330242dd1f8a18493549c00b36 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_exited_child_cannot_leave0\pipe_probe.py | 346 | 6f3e09a27206f774fde93c26b391d07e |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_exited_child_cannot_leave0\pipes.ps1 | 283 | f549d72941129ed909505f5f2ba5d13c |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_exited_child_cannot_leavecurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_owned_cap_after_child_nev0\child-started | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_owned_cap_after_child_nev0\parent.json | 246 | e0eefaf4e00c7e105f3356c37b2774f0 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_owned_cap_after_child_nev0\post-cap.ps1 | 1498 | 54a6ccfab1741a9c619b0c2258cdd5fc |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_owned_cap_after_child_nev0\probe.py | 188 | 8905ff9b91f49230d7f47392cb5564f6 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_owned_cap_after_child_nev1\child-started | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_owned_cap_after_child_nev1\parent.json | 246 | 1f5f95600d861c1d955c78969e824f91 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_owned_cap_after_child_nev1\post-cap.ps1 | 1498 | 4c85461a2a94e2340d1b6b8acc5f7dcd |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_owned_cap_after_child_nev1\probe.py | 172 | e73a1f49e595214b4e4383cb1d6ce9de |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_owned_cap_after_child_nevcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_storage_cap_rejects_befor0\probe.py | 153 | 253e2a74bacbac646db91e360f8a7895 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_storage_cap_rejects_befor0\storage.ps1 | 543 | e8bddb0a6e6f5de9afae5679811288fe |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_storage_cap_rejects_beforcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\command.json | 354 | e677593677e275ed201355620992c013 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\exit.json | 76 | 08917913225732a15696d4168e3efa4f |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\NOTE_FAILURES.md | 736 | 07b6d726c2ac6e33efd2b90e54d75656 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_child_environment_and_par0\harness.ps1 | 1114 | b96081c64878249710b325df34c7859e |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_child_environment_and_par0\probe with spaces.py | 460 | 90eeef1ae0236bfb38ccd22319959be3 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_child_environment_and_parcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_exited_child_cannot_leave0\descendant.json | 36 | 107a6401a97e692e545cee478062400b |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_exited_child_cannot_leave0\pipe_probe.py | 376 | 734958287be09d9f4ea3bc532c9fca44 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_exited_child_cannot_leave0\pipes.ps1 | 283 | 788b23b193bfbf6f71293d177696026f |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_exited_child_cannot_leavecurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_owned_cap_after_child_nev0\child-started | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_owned_cap_after_child_nev0\parent.json | 246 | 69b24f320e0baef81db131df527457a2 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_owned_cap_after_child_nev0\post-cap.ps1 | 1498 | 4cdc62a4a21770c42c1032f6295c946f |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_owned_cap_after_child_nev0\probe.py | 188 | d2cd28f0007107385751d515c750bd1a |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_owned_cap_after_child_nev1\child-started | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_owned_cap_after_child_nev1\parent.json | 246 | 936155214f120108469e7fd70bb5799e |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_owned_cap_after_child_nev1\post-cap.ps1 | 1498 | 96d86eef68917751d2eb654bf67785a4 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_owned_cap_after_child_nev1\probe.py | 172 | 0e66457584bfc5a4cc25cbaca212074b |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_owned_cap_after_child_nevcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_storage_cap_rejects_befor0\probe.py | 153 | 2f7d9c940ef28db72069eac334e03df2 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_storage_cap_rejects_befor0\storage.ps1 | 543 | 0dd2ea1787847ff0addb4208e2da23b3 |
| D:\a14\evidence\test_logs\r14\qc\launcher-cap-green03\pytest\test_storage_cap_rejects_beforcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-green02\NOTE_FAILURES.md | 777 | 86356657d26d29529c7c04f0699720d1 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\command.json | 357 | 3b00c50d730f7d2edabc2a104d4fd575 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\exit.json | 76 | 577ed9d52808e2f915d288804d9f4ce3 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\NOTE_FAILURES.md | 805 | 7c1fdfc8ca3f2db9dcb5552025391b88 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\output.log | 1295 | 7aa58c49082bbd024f3a7bf184e3ed64 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_direct_exit_cannot_leave_0\child.json | 341 | f8f311bfca5320ad5ac3ef900faebd41 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_direct_exit_cannot_leave_0\harness.ps1 | 1647 | 8a6987dbb9ab54e4adaaf69f5493885f |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_direct_exit_cannot_leave_0\parent.json | 588 | fcff6d90d8b88450d21f67b96cd776d7 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_direct_exit_cannot_leave_0\probe.py | 695 | 0cf5f4f1a1d7bb6fd0611ff0e04571a3 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_direct_exit_cannot_leave_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_fixture_options_cannot_ac0\harness.ps1 | 1639 | b43d951b89e2144642a9856c7edad228 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_fixture_options_cannot_ac0\parent.json | 627 | d60fdaed5766385c5234e57066fc81b9 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_fixture_options_cannot_ac0\probe.py | 554 | 3685d9d8affddcd710e4277ab6cb3f67 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_fixture_options_cannot_accurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_live_refusal_stops_only_o0\child.json | 342 | 784c7cd7e8f7eb551cef1bec1db1be78 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_live_refusal_stops_only_o0\harness.ps1 | 1648 | a14403adc03ee159b3d190f39cacdfe0 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_live_refusal_stops_only_o0\parent.json | 610 | a0a0fbd9f7fdd803d331013ad0f42a8b |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_live_refusal_stops_only_o0\probe.py | 697 | f882415cd436fede795a40543a919d7b |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_live_refusal_stops_only_o1\child.json | 341 | 1b300779be0a803b3036b02c335c8e2d |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_live_refusal_stops_only_o1\harness.ps1 | 1647 | 1d56d9fb6f5e1e1b03b31697699d558d |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_live_refusal_stops_only_o1\parent.json | 605 | f2383b319bb838a238b8629ce13277b9 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_live_refusal_stops_only_o1\probe.py | 697 | 8adaeed3a0ad93ce867fe8cf8ce98ee8 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_live_refusal_stops_only_ocurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_resource_boundaries_and_a0\boundaries.json | 159 | 081d842ec51eed52f8a3e7186dbd073b |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_resource_boundaries_and_a0\probe.py | 6 | 5527939aca3e9e80d5ab3bee47391f0f |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_resource_boundaries_and_a0\resource-boundaries.ps1 | 1221 | e4be267896f17bd566fd0a0115f4547b |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_resource_boundaries_and_acurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_setup_preserves_caller_en0\child.json | 319 | 76c61c4919d9fe9276907ae5b6be0a07 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_setup_preserves_caller_en0\harness.ps1 | 1648 | d072a3a2d9833f80fd940ea2da62037f |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_setup_preserves_caller_en0\parent.json | 588 | 09808e61ea7826e9644c3fa00cbe56cb |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_setup_preserves_caller_en0\probe.py | 554 | d3b1c62b1e7c32756c0c2c33b7377f72 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_setup_preserves_caller_en1\child.json | 319 | 02a0d6d0b1c3c608a719a0464fa4ba89 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_setup_preserves_caller_en1\harness.ps1 | 1648 | 2f8d1f0d46a9a1cdaf05e259a185345e |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_setup_preserves_caller_en1\parent.json | 679 | b5401dbc26cf028cfb4c63cd03cfbba0 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_setup_preserves_caller_en1\probe.py | 554 | 2c9f5b9c552d1427ad4724482cece0c3 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_setup_preserves_caller_encurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_unset_caller_environment_0\child.json | 319 | 25cf1cbb760f9a2f3e436163be39046c |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_unset_caller_environment_0\harness.ps1 | 1940 | aeb9495916af1e62b6f25cc2876009f9 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_unset_caller_environment_0\parent.json | 370 | 30df145fc440a331b15d2281a3d6546b |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_unset_caller_environment_0\probe.py | 554 | 2352d5f20b845e54b1ba92efb1c056d4 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\pytest\test_unset_caller_environment_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\command.json | 357 | 605e8cd4847c7015da5ddafbf531e85a |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\exit.json | 76 | 17427ae84e3d358b90be90d17b3ead35 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\NOTE_FAILURES.md | 1094 | b9772761415ee44fead3bc325c971bc4 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\output.log | 3179 | 8574a631c043968cf6fa6c5fea5569ef |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_direct_exit_cannot_leave_0\child.json | 340 | bb03dd7fef963a5c40d75f5987748629 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_direct_exit_cannot_leave_0\harness.ps1 | 1647 | 7d5316012e863b8cd49566e3c7098d69 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_direct_exit_cannot_leave_0\parent.json | 588 | 1a6c3a0a8c66091844b0d1c67172efd3 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_direct_exit_cannot_leave_0\probe.py | 695 | f18c54ee3376118a2c8633a8e1a9a0a9 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_direct_exit_cannot_leave_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_fixture_options_cannot_ac0\harness.ps1 | 1639 | e15d9dafd8becdd9c7587aef4ab516db |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_fixture_options_cannot_ac0\parent.json | 627 | dedb4843f6be0079411ca88ce3ad9bde |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_fixture_options_cannot_ac0\probe.py | 554 | a66ae8bc47138c868f24e1175a3319c0 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_fixture_options_cannot_accurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_live_refusal_stops_only_o0\child.json | 341 | 7c30cf694c201caa3b31ea803a4350b8 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_live_refusal_stops_only_o0\harness.ps1 | 1648 | 74b7e861c2887b667687ec9ef4da516c |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_live_refusal_stops_only_o0\parent.json | 604 | 5d147091ae2cf89c7ca08da0540410cc |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_live_refusal_stops_only_o0\probe.py | 697 | 1c055a505ae9c83a3ec80c9e13e49e12 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_live_refusal_stops_only_o1\child.json | 342 | 55d4039b27a668f5692fcf2fc7a79985 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_live_refusal_stops_only_o1\harness.ps1 | 1647 | 2eba3c363a61259a6e0ce44644b678da |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_live_refusal_stops_only_o1\parent.json | 604 | 5b09fb608115b61553b2f0e3ebb63fd2 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_live_refusal_stops_only_o1\probe.py | 697 | 344d7cbadb063261da74e1ba243c05e0 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_live_refusal_stops_only_ocurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_resource_boundaries_and_a0\boundaries.json | 159 | f31bb580fcca2373c550a6e793cd3fe0 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_resource_boundaries_and_a0\probe.py | 6 | 5527939aca3e9e80d5ab3bee47391f0f |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_resource_boundaries_and_a0\resource-boundaries.ps1 | 1221 | 0f7f84519275d7806ba2ef8843412346 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_resource_boundaries_and_acurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_setup_preserves_caller_en0\child.json | 319 | 4323cbd5feb89a112546d4d28814c22a |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_setup_preserves_caller_en0\harness.ps1 | 1648 | 1231eff19b442f8f42ec39fcb3e2fca9 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_setup_preserves_caller_en0\parent.json | 588 | 1130c1dced1809602a70defa34c1812f |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_setup_preserves_caller_en0\probe.py | 554 | 0c7168d9f1304d134d2cc110dd3495f5 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_setup_preserves_caller_en1\child.json | 319 | c752a0eb24092714450dcb2231783295 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_setup_preserves_caller_en1\harness.ps1 | 1648 | 25d5a53ad585a94572f885d335963bfe |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_setup_preserves_caller_en1\parent.json | 679 | b1683858d59fe6b9d49652cc65e94eb0 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_setup_preserves_caller_en1\probe.py | 554 | 6729675abc76878cca03a4aea902f5a2 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_setup_preserves_caller_encurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_unset_caller_environment_0\child.json | 319 | b47f641d04f75c0596587ce2889f7d51 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_unset_caller_environment_0\harness.ps1 | 1940 | 7959ab34b27aa64d039027973d6e7547 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_unset_caller_environment_0\parent.json | 370 | 4ebc51349306cc9a45a556fbe99b1bdc |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_unset_caller_environment_0\probe.py | 554 | 0b6b888379ffd1fcd7760bc8e89e453c |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\pytest\test_unset_caller_environment_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\command.json | 357 | adc08986b85191532a10ce3980eed9c3 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\exit.json | 76 | c8ffe40349747f7d9aca6e29c5f9f564 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_direct_exit_cannot_leave_0\child.json | 341 | e221fe96abd9d5dba2ae35408bce29d9 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_direct_exit_cannot_leave_0\harness.ps1 | 1647 | cdc4382e353d729797178895f3fc7f10 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_direct_exit_cannot_leave_0\parent.json | 588 | 4d2f1b726cc5e41bfacbafc3dd1ad0b3 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_direct_exit_cannot_leave_0\probe.py | 695 | 1f456f20fe4cacac9a557ebbf2ad65d4 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_direct_exit_cannot_leave_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_fixture_options_cannot_ac0\harness.ps1 | 1639 | 4bdbe03ccd934e76cd27042c4aa7c370 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_fixture_options_cannot_ac0\parent.json | 627 | 980663e3b82e1497591a5185b16b2f7e |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_fixture_options_cannot_ac0\probe.py | 554 | ecbf4544cd4a0f003e8cd2e7bb3e9b44 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_fixture_options_cannot_accurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_live_refusal_stops_only_o0\child.json | 340 | 5be3b802f92bd0d2b523326ea7c2655c |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_live_refusal_stops_only_o0\harness.ps1 | 1648 | f817b9b2fa6539dd78a04323c2c5cee8 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_live_refusal_stops_only_o0\parent.json | 610 | 21c1ac978009bbff30288944de73b1f4 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_live_refusal_stops_only_o0\probe.py | 697 | dcca0ca2729177b6664e3a5e4cdad66b |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_live_refusal_stops_only_o1\child.json | 341 | 8e31230d7e096c3045113dfc9b9b0e80 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_live_refusal_stops_only_o1\harness.ps1 | 1647 | 4d230c92e2b29a5b8b88e6fd05d5deef |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_live_refusal_stops_only_o1\parent.json | 605 | da1c7118a48ff437151dc06786ac1151 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_live_refusal_stops_only_o1\probe.py | 697 | 3446637bb0eaa88b11a50e80128d4234 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_live_refusal_stops_only_ocurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_resource_boundaries_and_a0\boundaries.json | 159 | 6497fb69f2d2edeb3fc06c2364fdd90b |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_resource_boundaries_and_a0\probe.py | 6 | 5527939aca3e9e80d5ab3bee47391f0f |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_resource_boundaries_and_a0\resource-boundaries.ps1 | 1221 | a244a6f24dc07c713a174d2bf9cfd116 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_resource_boundaries_and_acurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_setup_preserves_caller_en0\child.json | 319 | 0a90628241f4b3689bbb1cc1238c9928 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_setup_preserves_caller_en0\harness.ps1 | 1648 | 8bc31ea2991993cf2872a33ab49c8f71 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_setup_preserves_caller_en0\parent.json | 588 | f91ff46cbd34f3d1e4a0c470ba6dbe58 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_setup_preserves_caller_en0\probe.py | 554 | dee10d3b66f0607f922b10a0084080a4 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_setup_preserves_caller_en1\child.json | 319 | 016d71aa2527893d57249e0603ab3e79 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_setup_preserves_caller_en1\harness.ps1 | 1648 | a44510987a6b2e785c8d31f948b63593 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_setup_preserves_caller_en1\parent.json | 679 | 07ab728fe5cc58df1720c2574856bba5 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_setup_preserves_caller_en1\probe.py | 554 | 54011814b6ca1f94372bf8976adb9bc2 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_setup_preserves_caller_encurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_unset_caller_environment_0\child.json | 319 | 27b99b301765b68c516a012f6500e4de |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_unset_caller_environment_0\harness.ps1 | 1940 | 5d8ef48b426279a5aad841621e467065 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_unset_caller_environment_0\parent.json | 370 | 87c6837778561a3e304bda98ae5eb854 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_unset_caller_environment_0\probe.py | 554 | 4925c1f248042f0f55949d847b421867 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-green03\pytest\test_unset_caller_environment_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\command.json | 355 | 9f5b3b169e6eb1ee424d7ab3545b2c3b |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\exit.json | 76 | eb52df68223f172802bca8ae57c2984a |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\output.log | 1103 | 58388514f439b92bd5b5d1059c525e6f |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_direct_exit_cannot_leave_0\child.json | 341 | 2ddb3e3a8e89870e81929bfd3f4383af |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_direct_exit_cannot_leave_0\harness.ps1 | 1643 | ff6d5c389d7b1c4dcb8799e41ad444bd |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_direct_exit_cannot_leave_0\parent.json | 588 | 4d3bdf1ee4d4612856e7e525dd731802 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_direct_exit_cannot_leave_0\probe.py | 693 | 07072d5b157a1bcfd5ebdbc9a50dc13f |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_direct_exit_cannot_leave_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_fixture_options_cannot_ac0\harness.ps1 | 1635 | 1d058887542006988e4b53cea25143f2 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_fixture_options_cannot_ac0\parent.json | 627 | 272c5992711fad06303efa6dfa48da0f |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_fixture_options_cannot_ac0\probe.py | 552 | 4b8b80e84d8c7a66c8850916f87fe947 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_fixture_options_cannot_accurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_live_refusal_stops_only_o0\child.json | 340 | 54b06a618349191766871ec1436efbac |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_live_refusal_stops_only_o0\harness.ps1 | 1644 | fa66110b5c5f99a35a2a7153ee092c21 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_live_refusal_stops_only_o0\parent.json | 610 | 27516b0f99d0b8fd7eac927fd1d6d82e |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_live_refusal_stops_only_o0\probe.py | 695 | 59d1a43cd510e2023017b997e2ea8eca |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_live_refusal_stops_only_o1\child.json | 340 | 3a108f292c70235163c8de0a4f7d4cb8 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_live_refusal_stops_only_o1\harness.ps1 | 1643 | 9bf824c9412e377c86e3aa9e96a1d8f8 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_live_refusal_stops_only_o1\parent.json | 605 | 72b8db7f4ff5082b564c7466517e471a |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_live_refusal_stops_only_o1\probe.py | 695 | 6dedaa4c34148a849b9f43e6009bff30 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_live_refusal_stops_only_ocurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_resource_boundaries_and_a0\boundaries.json | 159 | 6497fb69f2d2edeb3fc06c2364fdd90b |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_resource_boundaries_and_a0\probe.py | 6 | 5527939aca3e9e80d5ab3bee47391f0f |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_resource_boundaries_and_a0\resource-boundaries.ps1 | 1217 | c9c426d2514f964493bbe482ac563d18 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_resource_boundaries_and_acurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_setup_preserves_caller_en0\child.json | 320 | 018363df87661cd6e027e4542cab81dc |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_setup_preserves_caller_en0\harness.ps1 | 1644 | 77cd34354973a8ded28e7042107c9a08 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_setup_preserves_caller_en0\parent.json | 588 | 7def5142f8ce1e2a8eeafc1b47e259b6 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_setup_preserves_caller_en0\probe.py | 552 | 4982425fadb1072c6dcf182de75790fa |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_setup_preserves_caller_en1\child.json | 319 | 5b7cb3f9b0060b769aaadbc0e1629071 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_setup_preserves_caller_en1\harness.ps1 | 1644 | 04ba1b07f1a268861b4d01176a01e9ae |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_setup_preserves_caller_en1\parent.json | 679 | edace9535fd8d98ba8f7a8a59d9f3d01 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_setup_preserves_caller_en1\probe.py | 552 | d5da74582239ea7c8122468dcb30c21e |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_setup_preserves_caller_encurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_unset_caller_environment_0\child.json | 320 | 23fc3e5a0c4306376c9faccea5412fa8 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_unset_caller_environment_0\harness.ps1 | 1936 | 0214ca064677485cf84c67b5a70d5ac6 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_unset_caller_environment_0\parent.json | 370 | 2cee1b382a88f0b35d0bfb8ae6aefca0 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_unset_caller_environment_0\probe.py | 552 | 5e7d97d7d01df07c66ca51da0cae0549 |
| D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_unset_caller_environment_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\R14_SUITE_CONFIG_PIN_MILESTONE.md | 3084 | c1b3896f4a4ae85737f945a2fef4f1d3 |
| D:\a14\evidence\test_logs\r14\runtime-containment-command.ps1 | 1283 | a9e33aede7d62a220313a17167493b54 |
| D:\a14\evidence\test_logs\r14\runtime-containment-red01\output.log | 2319 | bcf11b898d79f573438d83ea157911f3 |
| D:\a14\evidence\test_logs\r14\runtime-marker-green01\output.log | 101 | a655429a88a9e9642a6287c032af85fb |
| D:\a14\evidence\test_logs\r14\runtime-marker-red01\output.log | 2877 | 7cbdfcb95d505d6ed27eef78781d4801 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture01\driver\maps\source_000_boundaries_0001.bin | 81 | e0f56ecdb62b1c973be9daba21acaac7 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture01\driver\maps\source_000_pairs_0001.bin | 9000 | fa955516ecc2ff2400734698db4198a1 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture01\driver\maps\source_000_ranges_0001.bin | 153 | 3c2946cb5e3b06e3d13c0d9b82bdc7d5 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture01\driver\maps\source_001_boundaries_0001.bin | 81 | 65d72aa9f59e2a7a4911981c9d8ece30 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture01\driver\maps\source_001_pairs_0001.bin | 9000 | 7de0970dfba7b702e82aaa0807d1a6f2 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture01\driver\maps\source_001_ranges_0001.bin | 170 | 7902c821542646840826bc413a8cbacc |
| D:\a14\evidence\test_logs\r14\segments\native_fixture01\driver\progress.jsonl | 1923 | 3e59cd5d89ec675f3def023430f62230 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture01\synthetic_000.txt | 70789 | 7bbed6db29d3f10d40326d69f35093dd |
| D:\a14\evidence\test_logs\r14\segments\native_fixture01\synthetic_001.txt | 85316 | 9b4d20fdefcc27e3502340835c1190ef |
| D:\a14\evidence\test_logs\r14\segments\native_fixture02\driver\maps\source_000_boundaries_0001.bin | 81 | e0f56ecdb62b1c973be9daba21acaac7 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture02\driver\maps\source_000_pairs_0001.bin | 9000 | fa955516ecc2ff2400734698db4198a1 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture02\driver\maps\source_000_ranges_0001.bin | 153 | 3c2946cb5e3b06e3d13c0d9b82bdc7d5 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture02\driver\maps\source_001_boundaries_0001.bin | 81 | 65d72aa9f59e2a7a4911981c9d8ece30 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture02\driver\maps\source_001_pairs_0001.bin | 9000 | 7de0970dfba7b702e82aaa0807d1a6f2 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture02\driver\maps\source_001_ranges_0001.bin | 170 | 7902c821542646840826bc413a8cbacc |
| D:\a14\evidence\test_logs\r14\segments\native_fixture02\driver\progress.jsonl | 1938 | 53f5dc5e0f5d46ba9560b1c0c88fe2a9 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture02\synthetic_000.txt | 70789 | 7bbed6db29d3f10d40326d69f35093dd |
| D:\a14\evidence\test_logs\r14\segments\native_fixture02\synthetic_001.txt | 85316 | 9b4d20fdefcc27e3502340835c1190ef |
| D:\a14\evidence\test_logs\r14\segments\native_fixture03\driver\maps\source_000_boundaries_0001.bin | 81 | e0f56ecdb62b1c973be9daba21acaac7 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture03\driver\maps\source_000_pairs_0001.bin | 9000 | fa955516ecc2ff2400734698db4198a1 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture03\driver\maps\source_000_ranges_0001.bin | 153 | 3c2946cb5e3b06e3d13c0d9b82bdc7d5 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture03\driver\maps\source_001_boundaries_0001.bin | 81 | 65d72aa9f59e2a7a4911981c9d8ece30 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture03\driver\maps\source_001_pairs_0001.bin | 9000 | 7de0970dfba7b702e82aaa0807d1a6f2 |
| D:\a14\evidence\test_logs\r14\segments\native_fixture03\driver\maps\source_001_ranges_0001.bin | 170 | 7902c821542646840826bc413a8cbacc |
| D:\a14\evidence\test_logs\r14\segments\native_fixture03\driver\progress.jsonl | 1922 | d0b016f9b8a52ea884de7b439e7356ee |
| D:\a14\evidence\test_logs\r14\segments\native_fixture03\synthetic_000.txt | 70789 | 7bbed6db29d3f10d40326d69f35093dd |
| D:\a14\evidence\test_logs\r14\segments\native_fixture03\synthetic_001.txt | 85316 | 9b4d20fdefcc27e3502340835c1190ef |
| D:\a14\evidence\test_logs\r14\segments\pytest_green01\test_edges_and_prefix_hash_ent0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_green01\test_edges_and_prefix_hash_entcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_edges_and_prefix_hash_ent0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_edges_and_prefix_hash_entcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_map_abort_does_not_flush_0\maps\source_013_pairs_0001.bin | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_map_abort_does_not_flush_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_map_parts_preserve_exact_0\maps\source_013_ranges_0001.bin | 34 | cef53ee404a7be76a2e0b21cf3795cf2 |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_map_parts_preserve_exact_0\maps\source_013_ranges_0002.bin | 17 | 43763cae6ef85784b3c4a9e3fd81ecb6 |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_map_parts_preserve_exact_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_map_writer_rejects_unknowcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_prefix_unscanned_tail_sti0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_prefix_unscanned_tail_sticurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_window_scope_openness_is_0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_green02\test_window_scope_openness_is_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_edges_and_prefix_hash_ent0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_edges_and_prefix_hash_entcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_map_abort_does_not_flush_0\maps\source_013_pairs_0001.bin | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_map_abort_does_not_flush_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_map_parts_preserve_exact_0\maps\source_013_ranges_0001.bin | 34 | cef53ee404a7be76a2e0b21cf3795cf2 |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_map_parts_preserve_exact_0\maps\source_013_ranges_0002.bin | 17 | 43763cae6ef85784b3c4a9e3fd81ecb6 |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_map_parts_preserve_exact_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_map_writer_rejects_unknowcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_prefix_unscanned_tail_sti0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_prefix_unscanned_tail_sticurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_window_scope_openness_is_0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_green03\test_window_scope_openness_is_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_edges_and_prefix_hash_ent0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_edges_and_prefix_hash_entcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_map_abort_does_not_flush_0\maps\source_013_pairs_0001.bin | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_map_abort_does_not_flush_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_map_parts_preserve_exact_0\maps\source_013_ranges_0001.bin | 34 | cef53ee404a7be76a2e0b21cf3795cf2 |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_map_parts_preserve_exact_0\maps\source_013_ranges_0002.bin | 17 | 43763cae6ef85784b3c4a9e3fd81ecb6 |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_map_parts_preserve_exact_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_map_writer_rejects_unknowcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_prefix_unscanned_tail_sti0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_prefix_unscanned_tail_sticurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_window_scope_openness_is_0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_green04\test_window_scope_openness_is_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_edges_and_prefix_hash_ent0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_edges_and_prefix_hash_entcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_map_abort_does_not_flush_0\maps\source_013_pairs_0001.bin | 9 | 5163c52db6a9aac91a1dc2e161f73fb5 |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_map_abort_does_not_flush_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_map_parts_preserve_exact_0\maps\source_013_ranges_0001.bin | 34 | cef53ee404a7be76a2e0b21cf3795cf2 |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_map_parts_preserve_exact_0\maps\source_013_ranges_0002.bin | 17 | 43763cae6ef85784b3c4a9e3fd81ecb6 |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_map_parts_preserve_exact_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_map_writer_rejects_unknow0\maps\source_013_typo_0001.bin | 9 | 5163c52db6a9aac91a1dc2e161f73fb5 |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_map_writer_rejects_unknowcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_prefix_unscanned_tail_sti0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_prefix_unscanned_tail_sticurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_window_scope_openness_is_0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_red02\test_window_scope_openness_is_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_edges_and_prefix_hash_ent0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_edges_and_prefix_hash_entcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_map_abort_does_not_flush_0\maps\source_013_pairs_0001.bin | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_map_abort_does_not_flush_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_map_parts_preserve_exact_0\maps\source_013_ranges_0001.bin | 34 | cef53ee404a7be76a2e0b21cf3795cf2 |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_map_parts_preserve_exact_0\maps\source_013_ranges_0002.bin | 17 | 43763cae6ef85784b3c4a9e3fd81ecb6 |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_map_parts_preserve_exact_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_map_writer_rejects_unknowcurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_prefix_unscanned_tail_sti0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_prefix_unscanned_tail_sticurrent | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_window_scope_openness_is_0\source.txt | 282 | 5e60c8dd0db805e833f47fb6bf539fdf |
| D:\a14\evidence\test_logs\r14\segments\pytest_red04\test_window_scope_openness_is_current | - | deleted on the branch |
| D:\a14\evidence\test_logs\r14\suite-pure-command.ps1 | 1231 | d7e2de841113a0696df4c33af9e3a36a |
| D:\a14\evidence\test_logs\r14\suite-review-before-config\Invoke-R14Suite.ps1 | 9800 | e242a33d1580220d05ac569413a0f66e |
| D:\a14\evidence\test_logs\r14\suite-review-before-config\r14_suite.py | 11846 | 22d946817e6c8dd563f285626555083e |
| D:\a14\evidence\test_logs\r14\suite-runner-command.ps1 | 1109 | b0dd1fd9f62e730d5c8c980580e56aa3 |
| D:\a14\evidence\test_logs\r14\suite-runner-green01\NOTE_FAILURES.md | 1375 | 70e2338557d78de229479b7e9571b194 |
| D:\a14\evidence\test_logs\r14\suite-runner-green01\output.log | 6829 | 5121aa9278d16c8b03f164ff2238841c |
| D:\a14\evidence\test_logs\r14\suite-runner-red01\output.log | 13830 | d07bbaaabb80337390db7e9178b9a856 |
| D:\a14\PLAN.md | 9383 | d7c20b402a5619255ea457cc5d135e6f |
| D:\a14\R14_STATUS.md | 2381 | 589debc45017d648baa0f82c5ad955fe |
| D:\a14\sep\boardstm-probe01\PROBE.json | 16860 | ef049b82dce36eeb92e8434467612af6 |
| D:\a14\sep\boardstm-probe01\progress.jsonl | 6188 | 0913d296363870f868ff607534f5e587 |
| D:\a14\sep\boardstm-probe01\SHARED.jsonl | 2919239 | ea9d1e3024daf1fe0a3e70d11207e36b |
| D:\a14\sep\boardstm-probe01\TRIAGE_probe_only.json | 8192 | c8feadf5690078af4924e0c09ad772b3 |
| D:\a14\sep\boardstm-probe01\TRIAGE_probe_only_ROWS.tsv | 4179966 | ec05042753b0f4466e36dfc0a148c064 |
| D:\a14\sep\boardstm-probe01\TRIAGE_probe_only_tip.json | 8072 | 495d50516a677db302396502fe0b09f5 |
| D:\a14\sep\BOARDSTM_TRIAGE.json | 8519 | e18f8fe3dd2880f9d3d1235278abfd84 |
| D:\a14\sep\BOARDSTM_TRIAGE_ROWS.tsv | 4179966 | ec05042753b0f4466e36dfc0a148c064 |
| D:\a14\sep\GAMES_SIDECAR_PROPOSAL.md | 4323 | 5a911c209c7d3039fbbd1d33311274ea |
| D:\a14\sep\guardband01\DROPPED.tsv | 149154 | b134521039739137e02d59e2eb7f4fd5 |
| D:\a14\sep\guardband01\PROOF.json | 4811 | 04da3cfa633aceeccd89dda67edf6837 |
| D:\a14\sep\guardband01\SPLIT.json | 4053 | f2304604a07ceab3d8baca0da3661a26 |
| D:\a14\sep\GUARDBAND_SEPARATION.json | 4503 | 1b4b901e91f03622d94df39907ba5f2e |
| D:\a14\sep\overlap-production03\progress.jsonl | 73985 | 9c624559be14f7684fce81716b91b11b |
| D:\a14\sep\overlap-production03\REPORT.json | 46560 | 1607d19e2b66dbe3512d0997942523c4 |
| D:\a14\sep\overlap-production04\progress.jsonl | 71077 | a59234c445324ed4d512f9a9edb6495b |
| D:\a14\sep\overlap-production04\REPORT.json | 4725890 | d74118d6690d3af75838f62fc605e73f |
| D:\a14\sep\PROD_SEPARATION.json | 6494 | 3bccfa9b074a3050d436f08a29dd1b7e |
| D:\a14\sep\RETRY_PLAN.md | 2598 | a8f908df1306da233f8edd0ae6fff4e1 |
| D:\a14\sep\segments-production02\maps\source_012_boundaries_0001.bin | 16029 | a482d116c035b97ea16fb8bdfba765c2 |
| D:\a14\sep\segments-production02\maps\source_012_pairs_0001.bin | 900000 | 2c3b09c99bfedbf3572db0f82bf0580b |
| D:\a14\sep\segments-production02\maps\source_012_ranges_0001.bin | 30277 | e0b3609ca124c2df107e7c83b5c9e85b |
| D:\a14\sep\segments-production02\maps\source_013_boundaries_0001.bin | 1589346 | 968cc302cf3b27adcf2387fc78e04ed0 |
| D:\a14\sep\segments-production02\maps\source_013_pairs_0001.bin | 10485756 | c9005812fae186bc9c9cef1e71698413 |
| D:\a14\sep\segments-production02\maps\source_013_pairs_0002.bin | 10485756 | 013628cee4b25fadfb29ad9b9c5ea764 |
| D:\a14\sep\segments-production02\maps\source_013_pairs_0003.bin | 10485756 | df3798ed31b45a41f20fd73808a5c670 |
| D:\a14\sep\segments-production02\maps\source_013_pairs_0004.bin | 10485756 | 7c0e37df143fe31881694dcbaeb4ae59 |
| D:\a14\sep\segments-production02\maps\source_013_pairs_0005.bin | 10485756 | fd0e0672a108f217043d736e5f706c2c |
| D:\a14\sep\segments-production02\maps\source_013_pairs_0006.bin | 10485756 | 6ff8de3aeebdfe7a7855d11e946fca43 |
| D:\a14\sep\segments-production02\maps\source_013_pairs_0007.bin | 10485756 | c9c7975aa4faed7bb76c302655087917 |
| D:\a14\sep\segments-production02\maps\source_013_pairs_0008.bin | 10485756 | 5824961a2464831a21c99045656d680a |
| D:\a14\sep\segments-production02\maps\source_013_pairs_0009.bin | 6113952 | 688718d3b1bfae4017a2cd1b4aca07ad |
| D:\a14\sep\segments-production02\maps\source_013_ranges_0001.bin | 3002098 | 9362fd9a1856fbc841d052523c81aa0e |
| D:\a14\sep\segments-production02\maps\source_014_boundaries_0001.bin | 1022076 | 1efc18dd2b1004b70828467858d0355c |
| D:\a14\sep\segments-production02\maps\source_014_pairs_0001.bin | 10485756 | 206d5daf2c9e850bcb78dfac19466e69 |
| D:\a14\sep\segments-production02\maps\source_014_pairs_0002.bin | 10485756 | 9056e7dc612f78ad143a940ad5ff8cbb |
| D:\a14\sep\segments-production02\maps\source_014_pairs_0003.bin | 10485756 | a053197b79ac35f2dcce216c14fe6df0 |
| D:\a14\sep\segments-production02\maps\source_014_pairs_0004.bin | 10485756 | 6a84da8d9ef92745d7e35a96a295149d |
| D:\a14\sep\segments-production02\maps\source_014_pairs_0005.bin | 10485756 | 902e30c1ebd49bfe2ee46aadb8967a36 |
| D:\a14\sep\segments-production02\maps\source_014_pairs_0006.bin | 5068395 | 667febb4abfad627a8b0eb552e2587e3 |
| D:\a14\sep\segments-production02\maps\source_014_ranges_0001.bin | 1930605 | 1445d80ffb0456cbb4ed85eff155ad45 |
| D:\a14\sep\segments-production02\maps\source_015_boundaries_0001.bin | 16596 | aa135fec3fff8081d8a5813254ea82ba |
| D:\a14\sep\segments-production02\maps\source_015_pairs_0001.bin | 900000 | de8b08db8fe4ada5b84e5f7e28900bb0 |
| D:\a14\sep\segments-production02\maps\source_015_ranges_0001.bin | 31348 | c4c19ecb5105404a604e1d5c0964c1b9 |
| D:\a14\sep\segments-production02\MAPS_SEAL.json | 5083 | 9b708a8994edc0f87ad8283c783440bb |
| D:\a14\sep\segments-production02\native.stderr.log | 0 | d41d8cd98f00b204e9800998ecf8427e |
| D:\a14\sep\segments-production02\progress.jsonl | 60468 | 8d5697058a7dcc10c9b90c7f2368f57e |
| D:\a14\sep\segments-production02\REPORT.json | 36889 | fcb488f8c726326e013f648e1d202760 |
| D:\a14\sep\TOOL_MD5_CHAIN.md | 4281 | 038647fcf3ffe3763f3f31c6416ca444 |
| D:\a14\tests\r14_qualification\test_qualification.py | 13787 | c62cce4fbd40fe5b4cc00c2cfef7181f |
| D:\a14\tests\test_opus_boardstm_probe.py | 2921 | f45ced07034f7738d359ecc2029eeafd |
| D:\a14\tests\test_opus_boardstm_triage.py | 4106 | 25812dba613a439b34f43ebf9a51bd5d |
| D:\a14\tests\test_opus_ep.py | 2413 | bb81fa7d2d7c6a25a7fa24853bb41a32 |
| D:\a14\tests\test_opus_promote_export.py | 2418 | 36ba9f2f79a5f5d1ec0505edec86c659 |
| D:\a14\tests\test_r14_boundary.py | 9225 | 18b67115e086367b8ecad8b5aa351ded |
| D:\a14\tests\test_r14_boundary_publication.py | 6299 | 6657ff9405db6d89a2e4758f046e94e5 |
| D:\a14\tests\test_r14_boundary_qualify.py | 1467 | 58c975f15ad5319f5fb66fab2ecd1a4f |
| D:\a14\tests\test_r14_boundary_run.py | 8394 | e6104e46872859ed293b7923963b8249 |
| D:\a14\tests\test_r14_overlap.py | 15521 | 8c3c5d91fce110dc3444816b8a8c8fc3 |
| D:\a14\tests\test_r14_preflight.py | 2099 | dfdf6235e5d88aed5f99bbfd2464cd51 |
| D:\a14\tests\test_r14_suite.py | 10357 | d223977476a26d68fb4dd2e8749b897a |
| D:\a14\TOOLS.md | 10940 | 89f181ae43a42bbe76422569f5d2d64b |
| D:\a14\tools\Invoke-R14Suite.ps1 | 10313 | bfb2096320d5cabe7040b123688b910a |
| D:\a14\tools\opus_boardstm_probe.py | 12373 | ab989d17cca0b703b9b281855a71a81d |
| D:\a14\tools\opus_boardstm_triage.py | 12294 | 63e82e3a820a5495c258fa25efcd2b8f |
| D:\a14\tools\opus_ep.py | 7321 | 1b142bc9941e0b8c791c65adbfb472db |
| D:\a14\tools\opus_guardband.py | 13274 | bf2afb3de7bd5f6632a95c708b68bc4f |
| D:\a14\tools\opus_guardband_proof.py | 17602 | 6c974b2e446182ba875a74a4a32fb334 |
| D:\a14\tools\opus_guardband_record.py | 4505 | 1b8c9e77bb99ee13c0966c32653199b3 |
| D:\a14\tools\opus_inventory.py | 2574 | 1b63d0c0b6e7573942709c63d2aa17a7 |
| D:\a14\tools\opus_lowrun.py | 1755 | 0787fcaa38297f6df4c0fb8ae59b74bb |
| D:\a14\tools\opus_prod_separation.py | 12330 | 7f0a3ae03e02a2b8ee551c3548aef782 |
| D:\a14\tools\opus_promote_export.py | 4617 | 0bc94d4267529aec152a8ad92927c7db |
| D:\a14\tools\opus_pypi_hashes.py | 3169 | 50e32a68a8dd5b832d128c1c69ca137b |
| D:\a14\tools\opus_seal.py | 5463 | 6742803a4cb4908bee3e266768b02823 |
| D:\a14\tools\opus_silent_sweep.py | 3888 | b1571a0557a427c2319b0140c23647d6 |
| D:\a14\tools\opus_step0_verify.py | 1880 | 473259754c6149b865cb8d8f5fb09c4b |
| D:\a14\tools\opus_tools_md.py | 7281 | c11122cf13259758266bd526384df5e0 |
| D:\a14\tools\R14-OwnedJob.ps1 | 10278 | 362b00c4ce50c88cc7f2c4778d5af7d1 |
| D:\a14\tools\r14_boundary.py | 12286 | 7345624b054fac9af29c1546912736fa |
| D:\a14\tools\r14_boundary_FORMAT.md | 4992 | 65345d826546dc0871ccd0180793ef14 |
| D:\a14\tools\r14_boundary_qualify.py | 8328 | ea5bee2a0b300ee06544d183514e3350 |
| D:\a14\tools\r14_boundary_run.py | 23870 | c0eb24d8f1acbfc5c6c40fd0529412be |
| D:\a14\tools\r14_overlap.py | 18251 | a0fd44c5da2cf138492e77f438d7bdd4 |
| D:\a14\tools\r14_qualification\qualify.py | 33208 | ccdfac440ea8998e8da81f6e6d35dfdf |
| D:\a14\tools\r14_segments.py | 30316 | 5b82a577fbedd2f602605e070aef47f9 |
| D:\a14\tools\r14_segments_fixture_probe.py | 6708 | eeeb4953b4c9346a86dbda30f52bd62d |
| D:\a14\tools\r14_suite.ini | 9 | b9d12b7f4027e03000d178ccb2a49077 |
| D:\a14\tools\r14_suite.py | 14113 | 682cb61a711a9ec84636caed7e76e2a9 |
| D:\a14\tools\requirements-r14-hashes.txt | 1865 | bbbc4e3d4eee078420560f028d4d9297 |
| D:\a14\tools\Setup-R14Runtime.ps1 | 11880 | 75b14c067157b50c0fefdab8e7170418 |
