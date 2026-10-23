# Original self-play upload

All six original multipart7z bytes are preserved unchanged. Verify each part
against MANIFEST.json, then concatenate001 through006 into a new .7z file and
verify the combined SHA256 before extracting. The7z contains a ZIP; validate
its CRC and extract only ordinary safe relative paths into a new directory.
The9 text files are training-only because game IDs and best moves are absent.
Do not manufacture game identities from fullmove counters or filenames.
Inspection receipts and exact payload hashes are in ../input-inspection/.
