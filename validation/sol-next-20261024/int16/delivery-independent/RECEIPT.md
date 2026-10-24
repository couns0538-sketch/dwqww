# Independent int16 source delivery verification

PASS. Source commit `074102419c90c6b3725cd83c172e1ec22a2d8203`, exact lock `f4911f2709bd5ae7e5fca7aea30aac5d87314a05`.

- Source ZIP SHA256 `f7a145738b36cf4ebb7ec460cf93e480453535084db572b14ffdd0385302d103`, 1,310,139 bytes.
- Cumulative patch SHA256 `0a9be1a59c500619b52f458015ebaedcbdf00235fba6bb5e21d9272ed2553f73`, 236,353 bytes.
- Actual GNU patch dry-run and real application used `--batch --forward --fuzz=0 -p1` against a fresh selected-source f491 export. Both exited 0 with empty stderr; no offsets, fuzz, rejections or reversed hunks.
- All 105 patched source files equal the ZIP and source-commit Git blobs byte-for-byte. All 105 ZIP Unix modes exactly match manifest/Git modes; applied files match Git regular/executable semantics. Host read/write permission bits are subject to archive/patch umask and are recorded separately.
- ZIP has 106 safe unique regular-file members: 105 Git source files plus generated `SOURCE_MANIFEST.json`. CRC and every embedded size/hash/mode entry pass. The generated manifest encodes permission0600 without a file-type bit and has no Git counterpart.
- All 95 tracked build/source inputs are present. Exactly three tracked `__pycache__/*.pyc` generated caches are excluded, listed in RESULT; no real source/CMake input is missing. All quoted local includes and static CMake input references resolve.
- Four legacy source includes plus new `nnue_int16.inc` are present. Network remains `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`.

`RESULT.json` SHA256 `242ca1dde0e86588d28848e9a715bf36f9aabed3ef541d98c6f801b076f948c2` contains all105 comparisons, exact commands, original stdout/stderr paths and actual exits. `patch-dry-run.*` and `patch-apply.*` preserve originals. Read-only Git archive/blob stdout and applied exports remain in sibling `INT16_DELIVERY_WORK`; compact proof is this directory's top-level receipt/JSON/script/text files and the small retained consumer attempts.

No compiler, engine, benchmark, rebuild or Git mutation was performed. Initial consumer-check failures are preserved under `attempt1-validator`, `attempt2-validator`, `attempt3-validator`: generated-manifest file-type handling, Git-mode normalization under restrictive umask, then generated-cache exclusion. Package/source/patch bytes were not changed to obtain PASS.
