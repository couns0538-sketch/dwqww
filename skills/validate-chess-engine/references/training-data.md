# Training-data conversion and native evidence

Use a source-grounded validation record before accepting converted labels or a
shard pipeline. Keep format correctness, native search validity, trainer
compatibility, measured throughput, training behavior and playing strength as
separate conclusions. A unit fixture or lower loss establishes no Elo gain.

## Required validation record

| Field | Required evidence |
| --- | --- |
| Identity and representation | Source/producer/trainer revisions, source and executable hashes, exact row counts and sizes, byte layout, score orientation, result orientation and output format. FPOS v1 is columnar: header, packed boards, STM scores, metadata; results are White-relative. FHCE values are STM-relative. |
| Full validation scope | Decode every claimed input row and all metadata, including a suffix beyond the selected conversion slice. Validate piece nibbles, kings, STM/result encoding, reserved bits and format-specific ranges. Header/size checks alone establish neither legal metadata nor complete alignment. Report any unscanned region as unverified. |
| State provenance | FPOS omits castling, en passant, clocks, game IDs and best moves. Exact-state labels require an authoritative full-state sidecar. Match every row by board, STM, original score and White result with identical count/order. Standard 32-byte bulletformat also needs its verified full-FEN sidecar for exact state. |
| Derived state | Record reconstructed castling/EP/clock policy in every downstream manifest. Reserializing or relabeling a reconstructed FEN does not make it original. Require explicit origin when consuming FEN-only sidecars, and exclude reconstruction from exact-original-state claims. |
| Output accounting | Reconcile consumed inputs = retained rows + first-drop exclusions. Independently count every emitted format, sidecar and provenance stream against sealed chunk receipts and totals. Check zero-output and resumed runs too. Counters and header claims alone do not prove bytes on disk. |
| Holdout scope | Bind both complete holdouts to trusted expected hashes and row counts; independently scan retained keys against both. Report row and unique-key overlap counts. Synthetic or prefix checks qualify only that scope. Missing complete holdouts block real training clearance. |
| Split policy | Record explicitly accepted whole-shard exclusion when that is the user's policy. Missing authentic game IDs limits a game-ID claim; it does not invalidate an accepted whole-shard policy. Position overlap zero does not establish game exclusion. |
| Native process evidence | Preserve original requests/responses, IDs, operations, counts, bounded outputs, stderr, command and actual child exit status. A shell pipeline's final status need not be the child's status. Successful queries followed by nonzero shutdown do not certify a successful run. Terminate only owned processes. |
| Search completion | Require a completed iteration for an accepted score/bestmove. UCI cp0 placeholders, aborted iteration depths and partial bestmoves are not completed labels. Record insufficient teacher budget as an exclusion; never invent a score. |
| Publication and seals | Write new outputs; retain original inputs, failed partials and raw evidence. Publish only after validation and clean owned-worker exit. Serialize manifests before final publication. Keep audit/console receipts outside sealed folders. Re-read archived payloads and verify final published size/digest; a successful push or started upload job does not prove artifact publication. |
| Portable archives | Check one case-insensitive namespace spanning files, explicit directories, implied parents and the built-in manifest. File-only checks miss Windows file/directory aliases. |
| Complete dependency notices | Read full notices and the compiled include/dependency closure, including embedded third-party attribution. Record effective combined-tool licensing. Keep optional incompatible tooling external and off by default with explicit opt-in. |
| Resources | Report actual OS CPU time for the measured process scope separately from wall time; cores multiplied by elapsed time is allocated capacity. Record threads/hash/nodes/affinity and successful row counts. Respect established CPU/GPU reservations. Verify the GPU-free scheduled slot after compilation, immediately before GPU execution; unknown process/GPU telemetry is a refusal. |

## Windows portability

- Flush and sync writes through a **writable** descriptor before publication;
  opening a completed file as `rb` and calling `os.fsync` is not portable to
  Windows. For an existing owned file, use an appropriate writable descriptor
  without modifying its bytes; keep directory-sync behavior platform-specific.
- Use `st_ctime_ns` as inode-change evidence only on POSIX. Windows ctime has
  historically meant creation time and is not equivalent. Preserve content
  hashes and the applicable file identity/size/mtime checks; gate a POSIX
  change-time assertion on the platform rather than weakening its Linux test.
- PowerShell 5.1 can represent native stderr as an error record even for exit
  zero. Capture stdout/stderr separately through process APIs and preserve the
  native exit code. Test stderr plus exit zero, a genuine nonzero exit, paths
  with spaces and process cleanup. Set Idle/affinity before useful work starts.
- Linux tests or static inspection do not establish Windows runtime success.
  Report the actual tested OS and leave Windows execution unverified until run.

## Retained indexes and sequential shard budgets

Before **each** shard, measure free space on every destination volume and record
the observed values/time. Budget the next index for the current source keys,
both holdouts, and **all cumulative prior retained keys**. Add its new output
files, probe logs, journal/temporary coexistence, growth margin and the reserve.
Record measured bytes per key/row separately from conservative estimates.

Every previously kept SQLite index and output remains allocated. A batch boundary
does not reclaim disk. Actual free-space measurements already reflect existing
files; subtract only new allocations when checking the next shard. A forecast
from an earlier measurement must accumulate every planned retained allocation.
Use actual per-shard counts and sizes rather than assuming equal shard sizes.
Keep indexes by default. If the next shard cannot fit, stop before starting it.
A plan for explicitly provisioned separate volumes must account for each volume separately.
Neither a planner nor a verification step authorizes moving or deleting data.
For the Forge crew's retention policy, pruning requires the explicit crew vote;
do not insert `--prune-indexes` as a routine runbook step. Preserve inputs, raw
logs and failed attempts regardless of any later index-pruning authorization.

## Handoff

Preserve exact identities, commands, observed counts, measured/extrapolated costs,
raw evidence locations, tested platforms and unresolved limitations. After user
steering, check collaborator status: sending a message does not resume an idle or
interrupted agent; trigger a follow-up task while retaining file ownership.
