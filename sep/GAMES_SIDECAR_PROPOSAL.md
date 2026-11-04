# Self-play `.games` sidecar proposal (text only)

R14 finish, Job 3 step 7. Nothing in the self-play writer, its launcher, its configuration or any dataset was
changed. This proposal turns Astra's sep/FUTURE_GAME_IDS.md into a concrete file format. It also adds what the R14
scans showed about the dedup key.

## Why

- No row of forge_selfplay_001-039 carries an original game ID (sep/WRITER_EVIDENCE.md). Every separation verdict
  therefore ends at "authentic game IDs UNVERIFIED". The npt-data-holdout-check audit returns UNVERIFIED for every
  row whose game_id is null.
- The writer dedups on a hash of the raw first four FEN fields, in one database shared by every shard
  (WRITER_EVIDENCE.md, writer lines 39-42 and 231-236). It also writes an EP square after every double pawn push
  (EP census in sep/boardstm-probe01/PROBE.json: about 3.6 % of rows carry one, and about 98 % of those allow no
  legal capture). As a result:
  - no raw 4-field key repeats across shards;
  - the same position can still appear twice when the rows differ only in a non-capturable EP square or in
    castling rights.

  That is the 7,610-key board+stm overlap: ep_format_diff 4,070 keys, castling_diff 3,514 keys
  (sep/BOARDSTM_TRIAGE.json).

## File format

One `forge_selfplay_NNN.games` per data file, JSON Lines, one record per game. The record is written only after
the game's rows are durable.

| field | content |
|---|---|
| `game_id` | `<run_id>:<seq>`. `run_id` is a random 128-bit hex value fixed at writer start. `seq` is a per-run counter. Never derived from worker, shard or file numbers. |
| `ranges` | `[{"file": "forge_selfplay_NNN.txt", "first_line": a, "last_line": b, "sha256_of_rows": h}]`. A game that straddles a file rotation has two ranges. A game with no retained row has `[]`. |
| `start_fen`, `moves` | the full six-field start FEN and the UCI mainline. These allow an exact replay from row to ply. |
| `retained_plies` | the ply of every retained row, in row order. |
| `skipped` | `{ply: reason}` for each ply not written: `dedup`, `check`, `capture`, `promotion`, `score_bound`, `opening`. |
| `result` | the final White result, equal to the rows' result field. |
| `producer` | writer and engine sha256, effective configuration hash, seed, opening id, worker id. The worker id is for diagnosis only, never for identity. |

## Write order and recovery

1. Append the game's rows to the data file, flush and fsync.
2. Append the `.games` record, flush and fsync.

On restart, a data range without a `.games` record is reported, never adopted, and IDs are never regenerated. A
`.games` record whose row hash does not match fails the shard seal. Sealing a finished shard writes its row count,
md5 and sha256 together with those of its `.games` file into a run manifest. Imported legacy shards stay marked
`legacy, no game IDs`.

## Dedup key

Dedup on board, side to move, castling rights and the **legal-capture-only** EP field. This is the same key that
opus_ep.py produces. The writer may keep writing the raw EP field in the row; the key decides only what counts as
a repeat. Separately, a holdout policy should drop every train row whose board+side-to-move key occurs in a
holdout shard. The writer cannot decide this per game, so it stays an audit step.

## How the audit uses it

audit_exports.py takes `game_id` per row. With `.games` sidecars, an exporter fills `game_id` from the range that
contains the row's line, and `row_id` from `NNN:line`. An overlap between train and holdout `game_id` sets is
then a FAIL, and an absent sidecar stays UNVERIFIED. Acceptance tests, beyond Astra's list:

- a game straddling the 012/013 seam;
- two identical boards from different games, one with a non-capturable EP square, kept once under the new key;
- a row whose line falls in no range, which must be FAIL, not null;
- a sidecar edited after sealing, which must be FAIL.

This cannot authenticate the existing 001-039 population. It applies only to data written after the writer adopts
it.
