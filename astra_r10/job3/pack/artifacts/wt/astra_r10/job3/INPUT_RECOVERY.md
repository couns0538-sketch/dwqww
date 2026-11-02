# Job3 input recovery — UNPROVEN

Pinned source `d8982bc04d3a828ba440bad250d02fb72526f1a2` was fetched into the
R10-owned clone only and exported to `D:/a10/job3/source`: 194 files,
7,042,470 bytes. `SOURCE_MANIFEST.json` SHA256 is
`963425917e003880d00ba1c399af1e3a38f9a48dfd347d419ccce1f0b0b4aa54`.
The original repository and datasets remain unchanged. Source recovery launcher
receipt is `launch-source01/result.json` (exit 0, Idle, one worker, no capture or
disk-floor errors).

The source snapshot contains `astra_r8/datafilter/` and `tools/`, plus original
root licence/instruction files. Relevant real paths are
`astra_r8/datafilter/convert_forge.py`, `records.py`, `npt_adapter.py`,
`train_adapter.py`, `tools/data/forge_pos.py`, `tools/data/relabel_positions.py`,
and `tools/data2/convert_dataset.py`. The pinned relabeler already contains FEN
sidecar and reconstructed/original-state provenance handling; inspect its actual
contracts before changing anything. The existing test `conftest.py` hard-codes
telemetry outside D:/a10 and must be redirected in the working test copy before
running the suite.

## Available input identities

These identities were first recovered from original crew metadata. The completed
freeze receipt `freeze01/INPUTS.json` records independently hashed
source-before, source-after, and frozen-copy-after SHA256 and MD5 for every row.
`D:/a10/job3/inputs/INPUTS.json` is the same completed receipt. Partial per-file
receipts do not claim the entire freeze completed.

All six completed receipts are HASH_IDENTICAL; the final INPUTS manifest SHA256 is
`4a0b8287c7bf3c1a4666e1f1d723d7b3c15112eac18e1a4e5e8de73e809140af`.
`launch-freeze01/result.json` reports exit 0 with no capture or disk-floor errors.
`freeze01/PROVENANCE_MAP.json` binds exact original `record['source']` strings,
source row boundaries, historical trusted holdout metadata and frozen paths.

| Role | Original D: path suffix | Bytes | SHA256 |
|---|---|---:|---|
| source001 | selfplay_out/forge_selfplay_001.txt | 29,974,655 | de27d81720c0e33f10e0fa95e48b1f619b1325bf35675cd2fcd016fe48f338a2 |
| source002 | selfplay_out/forge_selfplay_002.txt | 201,066,420 | 16f3d241c1080b21bd7d05a3a297ef4ff11b49dea025c6301383815e85cb55b0 |
| holdout013 | selfplay_out/forge_selfplay_013.txt | 650,287,208 | fa383b67aa30b8df79d5989b8fc5a92b5edf615fcfca0f1b46085c47600e17b9 |
| holdout014 | selfplay_out/forge_selfplay_014.txt | 415,563,024 | b2c8ec79a2f24b72d5c1a124a14f64cd46c04221ff405cb4409b755a75abbef0 |
| cohort | dwqww/astra8_data/cohort/million.jsonl | 315,050,752 | a3cc03b258dfe3adbe5e5d84b8c08dec96261d0b9b6fb8c0d9e87b874829ed1e |
| filtered | dwqww/astra8_data/holdout_cleared/records.jsonl | 315,036,094 | 0e73a87c2e1af035aed34f51fdd74daefc05833ce133f254845f09f23aeb5dce |

Original suffixes above are relative to `D:/grok-pc-data/`. Frozen destinations
are `D:/a10/job3/inputs/<role>/<original filename>`. Total copy size is
1,926,978,153 bytes. Preflight reserved 1,936,978,153 bytes, observed existing
D:/a10 usage 1,000,658,348 bytes, C free 167,198,547,968 bytes, D free
74,961,510,400 bytes. No normalized full-holdout duplicates are needed.

Historical complete counts are 013 = 10,000,000; 014 = 6,388,575. Cohort is
1,000,000 rows: raw001 rows 1..466506, then raw002 rows 1..533494. The retained
filtered file has 999,953 rows. Original raw files are required for authoritative
six-field FEN comparison; normalized cohort alone is derived evidence. A 16,384
row validation013 prefix exists but is not a substitute for the complete holdout.

## Original metadata evidence

`discovery01/DISCOVERY.json` SHA256 is
`1e88bb76fcf6963a6623d69940a23c4ec9a494728414979efd123b922f917913`.
It records source/copy mapping and hashes for eight original small JSON files,
current dataset sizes, first-row format observations and related export names.
`launch-discovery01/result.json` records exit 0, Idle, one worker and no capture
or disk-floor errors. Copies live under `discovery01/original-metadata/`.

| Metadata | SHA256 |
|---|---|
| handoff/manifest.json | 0b75136d5d3ead9881b8dc78f0b46ee55d918de499884272c790356f8001d4bb |
| handoff/full_output_hashes.json | df8ae26ee616b3804b5092c93ada09717dfb98caf6880d123e711f035ba81243 |
| holdout_cleared/clearance.json | 35a839f81edfc3a12d5d8b4d9912d9a46992072cf2caa21fdfd1de51faef4a68 |
| holdout_cleared/selection.json | aebc12465488f4006f74d5354e1e68a7319458b79c7b14f096542081902830d3 |
| cohort/manifest.json | bce36a040c3dad55cb8224c0c256e7d04c8a48663d3f08f758bdd969992d5f73 |
| independent_audit/holdout013.json | d050e56ab1fd6c3cd2c9c3484e0bc87011a170c5c88a248ac3140884b12214fc |
| independent_audit/holdout014.json | 0fa08ee04b60874a27afeadd99d21303538f2dee44b604df7aed14ca52e86b40 |

## Limits and next audit

The inspected raw format is `six-field FEN | score | result`; the filtered JSONL
has full FEN, source path and source row, but no authentic game-ID field. The
original MIX_SPEC explicitly says genuine game identifiers were unavailable.
The bounded export-directory discovery found matching `.md5` files and no
game-ID/FEN-sidecar/manifest named files. This is evidence of missing provenance,
not proof that another trusted source cannot exist. Report actual missing-ID
counts from the complete scan and keep game separation UNVERIFIED. Never invent
IDs from FEN, row number, shard name or inferred game boundaries.

Historical clearance removed 47 board+STM overlaps (24 from013 and23 from014).
The new audit must independently recompute overlap and compare retained FENs to
original raw rows, including noncapturable EP fields. Previous `training_ready`
metadata has older requirements and does not establish current clearance.

No F: paths embedded in original metadata were followed. No Opus folders, live
trainer inputs, queues, GPU jobs or training were accessed. Full input hashes
establish input identity only; all data-quality and tool claims remain UNPROVEN
until the requested audits and adapter proofs complete.
