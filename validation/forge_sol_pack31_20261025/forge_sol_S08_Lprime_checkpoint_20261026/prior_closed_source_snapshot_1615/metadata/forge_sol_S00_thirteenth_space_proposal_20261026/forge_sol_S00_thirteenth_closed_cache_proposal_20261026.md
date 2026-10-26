# S00 external compiler-cache recovery proposal — 2026-10-26

Read-only proposal. All original cache paths remain present. No archive or retirement was executed.

- **80 inode groups / 175 aliases:** 7 static core libraries and 73 ELF ET_REL compiler objects.
- Unique raw payload: **230,945,904 bytes**.
- Gzip6 lengths measured in memory: **50,330,161 bytes**.
- Projected net payload savings: **180,615,743 bytes (172.25 MiB)**.
- Largest one archive: **1,571,295 bytes**; sequential preservation fits the current budget.
- Free snapshot: **88,272,896 bytes**. Projected free after all selected groups and pending 6 MiB packet archives: **262,627,328 bytes (250.46 MiB)**, before map/journal overhead.
- The first **62** sorted groups alone reach **158,316,100 bytes (150.98 MiB)** net; all 80 provide reserve.

`forge_sol_S00_thirteenth_closed_cache_proposal_20261026.json` contains every selected alias, original per-path metadata, current inode/link/size/mtime, measured gzip length, raw SHA256, complete producer array schemas and directory/source mapping, and fresh CMake/source bindings. It excludes all actual repository paths, nested repository evidence aliases, source/data/raw files, and final main/test/helper executables. Forge main/test compiler `.o` files are caches; the corresponding executables are retained. Unknown, incomplete, missing-provenance and source-path gaps are recorded as skipped groups.

All 175 aliases were rechecked after measurement. A complete external metadata walk inspected 95,508 paths, without following symlinks, and reported zero scan errors. A bounded 1,543,176-byte memory-only control reproduced the measured gzip size and exact Python/GNU decoder roundtrip. The audit script contains no retirement, filesystem replacement, subprocess or decompression calls. A separate review receipt records the checks and a corrected observer-only AST false positive.

Process visibility is limited: the snapshot had no live engine/compiler-name matches and no visible candidate reference hits, but 105 FD directories, 266 links and 8 maps were inaccessible. The two named compiler/build processes were zombies. This supports a historical closed-cache proposal, not a global FD-absence claim. Root must repeat ownership/lease/reference checks immediately before retirement and skip changed, unknown or active groups.

After root review, reuse the existing seventh/twelfth hardlink workflow in a **new** directory: deterministic gzip6, fsync, exact SHA/byte-count verification through Python and independent GNU decoders, fsync archive directory, durable full alias metadata map and journal, then retire every alias with exact decreasing-nlink assertions. Preserve the proposal's pre-read atime snapshots when recording original metadata. No change to an existing map/archive or any repository byte is proposed.

Proposal SHA256: `09066c23271aec284d702dcec37509a1922cd11ae097003d8b35c08380a58438`.

Review receipt: `forge_sol_S00_thirteenth_proposal_review_20261026.json`.
