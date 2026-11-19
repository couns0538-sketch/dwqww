Lossless compressed-ASCII transport of the authorized Forge TEXT evidence stream

The payload is the original742610270-byte concatenated text stream, not standalone engine binaries, neural nets, books or unrelated files. It is losslessly XZ/LZMA2-compressed (preset1,512MiB dictionary), then standard Base64 ASCII. The compressed representation is61939952 bytes;826 data parts total82586604 ASCII bytes, each at most100000 characters with no line wrapping.

Required files: decode.py.txt, reconstruct.py.txt, index.transport.json and its2 index.part*.txt files; manifest.transport.json and its9 manifest.part*.txt files; all826 data.part*.txt files. Keep these flat in one directory. transport_index.json is an optional local reconstructed convenience copy, not required when split index parts are present. Verify the externally published index SHA/manifest SHA before trusting this transport. Hashes detect corruption, not authenticity against an attacker who replaces both payload and index.

Python3 standard library with lzma support is sufficient. Approximate minimum working RAM512MiB for decompression; allow several GB free disk for temporary decoded stream, regenerated chunks and restored files. Read the decoder before execution. No engine experiments/builds are run.

1. python decode.py.txt TRANSPORT_DIRECTORY --output NEW_CHUNK_DIRECTORY
   Verifies every ASCII part, reconstructed manifest, compressed SHA, entire decoded stream SHA and all1064 archived-file hashes before creating output. Regenerates original hash-named~900KB chunks, manifest.json and original reconstruct.py.txt. Output directory must not exist; no different files are overwritten.
2. python NEW_CHUNK_DIRECTORY/reconstruct.py.txt NEW_CHUNK_DIRECTORY/manifest.json --chunks NEW_CHUNK_DIRECTORY/chunks --output NEW_RESTORED_DIRECTORY
   Restores1064 archived files.1230 already_remote entries must be retrieved separately at manifest.remote_baseline_commit; optional --baseline-repo CHECKOUT verifies/restores them through the original reconstructor. They are not included in this compressed stream.

Original stream SHA256 d8e4aafd1b8b5577e50bb428a3a7bbc86e1327ffe026e1e03d21c5b3ad2a24d3
Compressed SHA256 fc9162c08d87f37c0f130b379d2c34d5f8708c662e293419b8a87a3b2b3abea1
Original manifest SHA256 f0150459924561ab7846d8021f187e5cb497e6bb74c5c1cbbb4b1d5470d49798

Local verification restored all1064 files exactly against frozen stream slices, manifest hashes and all1064 current originals. Six corruption/path-safety cases rejected invalid input and preserved existing output. See VALIDATION.txt. Historical engine/test conclusions remain as reported; transport verification is not new engine validation. No publication completeness is claimed by these local files.

Reuse existing remote manifest transport (recommended): instead of uploading its9 parts and locator again, keep them in sibling evidence_archive_20261119/transport. Pass --manifest-directory ../transport to decode.py.txt (resolve relative to your current working directory). The exact original locator SHA and each part SHA are still checked. Self-contained copies remain supported by omitting this option.
