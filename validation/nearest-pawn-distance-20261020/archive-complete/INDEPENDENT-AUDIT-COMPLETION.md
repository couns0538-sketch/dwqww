# Forge21 independent archive audit — first attempt retained

Status: **FAIL_INDEPENDENT_COMPLETE_21_ARCHIVE_AUDIT**, 13783 checks, one finding; exit1. No retry.

Every frozen original (2045 files,319 directories), all2078 staged and ZIP payloads, split parts, reassembled121548290byte SHA256 and65 root bindings passed. Exact selected scope has no later additions.

The sole finding is the archived ROOT-METADATA-CHECK-NOTE.json390bytes SHA256 e27fb25282520c1be6b426cdf78d9a4204fc07ef81dffaa068a6e992b31a5f81 differs from the current outer375byte note SHA256 837c27849c2ee02e04b3787c115a881ef3a8a9e37bdc48a668bd6ed5df40055a. Only its resolution sentence differs. The current outer mtime is later than archive producer completion; authorship was not independently established. Original failure facts and57/65 counts remain identical. Both exact versions and their diff are preserved separately. The original first audit verdict has not been changed.

Audit receipt SHA256: accfa0b701ebedc9ef135b678c4b5739e6c86f70d560868f50330f6b0ab85b8b. Auditor SHA256: 01b2544448dd26ad7fa7c88efb05a662c2ddcbe13d295f1f50af79bc525e8b67. Preserved qualified20 reference SHA256: 0cfc5947feb941bebeb8d1ea837558ac6886927a927d7ececd07b3ddb97abbc9.

No recovery/extraction/chmod, engine, compiler, network or Git execution occurred. No originals or stage files were modified. ZIP permissions are generic0600; original file/directory permissions and file mtimes were verified against the mode map, live originals and stage. This is not an actual restoration claim.

Root must review the provenance difference before any separate recovery clearance. No engine correctness, speed or Elo acceptance follows from this archive audit.
