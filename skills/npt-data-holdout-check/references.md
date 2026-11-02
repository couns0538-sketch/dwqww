# Independent export audit contract

The helper is a separate Python/SQLite check, not an NPT decoder. Its JSONL exchange format is explicitly an **audit adapter format**. Authoritative readers must export one object per row:

```json
{"row_id":"003:42","fen":"rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1","game_id":"original-global-game-identifier"}
```

`row_id` is an immutable source-record identity retained by conversion, not an output ordinal. `game_id` must be the actual globally comparable original game identity; use JSON null when absent and receive UNVERIFIED. Do not manufacture it. FEN validation checks six-field syntax, board widths and state fields, not full chess legality. The independent positional leak key expands the board and includes side to move, deliberately ignoring rights/clocks for conservative exclusion; full-FEN state is separately compared to the source row exactly after whitespace normalization. Scores/results and native record encoding require the authoritative round-trip test; this helper does not decode or verify those fields.

Inputs are the complete frozen source export, retained training export and two complete 013/014 exports. The source export must include every retained row's original full FEN and real game ID. Audit artifact hashes are independent of the **original** FPOS/binpack hashes: preserve both, plus exporter source/binary and exact command. Trusted export rowcounts/hashes must come from a verified complete export, not a partial file chosen to make the audit pass.

Set the following paths and trusted values from the current crew manifest, all under the permitted D: job area. Run through `grok-pc-safe-run`; this direct Python recipe documents the argv the safety wrapper must invoke:

```powershell
$Python = 'D:\forge-tools\venv\Scripts\python.exe'
$SkillRoot = 'D:\forge-tools\plugins\forge-cpp-lab\skills\npt-data-holdout-check'
# SourceExport, TrainExport, H013, H014, Hash013, Hash014, Rows013, Rows014
# are mandatory values from the frozen export manifest. AuditOut must be NEW.
& $Python (Join-Path $SkillRoot 'scripts\audit_exports.py') `
  --source $SourceExport --train $TrainExport --holdout-013 $H013 --holdout-014 $H014 `
  --sha256-013 $Hash013 --rows-013 $Rows013 --sha256-014 $Hash014 --rows-014 $Rows014 `
  --out $AuditOut --min-free-mib 32768
if ($LASTEXITCODE -ne 0) { throw 'Clearance did not PASS; preserve and inspect the report.' }
```

Every input is bound to descriptor/path identity and a hash of the actual bytes consumed during the scan, with a final recheck; ctime is used only on POSIX to avoid Windows stat/fstat differences. The helper writes only a new owned directory, retains `audit.sqlite`, and publishes `audit.json` after completion. It never edits exports, source shards or live trainer files. Disk preflight estimates four input-byte equivalents plus 16 MiB index overhead and a default 32 GiB reserve; the estimate is not a quota. Free space is checked every 1024 rows. Other writers can consume space, so budget for retained indexes and fail safely. Scratch must have a fresh capacity measurement before the audit. Existing output is refused.

Exit 0: supplied-export checks PASS. Exit 1: demonstrated position/game/provenance failure. Exit 2: unknown IDs, incomplete inputs or a blocked audit. A mid-run failure can leave a partial SQLite index without a completion report; retain it and the actual stderr/stdout/exit log. Missing original-shard or adapter proof stays UNVERIFIED even if the supplied exports pass.

Fixture regression tests are `tests/test_crew_data_holdout.py` in the plugin. They do not certify the real private 013/014 data. The crew must run this independent audit on actual complete exports before training use.

## Frozen selfplay text adapter

`scripts/audit_selfplay.py` directly reads original Forge full-FEN selfplay text
and result-aware JSONL. The manifest has `schema: 1`, purpose `actual-inputs` or
`synthetic-fixture`, source mappings, cohort, filtered data and exactly013/014.
Every file is SHA256 pinned. Source mappings supply the exact original
`record['source']` literal and a physical, one-based inclusive row range. Both
cohort and filtered rows join independently to original raw six-field FENs; cohort
must cover every selected raw source row exactly once. Retained rows must belong
to that cohort. Missing, duplicate or unmapped provenance fails. Castling/EP and
both clocks compare exactly after whitespace normalization. The conservative
holdout position key remains expanded board+STM.

`actual-inputs` also requires the hash-pinned completed frozen-input receipt and
the two original trusted metadata files with complete_scan=true, matching shard,
row count and full SHA256. Both complete holdouts are streamed without writing a
normalized copy. An optional `game_ids` sidecar supplies one JSON object per
physical input line: `{"physical_row":1,"game_id":"real-global-ID"}`. It requires
its own hash, exact row count and stated original provenance; null means unknown.
Known IDs can pass from raw source to derived records through the exact source-row
join. Explicit derived IDs must agree with the original. No inferred boundaries,
shard prefixes or FEN-derived IDs are accepted as evidence.

The adapter imports `fen_state`, `fingerprint`, `identity` and duplicate-key
validation from the existing normalized helper. It hashes actual scan bytes,
checks descriptor/path identity, and independently rehashes all inputs and both
implementation files before completion. Inputs and output must be beneath
D:/a10 without reparses. The output directory must be new. The preflight reserves
2,000,000,000 bytes for retained indexes and reports within the15 GB workspace
cap. Every4096 rows it checks C>=30 GiB, D>=50 GiB and current output size; total
workspace usage is rescanned at most every60 seconds. SQLite uses one thread,
32 MiB cache and in-memory temporary tables. Use the full-protected-roots launcher,
Idle scheduling and one worker. This is a conservative reservation, not a hard OS
filesystem quota; other writers can still force a safely blocked audit.

The report distinguishes source full physical/selected rows, cohort, filtered and
holdout rows; missing IDs per role; cohort and retained full-FEN mismatches;
position/game overlaps; hashes; complete status; and the retained index identity.
`unknown_game_id_rows` counts filtered+holdout rows; source/cohort counts remain
separate. Native inputs with absent IDs finish UNVERIFIED even with zero overlaps
and FEN mismatches. A failed or blocked incomplete report never clears data.
Syntax validation is not full chess legality, and this adapter does not decode
NPT/binpack or prove trainer behavior. Synthetic fixture PASS is scoped only to
the adapter tests. The R10 task-specific reviewed manifest, launcher recipes and
negative fixtures live under `astra_r10/job3/audit/`.
