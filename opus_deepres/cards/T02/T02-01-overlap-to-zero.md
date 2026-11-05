# T02-01: Drive the train/holdout overlap to 0 - board+stm drop list plus a block-aligned (game-level) split
Status: COMPLETE (algorithm, measured costs and proofs; nothing executed on production data)

## Source
Own records only: `D:\a14\FINAL_REPORT.md` ("Is the npt data unblocked?", Job 2), `D:\a14\sep\BOARDSTM_TRIAGE_ROWS.tsv`
(md5 ec05042753b0f4466e36dfc0a148c064; one line per shared row: key, class, side, path, line, fen, ep_status,
normalised_4field), `sep\PROD_SEPARATION.json` (FAIL), `sep\WRITER_EVIDENCE.md`, `sep\GAMES_SIDECAR_PROPOSAL.md`,
`F:\forge_j1_data\convert.log`, skill forge-nnue-data, `tools/block_rule_check.py` -> `notes/T02/block_rule_012_015.json`.

## Licence
Own code and own data; nothing external.

## Mechanism
1. Key. The J1 train binpack is written from FPOS rows (32-byte board + side to move + score + result: no castling,
   no en passant, no clocks), 34 bytes per unchained record. The net therefore sees board + side to move only, and that
   key subsumes the others: every raw or EP-normalised 4-field match is a board+stm match.
2. Drop list. The 7,700 rows of the TSV with side = train (a complete listing: overlap-production04 listing_complete
   true, identical key for key to the independent probe). Minimum for "4,088 -> 0": the 4,118 train rows whose
   normalised_4field equals a holdout row's (recounted here from the TSV: 4,118, spread over all 37 train files, 3-226
   per file). Recommended: all 7,700 (0.0025 % of 304,999,573); the castling-only twins are identical binpack records.
   Dropping the 7,612 holdout rows instead is rejected: it would change the reference holdout behind every S31 number.
3. Rebuild. `.pos` record index = text line - 1 (013's `.pos.info`: lines = records = 10,000,000, bad 0). Copy the 37
   train `.pos` files without the listed records, convert with the same converter (exe sha256 C3672C3D..., per-shard
   verify: records = expected, mismatches 0) and concatenate in the J1 order -> 304,991,873 records.
4. Game level. No row carries an authentic game ID (UNVERIFIED for 001-039, cannot be fixed afterwards). Derived blocks:
   a new block starts when the result changes or the ply does not increase (writer invariants: one game = one block in
   play order with one result), so blocks are unions of games and never cut one. Measured on the R14 scan range (last
   100k rows of 012, 013, 014, first 100k of 015; 16,588,575 rows in 17.6 s): 189,182 blocks (87.7 rows each);
   result_mismatch 121,492 / nonpositive_ply_gap 67,689 vs the R14 scan's 121,467 / 67,730 (16 pairs apart in 189k).
   Both train/holdout seams are block breaks (012:2,625,970 -> 013:1 result_mismatch; 014:6,388,575 -> 015:1
   nonpositive_ply_gap), so the 013/014 file split is already block-aligned. Any NEW split (a validation slice inside
   training files) must cut at block breaks only. New data: the `.games` sidecar gives authentic IDs.
5. Not measured: within-train board+stm duplicates (castling / EP twins inside train) - a crew measurement (one keyed
   pass; the R11 dedup does it), not needed for the overlap.

## Forge fit
Data pipeline only. The R11 pipeline already dedups on (32-byte board, stm) with 013/014 first in the registry and
has a full-scan holdout proof (`opus_r11/tests/test_r11_holdout_real.py`); the J1 binpack skipped that step.

## Expected gain
Direct Elo: none expected - 7,700 rows are 0.0025 % of train and 7,612 are 0.046 % of the holdout. Value: the overlap
check turns from FAIL to PASS on all three keys, which unblocks training on 001-039 under the audit (game identity
stays derived, not authentic). Forge estimate: 0 Elo directly, UNPROVEN; an enabler for every T01/T02 net.

## Effort
Crew ~2 h with existing tools. CPU (one core): convert 39 shards 6 min 19 s incl. verify (convert.log
17:18:18-17:24:37), probe re-scan 388 s (boardstm-probe01), block pass over all 321M rows ~6 min (17.6 s per 16.6M
rows measured): under 30 min. Disk 10.37 GB for the new binpack: put it on C: (F: had 59.6 GB at 22:23; 10.4 GB more
would breach its 50 GB floor). Never overwrite `F:\forge_j1_data` (the live trainer reads it). GPU: none for the fix.

## Test plan
Before any training, all PASS: (1) record count 304,991,873; (2) decode the 7,700 dropped records, board+stm equal to
the TSV rows 7,700/7,700 (proves line -> record); (3) independent re-scan (the probe with the drop list, or the R11
holdout test on the new set): 0 shared keys for board+stm, raw and EP-normalised 4-field, fill rate 1.0; (4) both seams
are block breaks (`tools/block_rule_check.py`); (5) md5 + sha256 seals of drop list, binpack and scan JSON. Then train
as usual, holdout loss vs the lock net, and the gate route of the retrained net: UHO SPRT [0,5] at STC, then LTC.

## OFF-by-default design
Not an engine change: no option, no build switch, lock bench pins untouched by construction. The old binpack stays;
the cleaned one is a new file with its own name, drop list and seal.
