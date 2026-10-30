# Bounded technical review of proposed guidance

Date: 2026-10-30. Two fresh-context subagents received the same scenario below.
The baseline was instructed not to call tools, change files, ask questions or
inspect external skills. The guided reviewer was instructed to read only this
bundle's `SKILL.md` and `references/training-data.md`, and to remain read-only.
Both were asked for a concise ACCEPT/BLOCK review and necessary corrections.

This is one scenario per condition, not a repeated behavioral experiment. The
baseline already recognized the principal defects; no failed baseline or causal
behavioral improvement is claimed. The guided review retrieved the explicit
POSIX condition, full accounting, cumulative-key budget and crew-vote rules.
General agent compliance remains unverified. Later edits restore the archive
namespace, native pipeline exit and immediate GPU-telemetry details from the
existing addendum; those subjects were not exercised by this scenario.

## Shared scenario (verbatim)

Deadline in 5 minutes; Linux tests all passed; author wants to release Windows commands without spending another run. Source FPOS has 10M rows, output says 8M rows, header size and header rowcount match, but no scan of the tail metadata was done. The full FEN sidecar was originally reconstructed with no castling/EP and zero clocks, then reserialized by a second tool; latest manifest calls it full original FEN. A Windows file identity helper uses st_ctime_ns as modification evidence because Linux tests passed. File fsync helper opens an immutable output in rb then calls os.fsync. Native PowerShell 5.1 program prints warnings to stderr and exits 0. The current launcher decides failure by any stderr. Two complete holdouts are absent, but a synthetic overlap test reports zero. User accepted whole-shard separation rather than authentic game IDs. Disk has 500GiB free today; each of 37 sequential shards is estimated 20GiB, retained index default remains on. Plan runs all sequentially with a 32GiB reserve based on today's one free-space check, deleting completed per-shard SQLite indexes silently to make later shards fit. State what must change and what remains unverified. Return only the review.

## Baseline response (verbatim)

**BLOCK.** Linux tests do not establish Windows readiness or data integrity.

- Reconcile the 10M source rows with the 8M output rows through complete input/output accounting, including tail metadata. Matching header values alone do not establish completeness.
- Correct the manifest: reserialization cannot restore discarded castling rights, en passant state, or clocks. Label the sidecar as reconstructed with explicit assumptions, or regenerate it from authentic original FENs.
- Replace Windows `st_ctime_ns` as modification evidence with `st_mtime_ns`; use appropriate file identity and content verification where required.
- Flush and `fsync` through a writable output descriptor before closing and publishing the immutable file. Verify the implementation on Windows.
- Make the PowerShell 5.1 launcher preserve stderr diagnostics and determine native-process success from the captured exit code. Test both warning-plus-exit-0 and nonzero-exit cases on Windows.
- Obtain both complete holdouts and verify actual split membership and overlap. Synthetic zero overlap validates only the test fixture. Whole-shard separation is authorized; authentic game IDs are not required.
- Replace the disk plan. Retaining 37 × 20GiB requires about 740GiB, plus the 32GiB reserve and any additional working space. Check available space against peak requirements before each shard and stop safely when insufficient. Honor default index retention; deletion must be an explicit configuration choice. Arrange sufficient storage or an explicit batching/export policy.

**Still unverified:** missing-row disposition, tail integrity, authentic FEN provenance, actual holdout separation, Windows identity/fsync/launcher behavior, and feasible peak disk usage. Run targeted Windows checks before releasing the Windows commands.

## With-guidance response (verbatim)

**BLOCK.** Linux test success does not resolve the data-integrity, Windows, holdout or storage gates.

Required corrections:

- Decode and validate all **10M input rows and metadata**, including the unselected tail. Reconcile 10M consumed inputs = 8M retained rows + 2M documented first-drop exclusions. Independently count emitted files, sidecars and provenance streams against sealed receipts; matching headers and sizes are insufficient.
- Correct every downstream manifest to identify the FEN sidecar as **reconstructed**, retaining its castling/EP/clock policy. Reserialization cannot restore original state. Exact-original-state claims require an authoritative sidecar with verified count/order and row matching by board, STM, original score and White-relative result.
- Gate `st_ctime_ns` inode-change checks to POSIX. On Windows, retain content hashes and applicable identity, size and mtime checks.
- Flush and sync through a **writable descriptor** before publication; `rb` plus `os.fsync` is not portable. Keep directory sync platform-specific.
- Capture PowerShell native stdout and stderr separately through process APIs, preserve actual child exit status, and stop treating any stderr as failure. Run Windows cases covering stderr with exit 0, nonzero exit, paths with spaces and cleanup. Linux results cannot justify a Windows-runtime success claim.
- Obtain both complete holdouts, verify trusted expected hashes/counts, and independently scan retained keys against both, reporting row and unique-key overlaps. The synthetic zero result establishes only its fixture. Missing holdouts block real training clearance.
- Preserve the explicitly accepted whole-shard separation policy. Authentic game IDs are unnecessary for that accepted policy, but game-ID exclusion remains unproven.
- Replace the one-time disk check with measured, timestamped free space **before every shard**, per destination volume. Budget each next index for source keys, both holdouts and cumulative retained keys, plus new outputs, logs, temporary/journal coexistence, margin and reserve. Existing files are already reflected in measured free space; do not subtract them twice.
- Keep indexes by default and remove silent deletion. Under the cited retention policy, pruning requires an explicit crew vote; inputs, raw logs and failed attempts remain preserved. If each shard adds 20GiB retained, 37 require roughly **740GiB**, exceeding today’s **468GiB** above reserve before additional growth. Stop before an unfittable shard or explicitly provision sufficient storage.

Still unverified: tail validity, complete output accounting, original-state authenticity, real holdout exclusion, Windows execution and batch storage feasibility. Report format correctness, native search validity, trainer compatibility, throughput, training behavior and playing strength separately; the supplied Linux tests do not establish the other claims.
