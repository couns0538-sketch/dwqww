# Broader PC provenance search — no authentic target mapping found

Following the user's expanded search request, inspected permitted C:/D: user folders, QA/staging/export directories and project metadata using bounded Idle PowerShell operations. This extends the original recovery receipt without changing it. No new training or engine job was launched.

The two metadata passes visited 38 roots, 4,276 directories and 56,246 file metadata entries, retaining 3,714 candidate names. C:/D: Downloads, Desktop and Documents were included. The search also covered Astra handoffs, archive staging, QA directories, D:/grok-pc-data and selected D: project outputs. Exact paths, exclusions and per-root limits are retained in `BROAD_METADATA.json` and `BROAD_METADATA_2.json`; this was not an exhaustive content scan of every PC file.

## The strongest new candidates were inferred IDs

`D:/grok-pc-data/forge_holdout/holdout_game_ids.txt` and its WDL counterpart contain identifiers such as `forge_selfplay_001.txt#7`. Their `stats.json` expressly says the source has no game ID and derives a new ordinal when fullmove decreases, piece count increases, or result changes. `build_forge_holdout.py` lines2–4 and29–32 confirm that rule. These names therefore do not provide authentic original game membership.

`D:/grok-pc-data/sp_chunk_013_013/val_game_ids.txt` is tied to the correct raw013 file by its metadata, but `build_sp_chunk.py` lines53–67 derives game ordinals with the same heuristic. The file contains only the historical validation subset's inferred IDs, not complete original013/014 game provenance. It must not be promoted into the trusted registry. Exact metadata/script/list hashes are recorded in `BROAD_SEARCH_PC.json`.

Pilot directories contain other ID lists and per-worker game metadata. Their statistics identify separately generated pilot populations; no authentic mapping to target001/002/013/014 was found. Their training binary payloads were not opened.

## Archive and download findings

- Downloads contains `forge_sample_10M`, an extracted995MB TAR and a compressed copy. The TAR has exactly shard003 `.pos`, `.pos.info` and `.txt`. Its source-info file explicitly identifies003 and10M records. The Astra handoff likewise identifies GitHub release `data-sample-10m-20261030` as only shard003. This is not the missing target population or a game map.
- Downloads also contains `forge_selfplay.py`; SHA256 `9ff8a48b5185e10cb184486e762f63537b26aebf6b88ffc936dfb287773632f2` matches the previously inspected historical generator. Another identical copy does not restore discarded game boundaries.
- Searched all12 `.list`/`.tsv` files in `forge_archive_pull_staging` for target shard names, game IDs/maps, binpacks and selfplay manifests: no targeted matches. Unrelated engine/book provenance exists but does not identify these selfplay games.
- Inspected the3.72GB uncompressed `box-archive-20261015.tar` by reading512-byte TAR headers and seeking across member payloads. Examined10,730 headers and separately resolved4,546 GNU long-name metadata records. No target game-map match was found. Regular file payloads were not read or extracted. `TAR_HEADER_SEARCH.json` and `TAR_LONG_NAMES.json` retain the inventory and metadata-read evidence.

## Limits and disposition

The metadata walks had explicit caps: the C:/grok-pc walk retained1,767 unvisited queued directories after the first pass's aggregate cap; D:/grok-pc-data and D:/qa_df retained386 and72 after their600-directory caps. Reparse points and dependency/cache trees were skipped. F:, D:/a10, live queue/lock/database files, `.nnue` files and live trainer input payloads remained excluded. No large compressed payload archive was decompressed without an indexed lead.

The first TAR command's terminal summary encountered a PowerShell presentation error when selecting fields from ordered dictionaries. The saved JSON inventory was parsed and inspected afterward; a separate pass resolved GNU long-name metadata. This does not constitute a full archive checksum verification.

No authentic historical row-to-game mapping was recovered. Per the user's latest instruction, unresolved historical repair can be skipped; it must remain labeled BLOCKED rather than treating inferred IDs as proof. The next job should capture authenticated source/game/ply plus durable row emission offsets at generation time, preserve cross-shard game identity, and test the complete train/holdout split before training. This report does not authorize starting that next job.
