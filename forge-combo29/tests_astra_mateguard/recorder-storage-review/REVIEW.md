# Storage and successor-accounting review

The three reported accounting edges are corrected in the reviewed VM scripts. This was a read-only source review plus syntax and retained-evidence checks; the recorder was not executed and no engine tests or fault injection were run. No engine source, live state, refs, published evidence, or raw traces were changed. Only the small review artifacts in this directory were created. No reclamation occurred.

## Accounting patch

- `/workspace/work/r4-run/finish-soak-play.mjs:8` now detects both AddressSanitizer:DEADLYSIGNAL and UndefinedBehaviorSanitizer:DEADLYSIGNAL, alongside the prior diagnostic markers. Line 16 still totals findings from all attempts, including incomplete attempts.
- Lines 9 and 12 separate completion from success: a normal process exit 66 with one positive final SUMMARY is completed; exit nonzero and/or sanitizer findings keep it failed. Timeout exits 124/137 and signaled attempts remain excluded from completed workload totals. This addresses the TSan halt_on_error=0 plan.
- Lines 10–11 derive normal games from mates, stalemates, repetitions, fifty, ply_caps, and insufficient, then require normal games + faults == raw games. Lines 13–15 keep faultAbortedGames separate and retain all searches in completed harness runs. The fallback for older rows subtracts their faults from raw games.
- `/workspace/work/r4-run/render-report.mjs:64` renders normal games and distinguishes failed from incomplete. Line 66 explains fault-aborted games, TSan exit 66, and that sanitizer totals count marker occurrences rather than distinct races. Repeated DEADLYSIGNAL lines can therefore yield multiple markers; the report now names that limitation explicitly.

No remaining material flaw was found in these three corrected paths. This is not a general audit of all harness behavior.

Both scripts passed `node --check` with exit 0 and empty stdout/stderr. Source SHA256s and exact syntax-check argv are in [accounting-verification.json](accounting-verification.json). A read-only Node audit independently read the first two real metadata/stdout/stderr sets, verified their raw SHA256s, parsed their single final summaries, recomputed all six termination counters, and compared the counts with recorded state. Results: **132 normal games, 19314 searches, 0 fault-aborted games**; both exits 0, signal null, empty sanitizer stderr. Earlier valid totals are unchanged.

## Retained trace verification

The repeated verification covered all six raw `.engine.log` files; there are no `.debug.log` files in the requested scratch directory. All **87 chunks** have contiguous ordered offsets, matching per-chunk sizes/SHA256s, and correct whole-trace sizes/SHA256s. Every raw byte was compared directly with its chunk. Each chunk was also compared byte-for-byte with its actual Git blob, and each working manifest was compared with its committed blob. Raw sizes and mtimes remained stable across verification.

Pinned evidence commit: `f7d1e3196834b1d89ffbd5acd81887e6a3742ed1`.
Remote observation: `3d74100a27e7d8f37ccceb15b9a81af295f4b231	refs/heads/for-fable-and-opus/astra-r4-mate-alpha-guard`.
`git merge-base --is-ancestor` confirmed the pinned commit remains reachable from that pushed branch tip.

The machine-readable [storage-verification.json](storage-verification.json) contains all six absolute raw paths, absolute manifest paths, manifest Git paths, SHA256s, sizes, chunk counts, pinned commit, timestamps and remote verification. Total duplicate raw bytes: **1402314230 (1.306 GiB)**. No trace contents were copied into this review directory.

Actual retained verification command, exit 0:

`node /workspace/work/r4-storage-review/verify-storage.mjs > /workspace/work/r4-storage-review/storage-verification.json`

[verify-storage.mjs](verify-storage.mjs) is the exact read-only verifier used. It records and checks the remote reference, reads manifests and actual Git blobs, and performs byte comparisons without modifying any input.

## Reclamation plan — not executed

If storage later requires it, allowlist only the six exact source paths in storage-verification.json. Recheck that no writer is active, then rerun the full identity checks immediately before each replacement. First durably write a clearly named `<raw>.PRESERVED_POINTER.json` containing the original path, bytes, SHA256, pinned commit, manifest path, and ordered reconstruction instructions. Only after that pointer is durable may the verified raw duplicate be removed. Use the suffixed pointer path so consumers cannot silently parse a pointer as an engine log.

Keep published chunks/manifests, Git objects, PGNs, summaries, events and all other evidence. Preserve the incomplete-0001 classification. Restore by streaming committed chunks in manifest order to a temporary file, verifying the whole size/SHA256, and then renaming. This can recover about 1.306 GiB without losing evidence; nothing has been reclaimed now.
