# R11 authentic-game recovery — BLOCKED / UNPROVEN

Bounded recovery found **no authentic row-to-game mapping** for the R10 Job3 population. No game IDs were assigned. Complete original holdout provenance remains mandatory; the retained-position overlap result from R10 cannot clear this requirement.

The machine-readable companion `RECOVERY.json` records exact small-file hashes, directory inventories, source line references, rejected alternatives, and missing prerequisites. This investigation performed metadata/small-file reads only, not a new scan of all data rows. Population figures below come from the pinned R10 manifests: 999,953 filtered rows, 10,000,000 holdout013 rows, and 6,388,575 holdout014 rows, totaling 17,388,528. Authenticated mappings recovered: 0. Authentic games per side: unknown, not zero.

## Evidence recovered

- Historical package `C:/Users/Administrator/grok-pc/nnue/forge-nnue-tools.tgz`, 50,778 bytes, SHA256 `e79b87a94bce45577f3a2e53b0bcd697b1d0aaf6a6ec514f79006d36beeeea81`. Its exact `forge_selfplay.py` member was streamed into memory and hashed: 28,072 bytes, SHA256 `9ff8a48b5185e10cb184486e762f63537b26aebf6b88ffc936dfb287773632f2`. This matches both the embedded checksum manifest and installed source. The archive contains tools, tests, validation reports and a 916-position example, not the target game records or a generation manifest.
- Historical guard backup `selfplay_guard.py.bak_qa_r8v5_20261029_2015`, SHA256 `26191286231dd248121e2ca5111529ea7dd41431c38091032baf1ec4669dc57c`, names the Python generator, two workers, and the original `selfplay_out` directory. Its command does not supply a seed. It provides a historical program/path connection but no per-game identity or output-offset receipt.
- Historical `logs/selfplay.log`, 608,570 bytes, SHA256 `5a07858df5bb8bdf45de2d3511182cebefb0789d50d0158be9382f2e08b5e181`, contains periodic aggregate game/position counts. Its recorded completions are shards007, 008 and009 (lines2774,5585,8272). No per-game offset map or target013/014 binding was found. Its last-write timestamp is 2026-10-19; it is not evidence of a current running job.
- Original cohort manifest SHA256 `bce36a040c3dad55cb8224c0c256e7d04c8a48663d3f08f758bdd969992d5f73` confirms selected source001 physical rows1..466506 and source002 rows1..533494. It authenticates physical row selection, not game membership. Existing tiny raw `.md5` files were recorded as metadata; their raw datasets were not rehashed by this recovery task.

## Why the generator cannot recover the missing identity

The recovered generator source makes the information loss concrete:

| Source lines | Behavior | Consequence |
|---|---|---|
|122–126|SQLite schema stores position hashes and file name/byte/line totals.|The documented schema has no game index, move list, or row-to-game table. The live database was not opened.|
|231–257|Deduplicates each position and rotates at a line limit inside a game's iterator.|A game may lose arbitrary positions and span output shards. A shard cannot be used as a game ID.|
|377–415|Omits checks, captures, promotions, mate/bounded scores and out-of-range scores.|Adjacent saved FENs need not be consecutive plies. Discontinuities do not authenticate new games.|
|469,482,591–596|Worker-local RNG and whole-game messages exist in memory; the writer receives only FEN, score and result.|Neither worker/game sequence nor source-game boundaries are persisted in output rows.|

The historical archive establishes source-code identity, but it does not establish an exact immutable code/run/input binding for every shard. Even a perfect historical binding to this implementation would not reconstruct identities it did not persist. A monotonic ply run or uniquely legal one-move transition can support a chain hypothesis; neither is an authentic game index. No row ordinals or inferred chain boundaries were promoted into IDs.

## Bounded search coverage

Top-level metadata searches covered the original `selfplay_out`, `exports`, `forge_sp_snap`, `sol_sample`, `sol_sample2`, `data40m`, `box_archive`, `box-archive`, relevant archived PGN conversion directories, original cohort/handoff directories, and the historical generator package/validation directory. Exact inventories are in the JSON receipt.

- `selfplay_out` has raw text shards and small checksums. Its targeted game/manifest/PGN/binpack/offset/provenance filename search found no matching sidecar. Database and lock files were excluded from opening.
- `sol_sample` and `sol_sample2` contain raw shard heads, including partial013. These do not supply complete013/014 or authentic game identities.
- `forge_sp_snap` contains a shard003 text snapshot. `data40m` contains converted train/validation binaries with no discovered row-to-target-game map.
- Archived `data_forgepgn` and `data_forgepgn_wdl` statistics list earlier match PGNs and explicitly report `sp_lines=0`. Those files are not identified as sources of the target selfplay shards. Their binary datasets were not opened; a board coincidence would not establish provenance.
- The 3.72GB `box-archive-20261015.tar` and larger sample compressed files were not scanned. The inspected metadata does not connect them to authentic target game records, and bulk archive scans require separate resource admission. This is a bounded search result, not a claim that no useful evidence exists anywhere.

## Exact dependencies needed to continue

1. An immutable historical PGN/binpack source with documented real game boundaries, or the original per-game emission/offset manifest, covering the target selfplay data.
2. A hash-bound map from every selected source001/source002 row and **every** complete013/014 row to canonical source identity, authenticated original game index and ply. A source index alone is insufficient without the row join.
3. Explicit continuation/alias evidence for games spanning rotating output shards or represented in multiple exports.
4. Historical source/run binding that authenticates the recovered map. The generator package hash, aggregate log counters and FEN-chain hypotheses do not satisfy this by themselves.

The next useful operation is to validate a newly supplied authentic source or map against the frozen original row identities. Repeating the same filename search, scanning partial holdouts, inspecting the live dedup database, or assigning chains synthetic IDs would not resolve the blocker. Complete original holdout qualification remains BLOCKED even if every unresolved training row is excluded.

All writes from this task are under `D:/a11/wt/astra_r11/recovery`. No existing dataset was changed; no F:/a10/network/queue/lock contents were accessed; no live database, GPU, training, or process-control operation was used. No bulk provenance scan, overlap proof, regression PASS, or seal is claimed by this report.
