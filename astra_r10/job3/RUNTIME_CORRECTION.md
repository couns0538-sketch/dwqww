# Runtime identity correction — UNPROVEN

The original `RUNTIME_INPUTS.json` is preserved unchanged, SHA256
`659ca6fbe6abd4337f06eb7841cd8b065c0fc6dc558e3ca7bc47c161c13daa90`.
Its `files` property is a string, not the intended per-file array. A typed
`$Manifest` collision in the dot-sourced PowerShell launcher lost that array.
The original copy script checked source/copy hashes and exited 0, but the missing
historical per-file list cannot be reconstructed by a later hash pass.

The separately authorized current-D pass read all 20,045 files under
`D:/a10/job3/runtime`, totaling 1,326,486,174 bytes. Each SHA256 was computed with
descriptor/path identity checks; the complete file-name/identity inventory was
rechecked afterward. No runtime file was changed and no original protected
runtime source was opened. This establishes current copied-file identities only.

New receipt: `RUNTIME_CURRENT_HASHES.json`, 11,015,923 bytes, SHA256
`c20358958646d3ccf6372fda39548c9c9840626f8dfd93fcc531219d2d16bba6`.
It explicitly preserves the original malformed receipt identity and the limits
above. Package it as an ordinary artifact/hash reference; its size exceeds the
sealer's 8 MiB JSON-report parser limit. Do not reinterpret it as historical
source/copy proof or copy the 1.326 GB runtime into the small handover pack.

Admission observations were separately inspected: CPU3 11.9% then 14.6%, host
mean 80.725% then 81.98125%, over two 3-second samples. The launcher completed at
2026-11-02T08:16:31.3202621Z, exit 0, Idle on CPU3, one worker, without capture
errors or disk-floor breach. Originals are retained in
`packaging/sealer-tests-loadruntime01-launch/` and `launch-runtime-current/`.
