Forge reproducibility source supplement

168 selected historical experiment test/build/QA/workload source files, stored as inert .py.txt/.sh.txt/.cpp.txt names. Exact source bodies are preserved; no executable binary, neural-net payload, credential or publication/coordination tool is included. This is separate from the frozen evidence archive.

Extraction format (operate on bytes, not Unicode character offsets):
1. Require the first line FORGE_REPRODUCER_TEXT_BUNDLE_V1 followed by LF.
2. Read one LF-terminated header: FILE <decimal byte count> <SHA256 hex> <basename>.
3. Consume exactly the stated number of bytes as the file body. Do not search for delimiters within that body. Verify its byte count and SHA256 against the header and MANIFEST.json.
4. Require the exact ten-byte separator LF END_FILE LF. Repeat until the header line END_BUNDLE followed by LF, then require EOF.
5. Save only validated basenames (no directory separators, dot-dot or absolute paths) into a new scratch directory. Keep the .txt suffix for inspection; removing it does not authorize execution.

All168 bodies were independently extracted from the on-disk bundle using byte lengths and compared byte-for-byte and by SHA256 with their selected original sources. This verifies preservation, not test correctness.

Historical scripts are NOT universally executable or pass-certified. They retain original absolute paths, source/build/net dependencies, counters, deadlines and earlier checker assumptions. Some scripts generate scratch output or invoke native builds. Review before running; do not run unchanged against valuable files. Build-source patches, compiler versions, settings and original run evidence remain in their corresponding job artifacts. Generator source is not a shipped net or dataset; external inputs still need matching hashes.

Important canonical comparison caveat: forge-dot-job7-common.py has a legacy canon() helper that removes time, nps AND hashfull. It is not the later strict parity criterion. Later independent QA scripts preserve hashfull and PV and remove ONLY time/nps. Use those stricter comparisons when reproducing the later reported parity results.

Selection was bounded to genuine experiment harness/build/QA/workload sources not found verbatim in the locally inspected source copies/build bundles. It is not an exhaustive remote-repository absence claim. No new engine experiment was run to prepare this supplement.
