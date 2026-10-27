# S16 Real 013/014 overlap check: Sol's filter (v3) and a read-only overlap scanner

Two tools, one question: do the training shards contain positions or games of the 013/014 holdout?

| tool | what it does | when to use it |
|---|---|---|
| `filter_v3/` Sol's offline filter, v3 | builds NEW filtered training shards: drops holdout positions, holdout game groups, duplicates and (optionally) score/result disagreements; SQLite work DB; removal ledger; one-command runners (`sh`, `pwsh`) | producing filtered data on a quiet machine (scratch about 300 B/row) |
| `forge_sol_S16_overlap_scan.py` | counts and lists the overlap without writing any training data; streaming, exact, read-only, < 0.5 GB RAM | checking the real data on the busy PC (232M rows in about 8.5 min at Idle priority) |

Both use Sol's Job D identity: **board32 + side to move** (FPOS stores no castling, e.p. or clocks), and Sol's
conservative game rule over the ordered text: a new game starts when the fullmove number decreases, the piece count
increases or the WHITE result changes (missed boundaries merge games, so groups are supersets of games).

## Where the real data is (PC, read-only)
- positions: `D:\grok-pc-data\forge_push\nnue_data\pos\forge_selfplay_NNN.pos` (FPOS v1: 16-byte header, then
  boards 32 B, scores i16, meta u8 per row, columnar); labels `...\nnue_data\hce\*.hce`; ordered text (one line per
  row, `FEN | STM score | WHITE result`) `D:\grok-pc-data\selfplay_out\forge_selfplay_NNN.txt`.
- The live trainer (`--holdout`) holds out exactly 013 and 014 and trains on 001-012 + 015-031 (29 shards).
  `F:\forge_nnue_train` has logs and run folders only. There is no Job D output on the PC.
- Self-play is still writing (`forge_selfplay_032.txt.part`): treat every file there as read-only.

## Scanner usage
```
nice -n 19 <python with numpy> -I -B forge_sol_S16_overlap_scan.py \
  --holdout <pos>/forge_selfplay_013.pos <pos>/forge_selfplay_014.pos \
  --train <pos>/forge_selfplay_001.pos ... (the trainer's --train list) \
  --text-dir D:/grok-pc-data/selfplay_out --out F:/opus_scratch/<NEW dir>
```
On the PC use the read-only torch venv (`C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe`, Python
3.10.22, numpy 1.26.4); never install into it. Options: `--order` (chronological stems; default sorted stems),
`--min-free-ram-gib 6` (checked before every 500k-row chunk), `--footprint-gib 0.6` (extra free RAM required at
start), `--max-wall-seconds 540`, `--priority idle|background` (default `idle`: the Idle priority class, never raised;
Windows background mode starved the scan on the loaded PC, about 100x slower, so it is opt-in).

Outputs (in the NEW directory only; it may not lie inside any input directory):
- `forge_sol_S16_overlap_summary_20261027.json`: per training shard rows, overlap rows, distinct holdout positions
  hit, label conflicts, rejected 64-bit key collisions, md5; holdout unique positions and duplicates; holdout rows
  whose position is in training; whole-file duplicates; game groups, interleaving tripwire, per-group overlap
  histogram, overlap by fullmove bucket, straddling games at every holdout/training junction; status and guards.
- `forge_sol_S16_removal_list_20261027.csv.gz`: `stem,row,reason,holdout_stem,holdout_row,label_conflict`
  (reasons `holdout_position`, `holdout_game_group`); advisory, nothing is removed.
- `forge_sol_S16_holdout_rows_in_training_bitmap_20261027.npy`: packbits, bit i = holdout global row i (013 first).
- `SHA256SUMS`.

Status `COMPLETED`, `STOPPED_LOW_RAM` or `STOPPED_WALL_BUDGET` (exit 3, partial results kept and labelled), or
`FAILED` (exit 1: text/POS mismatch, a 64-bit key collision inside the holdout, bad input). Matching is exact:
the 64-bit key only finds candidates; every candidate is compared on all 33 identity bytes.

## Sol's filter, v3
`filter_v3/forge_sol_datafilter_v3_20261027.py` = Sol's v2 (`sol_v2/`, unchanged) with 4 Windows fixes found on
the PC (`logs/step2_*`): the per-shard segments cursor is materialized (Python < 3.12 keeps a live statement and the
SQLite file open after `close()`, so the scratch cleanup failed with WinError 32), and three `write_text` calls use
UTF-8 and LF (the cp1252 default could not encode a Unicode stem; CRLF made outputs differ from Linux). Logic,
`DATE` and output names are unchanged. Run it like Sol's v2 (see `sol_v2/forge_sol_S16_README_20261026.md`):
```
sh filter_v3/forge_sol_S16_overlap_runner_v3_20261027.sh owner_config.json
pwsh -NoProfile -File filter_v3/forge_sol_S16_overlap_runner_v3_20261027.ps1 owner_config.json -Python <python>
python -I -B filter_v3/forge_sol_datafilter_v3_20261027.py --diagnostic-mode --train ... --holdout-pos ... \
  --hce-dir ... --out <NEW> --work-dir <existing scratch> [--text-map map.json --ordered-stems ...]
```
Production mode needs owner-authoritative row-aligned game-ID maps; none exist on the PC (the self-play text has no
game IDs), so only diagnostic mode applies here.

## Tests
```
cd filter_v3 && FORGE_PYTHON=<python> FILTER_TEST_TOOL_PATH=$PWD/forge_sol_datafilter_v3_20261027.py \
  <python> -I -B -m unittest discover -s . -p '*tests*.py' -v          # Sol's 21 + 20 tests against v3
<python> -I -B -m unittest discover -s filter_v3 -p test_forge_sol_S16_runner_pwsh_v3.py -v   # pwsh runner
FORGE_S16_TEST_ROOT=<NEW dir> <python with numpy> -I -B test_forge_sol_S16_overlap_scan.py -v  # scanner, 13 tests
<python with numpy> -I -B mutation_check_scan.py <NEW dir>                                     # 14 planted bugs
```
Sol's tests create their temporary folders next to the test files: run them from a scratch copy, and point `TMP`
/`TEMP` at scratch. Cross-validation on real records: `xval_build_fixture.py` then both tools, then
`xval_reconcile.py` (Sol's v3 and the scanner agree row for row).

## Real 013/014 result (2026-10-27, `results/`)
Produced by the committed scanner (sha256 `4bdd2520…`, run 3: 448 s at Idle priority, peak free RAM never below
12 GiB); run 2 with the pre-refactor scanner gave byte-identical removal list and bitmap and equal counts.
| quantity | value |
|---|---|
| holdout 013 + 014 | 16,388,575 rows, 16,387,223 unique positions (1,352 duplicate rows, verified exactly) |
| training (29 shards, the trainer's list) | 231,913,894 rows |
| training rows whose position is in the holdout | **6,069** (0.0026 %), in every shard (3 to 339 per shard) |
| distinct holdout positions found in training / holdout rows affected | 6,009 / 6,010 (0.037 % of the holdout) |
| of the 6,069, label differs (score or result) | 5,042 |
| 64-bit key collisions rejected by the exact check | 0 |
| whole-file duplicates (md5 of 31 files) | none; all 14 md5s recorded at conversion still match |
| inferred holdout game groups | 186,841 (median 83 rows); interleaving tripwire PASS (max 4 boundaries per 100 rows) |
| groups straddling a holdout/training junction (012→013, 014→015) | 0 (both junctions start a new game) |
| groups with at least one position in training | 4,084; all positions in training: 105 (98 one-row groups, 7 opening fragments of 3-14 rows starting at fullmove 5) |
| overlap by holdout fullmove | 1-10: 3,474 rows; 11-20: 365; 21-40: 5; 41-80: 1,878; 81+: 288 |

Reading: the self-play generator already deduplicates (`selfplay_out\forge_seen_hashes.sqlite3`), so the leak is
tiny and concentrated in early opening positions and simple endgames; no complete game is duplicated. Removing the
6,069 listed rows (or not) is the owner's decision; this tool changes nothing. No training-gain or Elo claim.

## Limitations
- Game IDs are inferred (Sol's rule), not authoritative; the text has no game IDs. Interleaving is checked only by
  the tripwire. Boards are compared text-vs-POS on every 997th holdout row (stm, score and result on every row).
- Training-internal duplicates are not counted by the scanner (Sol's filter does that, at SQLite cost).
- The label-conflict count compares each training row with the first holdout row of that position.
