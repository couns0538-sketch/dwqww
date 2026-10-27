# S40 cross-folder datagen dedupe + merge tool

`forge_sol_S40_merge_datagen_20261027.py` takes a **second** self-play output folder (ordered text
`FEN | STM score | WHITE result`, as written by the PC's `forge_selfplay.py`), removes every row that would duplicate
the **main** training shards or leak the **013/014 holdout**, and writes NEW sealed shards in the trainer's exact
record format: FPOS v1 `.pos` (the `tools/fen2bin.cpp` layout), FHCE v1 `.hce` (the `tools/hce_dump.cpp` layout) and
the kept text lines, plus an md5 manifest. Existing files are never changed.

## Rules (one reason per second-folder row, first match wins)
| reason | meaning |
|---|---|
| `holdout_position` | the position occurs in a holdout shard |
| `holdout_game` | the row's game contains a `holdout_position` row, or its game ID is in the holdout ID list |
| `main_game` | the row's game ID is in the main ID list |
| `dup_main` | the position occurs in a main shard |
| `dup_second` | the position occurs in an earlier surviving row of the second folder (the first survivor is kept) |
| `kept` | written to the output |

- **Position identity** = board32 + side to move: what the v3b trainer sees (FPOS stores no castling, e.p. or clocks).
  So a castling-only or e.p.-only variant of a main position is a duplicate; a side-to-move flip is not. A 64-bit key
  finds candidates, and every candidate is confirmed on all 33 identity bytes.
- **Games** (the self-play text has no game IDs): by default Sol's conservative ordered-text rule (a new game when the
  fullmove number decreases, the piece count increases or the WHITE result changes). Groups do not reset at file
  boundaries (the generator splits files mid-game). More than 20 boundaries in a rolling 100-row window means
  interleaved text: the run fails closed. An inferred group's game ID is a content fingerprint (sha256/128 of its
  rows). With authoritative IDs, pass `--game-id-sidecars` (`<text name>.gameid`, one ID per line, row-aligned).
- **Reference game-ID lists** (`--main-game-ids`, `--holdout-game-ids`, one ID per line) are optional.
  `gameids --text ... --out LIST` makes a fingerprint list from reference text. Fingerprint lists only catch
  identical games, and the position rules already remove those rows. They matter with authoritative IDs.
- `--holdout-game-rule off` keeps the rest of a game that touched the holdout. The default `drop-group` drops it.

## Usage
```
nice -n 19 <venv python> -I -B forge_sol_S40_merge_datagen_20261027.py merge \
  --second <second folder or its forge_selfplay_NNN.txt files, chronological> \
  [--include-part [--seen-db <COPY of forge_seen_hashes.sqlite3 (+ -wal), outside the second folder>]] \
  --main <main .pos (or .txt) shards> --holdout <013.pos> <014.pos> \
  (--hce-dump <hce_dump.exe> | --second-hce-dir <dir> | --no-hce) \
  --out <NEW dir> [--prefix forge_s40_merged] [--rows-per-file 10000000] [--min-free-ram-gib 6]
<venv python> -I -B forge_sol_S40_merge_datagen_20261027.py verify <out dir>
```
- A `.part` is read only with `--include-part`. With `--seen-db` (a copy of the generator DB) the tool reads exactly
  the committed bytes and lines from the DB's `files` table. Without it, it reads complete lines only and marks the
  committed offset UNVERIFIED. The live generator DB is never opened: the tool refuses a `--seen-db` inside the
  second folder.
- HCE for the new shards: `--hce-dump` runs the PC's `hce_dump` (same build as the main data, sha256 recorded) on each
  new text shard, at Idle, with relative names, so the output is deterministic. `--second-hce-dir` takes the rows
  from existing row-aligned `.hce` files of sealed second files. `--no-hce` writes no `.hce` (counting only; v3b
  cannot load such output).
- Outputs (all exclusive-create, in the NEW directory): `<prefix>_NNN.{txt,pos,pos.info,hce,hce.info}`,
  `forge_sol_S40_row_ledger_20261027.csv.gz` (every second row: group, game ID, reason, first match, label
  conflict, output file/row), `forge_sol_S40_summary_20261027.json` (deterministic counts),
  `forge_sol_S40_manifest_20261027.md5` (written last: **the seal**), `run_info.json` (paths, timings) and
  `SHA256SUMS`. A failed or stopped run leaves `STOPPED.txt` and no manifest. Use only a directory that `verify`
  passes.
- Safety: inputs are opened read-only. The output directory must be new or empty, and may not lie inside or contain
  an input directory, or lie inside `D:\grok-pc-data\forge_push`, `D:\grok-pc-data\selfplay_out`,
  `F:\forge_nnue_train` or `C:\Users\Administrator\grok-pc` (`--protected` adds more). Free RAM is checked before
  every step and every 500k-row chunk (exit 3 below the floor). Idle priority; single thread; nothing is deleted.
- Exit codes: 0 completed, 1 failed (bad input, mismatch, interleaving), 2 usage, 3 stopped by a guard.

## Tests and checks (the PC's read-only NNUE venv: Python 3.10.22, numpy 1.26.4, python-chess 1.11.2, torch 2.4.1+cpu)
```
export FORGE_S40_TMP=<scratch dir> FORGE_S40_FEN2BIN=<fen2bin.exe> FORGE_S40_HCE_DUMP=<hce_dump.exe> \
       FORGE_S40_V3B=<renamed v3b trainer copy>        # the last three are optional (tests skip without them)
<python> -I -B test_forge_sol_S40_merge_datagen_20261027.py          # 15 tests on a private copy of the fixture
<python> -I -B mutation_check_s40.py <scratch dir>                     # control + 22 planted bugs, all must be caught
<python> -I -B v3b_cpu_smoke_s40.py --trainer <copy> --merged <out> --holdout-pos <a.pos> <b.pos> \
         --holdout-hce-dir <dir> --work <NEW dir>                      # v3b trains on the output (RAM + mmap)
```
- Fixture: `fixture/forge_sol_S40_fixture_20261027.tar.gz`, built by `make_fixture_s40.py` and packed by
  `pack_fixture_s40.py`. It holds 5 main shards (001-003 training, 004-005 holdout, like 013/014), 3 second-folder
  files (two sealed, one `.part` with an unterminated tail written by a restarted generator), a generator-style DB
  copy, explicit-ID sidecars and an interleaved file. It is converted with the PC's own fen2bin/hce_dump. Planted
  cases (`fixture_truth.json`): a copy of a training game, a prefix of a training game, a copy of a holdout game, a
  game that transposes into a holdout game after the 001→002 file junction, a game touching the holdout in exactly one
  row, an identical-score holdout replay, a castling-only variant (duplicate), a side-to-move flip (kept) and
  repeats in the `.part` (`dup_second`).
- The expected reasons come from an independent brute-force reference in the test (python-chess FEN parsing, Python
  sets, the group rule re-implemented). The tool's parser and numpy matching are not reused.
- The v3b checks use a byte-identical copy of the trainer, renamed `opus_nnue_smoke_v3b_s40.py` so the NNUE
  supervisor (which adopts `train_resid*.py` command lines) never sees it. They pass no `--guard-tag`.

## Real-data run (the PC, read-only)
`real_stage_inputs_s40.py` copies the second folder's files to scratch with read-only opens, hashing the sources before
and after. The merge then reads the 29 training shards and 013/014 in place, read-only. See REPORT.md for the numbers.

## Limitations
- Game groups are inferred (no authoritative game IDs on the PC); groups are supersets of games.
- A reference game-ID list built from fingerprints matches only identical game records. The generator's per-folder
  dedupe can drop rows from a game, which changes its fingerprint; position dedupe still removes those rows.
- The whole second folder is held in RAM (about 80 B/row plus the parse), and the references are streamed. A
  300k-row folder needs well under 1 GB.
