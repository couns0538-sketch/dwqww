# S17 Leak-free game-group validation split + dedupe manifest (Sol's tool, v2 for Windows)

`gamesplit_v2/forge_sol_S17_gamesplit_v2_20261027.py` builds a validation split **by game group** from ordered
self-play text plus POS (and HCE when present), and a dedupe manifest for the sealed shards. It writes new files only.
v2 = Sol's prepared tool (`sol_v1/`, unchanged) with 5 Windows fixes (all marked `v2`): the per-source segments cursor
is materialized (Python < 3.12 kept the SQLite file open after `close()`: cleanup failed with WinError 32), three
`write_text` calls use UTF-8 and LF, and the config is read as UTF-8. Logic, `DATE`, output names and the pinned
dependencies (`forge_sol_datafilter_v2_20261026.py`, `forge_sol_datafilter_20261025.py`, unchanged, sha256-checked
before import) are unchanged. Keep the three files together.

How it splits (Sol's design): groups come from authoritative row-aligned game IDs (production, the default) or, with
`--diagnostic-mode`, from Sol's conservative ordered-text rule (a new group when the fullmove number decreases, the
piece count increases or the WHITE result changes; no reset at file boundaries, so a game that continues into the
next file stays one group; an interleaving tripwire refuses more than 20 boundaries in 100 rows). Groups are ranked by
SHA256(domain, seed, group id); the first ceil(n x basis points / 10000) groups go to validation. Position dedupe
(board32 + side to move) gives validation priority, then keeps the first record inside each part; it may drop rows
but never moves a group's rows to the other part.

## Usage
```
python -I -B gamesplit_v2/forge_sol_S17_gamesplit_v2_20261027.py --config split_config.json [--diagnostic-mode]
```
Config (paths relative to the config file; see `sol_v1/forge_sol_S17_owner_config_example_20261026.json`):
`sources` = chronological list of `{name, text, pos[, game_ids]}` (the `.hce` must sit beside its `.pos`),
`sealed_pos_dirs` (every `*.pos` below them is audited in the manifest), `seed`, `validation_basis_points`, `out`
(NEW), `work_dir` (existing scratch). Outputs: `forge_sol_S17_{train,validation}_20261026.{pos,hce,txt}`,
`..._row_selection_...jsonl` (every source row: group, split, kept/dropped, reason, position sha256),
`..._duplicate_rows_...jsonl`, `..._shard_dedupe_...jsonl` (per sealed shard: sha256/md5, records, duplicate and
conflicting positions, whole-file duplicates), `..._summary_...json`, `..._output_manifest_...md5`; all read-only.

Independent checks added here (own code, read-only):
```
<python with numpy> -I -B audit_split_leak.py <config> <split out> <NEW dir>   # leak count, round trip, SHA256SUMS
<python with numpy> -I -B audit_planted_leak_check.py <config> <split out> <NEW dir>   # the audit must catch planted leaks
python -I -B real_window_build.py <pos dir> <hce dir> <text dir> <stem> <n> <out dir> <new stem>   # last n real rows
python -I -B real_junctions_check.py      # which real shard junctions continue a game (edge lines only)
```
Sol's tests (`gamesplit_v2/test_forge_sol_S17_gamesplit_v2_20261027.py`: his 14, only the tool filename and one
Windows fixture line changed) create temporary folders beside themselves: run them from a scratch copy with `TMP`/`TEMP`
pointed at scratch: `python -I -B -m unittest discover -s . -p test_forge_sol_S17_gamesplit_v2_20261027.py -v`.

## Real run on the PC (2026-10-27, `results/`)
Real games, read-only: the chronological window `forge_selfplay_010` rows 9,800,000-9,999,999 + all of `011` +
all of `012` (copied to scratch; every copy's md5 equals the PC's conversion-time list). The 010 → 011 junction
continues a real game (the 10M-line file was cut mid-game); 011 → 012 starts a new game. Diagnostic mode (the PC has
no authoritative game IDs), seed 20261026, 1000 basis points, real HCE.

| quantity | value |
|---|---|
| input rows | 2,930,566 (33,467 inferred groups; tripwire max 4 boundaries per 100 rows) |
| validation groups | 3,347 (ceil 10 %) |
| output rows | train 2,635,839 + validation 294,515; dropped 212 (duplicate_train 185, duplicate_validation 27) |
| **leak count** (independent audit) | **0**: 0 groups with kept rows in both parts (recomputed groups = the ledger's partition, 33,467), 0 exact positions in both parts |
| the game crossing 010 → 011 | one group (54 + 12 rows), all in train |
| round trip | every output POS/HCE/text row equals its source row |
| duplicates inside each part | 0 / 0 |
| dedupe manifest (3 sealed shards) | 2,930,354 unique of 2,930,566; 212 duplicate positions, 165 with conflicting labels; 0 whole-file duplicates |
| determinism | real `011` split twice: 11 of 11 output files byte-identical |
| manifest + sha256 | `results/real_split_outputs_SHA256SUMS` (all 11 outputs) and Sol's `forge_sol_S17_output_manifest_20261026.md5` |
| runtime | 479 s at Idle priority (tool), 15 s (audit); outputs 912 MB in `F:\opus_scratch\sol_s17\real_split1` (not committed) |

The split is not training-approved (`training_approved=false`), game IDs are inferred, and the 013/014 holdout is
outside this window (S16 measured the 013/014 overlap of every training shard).

## Limitations
- Sol's SQLite design runs at about 6-8k rows/s on the loaded PC: the whole 248M-row dataset would take hours, so the
  real run used a 2.9M-row window. A global position-dedupe manifest over all 31 shards was not built; S16's scanner
  gives the whole-file md5 manifest of all 31 shards (all distinct) and their 013/014 overlap.
- Authentic game isolation needs owner game IDs; the inferred groups are supersets of games.
