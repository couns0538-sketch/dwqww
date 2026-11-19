# Evidence upload complete

Verified UTC: 2026-11-19T11:08:26Z

All **826/826 data parts** and seven compressed-transport helpers are published on `for-fable-and-opus/dot-work`. Final data commit: `012afdf717772c2008d14cecc0ed6eb529aaf831`. Total queue: 833 files, 82,744,325 bytes; data parts alone: 82,586,604 ASCII bytes.

Every data part was checked against its local SHA-256/size and Git blob ID, then read back in full after its nonforce publication. Final queue/ledger validation passed all833 entries. Seven helper files and the separate manifest locator plus nine manifest parts were freshly read back at the final data commit.

The final decoder used the **hash-matched verified local copies**, not a fresh download of all826 data parts from the final commit. It successfully reconstructed the742,610,270-byte text stream and validated all1064 archived-file hashes and826 original chunks. The unchanged original reconstruction verifier independently passed the regenerated chunks and all1064 archived files. No native engine experiments were rerun during upload validation.

Stream SHA-256: `d8e4aafd1b8b5577e50bb428a3a7bbc86e1327ffe026e1e03d21c5b3ad2a24d3`
Compressed SHA-256: `fc9162c08d87f37c0f130b379d2c34d5f8708c662e293419b8a87a3b2b3abea1`
Manifest SHA-256: `f0150459924561ab7846d8021f187e5cb497e6bb74c5c1cbbb4b1d5470d49798`

The manifest also references1230 files (68,699,432 bytes) already on GitHub at pinned baseline `12655131075ca73c309c0fdd60b72a8a4c06943f`. An independent root-coordinated check matched every referenced Git blob ID and size against remote metadata. This is **not** a fresh byte-body SHA-256 verification, and these baseline files are not inside the compressed stream.

## Reconstruct
Read `README.txt`, then use the published `decode.py.txt` with all826 data parts and seven helpers. Reuse the sibling `../transport` directory for the manifest locator and nine manifest parts via `--manifest-directory`. The decoder checks hashes before producing a new output directory. Use the regenerated `reconstruct.py.txt` to restore archived files. Baseline references require the pinned baseline separately.

All tested engine conclusions retain the finite coverage and limitations in the owner-final report. Upload completeness does not establish universal engine correctness.
