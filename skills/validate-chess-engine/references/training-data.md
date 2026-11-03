# Training-data conversion and native evidence

## Result-aware converter and filter follow-ups

- Freeze the no-flag converter and compare actual train/validation payload hashes
  separately. Cover each existing input route; an unchanged selection count is
  not byte compatibility. Preserve deduplication and shuffle alignment with sidecars.
- When reusing reserved bytes for outcomes, document the mask, result perspective,
  unknown sentinel and explicit format version. Version a perspective change;
  never silently reinterpret old White-relative bytes as side-to-move labels.
  Reject unknown versions and invalid mask/payload pairs. Scores and outcomes may
  have different perspectives; test each explicitly.
- Exercise the real converter and decode its output against a literal independent
  W/D/L-by-turn table, including missing outcomes and color-swapped mirrors.
  Testing only a normalization helper does not establish binary round-trip behavior.
- Run all-off and single-rule filter audits explicitly. A run with enabled rules
  that happen to match zero rows is not evidence of the all-off path. Report
  independent hits, first-drop counts, overlap, coverage and measured timings.
- Missing stored best moves is unavailable capture evidence, not a zero capture
  rate. A separately pinned PGN cohort can measure capture behavior, but label
  that cohort separately and never mix its rates into the original cohort table.
- Bind oracle capabilities to the exact executable digest and matching source
  receipt. A depth-one UCI search is not root qsearch; unsupported static/qsearch
  queries remain blocked under a no-engine-changes scope.
- Recheck output containment and fresh free-space plus next-allocation bounds at
  every write batch. Count retained artifacts and failed partials across old and
  new roots. Follow the user's current root/reserve authorization; do not silently
  reuse obsolete machine exceptions. Keep original sources read-only.
- A refreshed handoff may reuse immutable row/holdout evidence only after digest
  checks. Rebind changed tooling, run current CPU preflights, and publish readiness
  only after verification; historical PASS logs do not qualify changed code.
- Exercise the actual consumer entry point: a separate verifier cannot protect a
  caller that only trusts a readiness flag. Check receipt/holdout bindings, finite
  statistics, fixed recipe parameters and safe output paths at admission. Staged
  manifests may support CPU preflight, never training.
- Inspect seed timing in the installed trainer. Seeding after model construction
  does not make matched recipes start from identical weights; compare actual small
  CPU constructions after pre-seeding, without taking optimizer steps.
- Reject malformed PGN prefixes and contradictory header/movetext results before
  emitting labels. Check raw score types before arithmetic can coerce booleans.
  Hash inputs before and after filtering to detect complete-line truncation that
  would otherwise look like successful EOF; publish only from completed staging.

The R8 reproducible examples live in `astra_r8/datafilter/`: `result_codec.py`,
`audit_stm_roundtrip.py`, `audit_followup.py` and `resource_policy.py`. Recipes and
all correctness claims remain separate from crew-owned strength qualification.

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

## Result-aware normalization and deterministic filtering

Keep original full FEN and provenance before legacy clipping, quiet filtering or
deduplication. Distinguish White-relative stored outcomes from signed STM targets:
White loss/draw/win = -1/0/+1, invert only for Black to move. Unknown outcomes
require an explicit false result mask and null semantic result; never invent draws.
For 32-byte Forge REC, audit byte29 mask and byte30 White 0/1/2 separately from
STM targets. Exclude results from position identity and apply the identical
first-occurrence and shuffle indices to binary records and all sidecars.

Test both turns, all outcomes, unknowns, duplicate positions with different outcomes,
and color/vertical mirror invariance. Feature-index enumeration may change under
mirroring: compare active feature multisets or summed features, not arbitrary order.
Run old/new compatibility on identical inputs and compare train/validation hashes
separately. Pin production helpers and preserve their checkout bytes.

An independent filter must be all-off by default and add no implicit clipping,
deduplication or exclusions. Check captures, promotions and en passant using a
genuine stored best move; absent metadata blocks measurement. Drop explicit mate
labels or producer-defined thresholds before clipping (Forge: abs(score)>=31872).
Derive zero-based ply from original FEN: 2*(fullmove-1)+(Black to move), with an
inclusive limit. Report independent, overlap and ordered first-drop counts,
metadata coverage, and input=retained+first-drops conservation. Test flags through
actual output generation, not predicates alone. Compare record and metadata hashes
across ordered two-worker runs; wall-time fields are not deterministic payloads.

Preflight oracle capability before creating output. UCI depth1 is not root qsearch
or static evaluation. An engine lacking the actual oracle must fail clearly;
fixtures cannot replace a missing production measurement. Reserve the next bounded
write against the complete artifact root before allocation, not after it.

For npt result masking, call installed APIs without copying GPL implementation.
Custom REC is not binpack. Supply original FEN, STM score, actual ply and signed
STM result; retain provenance/masks separately. Clone all eight CPU tensors before
freeing native memory, including failure cleanup. A native dummy outcome is safe
only when an explicit mask forces lambda=1 and the semantic result stays null.
Require lambda [batch,1] on score dtype/device; reject malformed batch metadata and
clear transient state after training/validation/error paths. Verify mixed batches
against the installed scalar loss and exercise actual loader/callback/trainer
construction without training. Bind manifest identity, actual imported file/native
library hashes and deterministic sampler state in checkpoints. Test checkpoint
resume including scheduler timing; reject unsupported devices/processes rather
than silently dispatching elsewhere. Keep full holdout clearance separate from
adapter correctness, and playing strength UNPROVEN until crew-owned gates pass.

## Handoff record

When using a forgiving PGN library for training data, inspect its actual recovery
behavior. A populated game object and empty parser error list do not prove that
every token was understood: garbage and incomplete comments can be ignored.
Reject unsupported variants before emitting ordinary-chess records, bind both
header and movetext outcomes, and reject conflicting repeated semantic headers.
Keep a strict structural preflight original and separate from library move
legality; test ordinary exports, variations, special moves and UTF-8 damage.
Preserve legacy parser behavior on an explicitly compatible no-flag interface.

Recheck the original supplied source path, not only its initially resolved target.
A retargeted input alias can otherwise read different bytes while the original
target still hashes correctly. Cover this with an owned fixture link and preserve
both fixture targets. A byte-compatibility contract includes output names and
statistics/metadata files as well as binary payloads; distinguish original labels
from intentionally clipped encoded labels in round-trip audits.

Validate optional metadata as carefully as labels: reject booleans masquerading
as depth/score integers, blank provenance, invalid game:ply identifiers and result
claims on evaluation-only sources. Preserve valid original raw-label text and
leading-zero source identifiers. After tightening a schema, replay existing real
normalized shards read-only and bind their before/after hashes; unit fixtures
alone do not prove compatibility with retained training data.

A proof checker must reject missing evidence collections, not merely iterate
whatever entries happen to be supplied. Bind required tool identities, ordered
source consumption, retained/excluded conservation and sign/mirror evidence to
the exact payload. If historical proofs need migration, authorize the specific
historical digest and specific local modules; newly published proofs must satisfy
the full current contract. Preserve old receipts instead of editing their pins.
For installed-runtime proof, require the complete approved file set and versions,
not just hashes of the entries supplied by a new manifest. Rehashing a changed
installed DLL does not make it the approved runtime. Keep permitted local changes
explicit and verify their actual current bytes; do not extend that exception to
installed packages or duplicate resolved-path aliases.

Count parsing/validation/serialization in the CPU budget, not only pool workers.
For a two-process budget with a computing coordinator, permit one pool process.
After correcting allocation, remeasure throughput rather than reusing timings
from a larger total process set. If an owned validation job yields its slot,
verify its exact identity/ancestry, resume it reliably and retain elapsed-time
disclosure. Never use this procedure on crew training, gates or unowned jobs.

Profile closed raw sources before assuming a proposed filter removes anything.
Bind producer digests and full-source hashes; keep descriptive audit reservoirs
separate from training inputs. Aggregate correlations from raw moments, not mean
correlations. Require nonnegative variances, the integer covariance bound and
consistent outcome marginals; distinguish genuine zero variance from impossible
statistics. Missing game identifiers and missing oracle metadata remain explicit
limitations regardless of how many source rows were inspected.

Qualify abrupt interruption on an owned fixture child at a real flushed-output
boundary. Preserve the partial directory, prove same-destination refusal, and
compare a fresh retry with an uninterrupted result. Do not call fresh retry
resume. Process cleanup must tolerate a Windows venv launcher exiting after its
worker, and always wait for the exact owned child; never target by process name.
Keep fixture proof distinct from production-corpus interruption qualification.

Before using an audit reservoir for a broad native proof, verify each numbered
original source line, exact six-field FEN, score and outcome against a literal
orientation oracle. Full-source digest checks also bind unselected bytes. A
reservoir whose metadata hashes are self-consistent can still contain wrong
labels; numerical equality alone also accepts Boolean/float impostors. Keep the
reservoir explicitly audit-only and preserve its original source/sample hashes.

For native compatibility checks, reproduce the archived UCI option transcript.
An experiment labelled OFF may leave UseNNUE enabled; do not infer options from
the label. Pin the executable hash and preserve failed probes before correcting
the runner. Perft checks FEN and move-state compatibility, not NNUE evaluation
quality or training/export compatibility.

Bind a native compatibility probe's sample before and after execution, not just
by hashing whatever file exists afterward. Reject empty, invalid or multiline
FEN input before constructing UCI commands. Check original numeric fields before
library normalization: a board parser may repair fullmove0 to1 and then report a
valid board. Preserve the original input identity and failed probe diagnostics.

Apply the same single-line FEN contract at shared data admission, including JSON
and evaluation-only sources. A whitespace-tolerant board parser can accept CR/LF
that breaks a later UCI command. Reproduce the gap through the actual all-off
filter, reject before publication, and retain the original valid FEN unchanged.
Keep explicitly compatible legacy conversion behavior separately qualified.

Python chess parsers may accept a wider notation than the native engine: Unicode
separators/digits, promotion markers, Shredder rights and Python-style integer
text can survive library validation. Reproduce a mismatch with a bounded UCI
probe on the exact executable, including a distinct prior board to expose a
rejected position command. Share the proven text contract between normalization
and native probes; preserve accepted original text instead of silently repairing
it. Refresh source-bound handoffs after any admission change. In regression
fixtures, keep derived ply consistent so an unrelated metadata check cannot
hide the parsing defect.

Basic library board validity may omit necessary promotion inventory: extra
non-pawn pieces require enough absent pawns. Verify the actual engine's behavior
with both impossible fixtures and positive promotion controls, including mixed
piece types and color mirrors. Keep descriptive whole-corpus claims tied to the
validator actually used; a later stricter sample/selected-cohort check does not
retroactively qualify every historical source row.

Describe the exact timing interval: a processing timer may include a final
input rehash while excluding startup and output hashing. Preserve command-level
elapsed time separately, and bind both to their measured source and CPU budget.

Preserve timeout diagnostics before re-raising an owned-child timeout; Python may
return bytes even in text mode. Inventory only closed logs. A packaging process
must exclude its own active stdout log, then pin that final log separately. Keep
the incorrect inventory for provenance and publish a distinct corrected record.

Keep archived execution scripts out of test discovery. A preserved source file
named test_*.py may have top-level process-control or file-writing code. Scope
pytest collection exclusions to the evidence tree, preserve archived bytes, and
verify that broad collection still finds the complete real correctness suite.

Preserve exact identities, commands, observed counts, measured/extrapolated costs,
raw evidence locations, tested platforms and unresolved limitations. After user
steering, check collaborator status: sending a message does not resume an idle or
interrupted agent; trigger a follow-up task while retaining file ownership.
