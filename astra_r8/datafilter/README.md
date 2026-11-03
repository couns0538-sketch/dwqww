# Astra R8 Job 2: result-aware data tools — UNPROVEN

This directory contains an isolated converter extension, a deterministic opt-in
filter, and a bounded Python adapter to the installed npt recipe. The production
converter, engine and installed npt files are unchanged. No training, GPU work,
net export or strength gate has run. Engine NNUE owns training; Engine QA owns
FD3A5190 UHO, separate 8moves_v3 and WAC300 qualification.

Current candidate also validates original PGN FEN headers before library
normalization and rejects SetUp=1 without an initial position. The complete CPU
suite passes **564 tests and 11 subtests** in 532.82 seconds. Collection proves
that running the larger checkpoint tests last omitted no cases. Fresh verification
passes all 999,953 selected rows, both CPU recipe preflights and strict v9 checks.
The earlier 100k legacy, 1,000 binary result/mirror and repeat-filter proofs retain
their original identities; exact source comparison confines this repair to the
PGN header method. See [source lineage](evidence/extension5h/verified_v9/pgn_fix_validation_v1/source_lineage.json).
Current manifest: `C:/astra8_data/extension5h_20261103/handoff_v9/manifest.json`,
SHA256 `c43e2498ec6256035d64e39f64093692b77239b585ed87eb5a74ba9361056291`.
Current code must not be paired with historical v7/v8 manifests. v7 is protected evidence and remains
unchanged at SHA256 52f39e0ceeb6fc6c63422514296b928b308ede862754e8d69addde1aa44fc720.
The final review is active from 08:25 through at least 09:25 UTC. See [results](RESULTS.md),
[review log](REVIEW_LOG.md), [recipe commands](MIX_SPEC.md), and
[R12 continuation constraints](R12_HANDOFF.md).

Both recipes retain the same 999,953 rows after explicit exclusion of 47
board+STM matches against the complete 013/014 holdouts. The 10,000-row sample
is 3,139,111 bytes, SHA256
`c7394f11aebf2e76a2e5a1b8e834c8b5b92676180f5896e8ac30062472f7462c`.
Fresh v9 selected-cohort Pearson correlation is 0.6635950368 with 1,000
passing mirrors. The bounded 152.5M-position
epoch recipe repeats this cohort, as disclosed in MIX_SPEC.md.

The cleared `records.jsonl` and `metadata.jsonl` are intentionally byte-identical:
each contains complete normalized records, 999,953 rows and 315,036,094 bytes.
Fresh byte comparison and full hashes PASS. SHA256:
`0e73a87c2e1af035aed34f51fdd74daefc05833ce133f254845f09f23aeb5dce`;
MD5: `aa3e9272d686356ef6a9e25003c52546`. Binary REC files and their JSONL sidecars
have different formats and are not byte-identical.

The strict [complete admission union](evidence/extension5h/closed_0728/admission_union_v1/SUMMARY.json)
passes all 304,999,573 rows in 37 original closed training shards, with zero
rejections. It retains the audited records.py SHA256 a8ef0f43...7360be; the later
Lichess and PGN repairs are separately attributed. The separate
[numeric census](evidence/extension5h/native_counter_closed/CLOSURE.json) also
passes all 304,999,573 rows for score and counter representation in 1,235.139s.
Maximum halfmove is 99, fullmove 150 and zero-based ply 299; scores are -3000..3000.
Neither audit executes native batches or grants game-ID/full-corpus holdout
clearance. Only the selected cohort has holdout clearance.
The [historical descriptive profile](evidence/quality6h/corpus_report/DATA_PROFILE.md)
reports aggregate score/result correlation 0.6567069235 and 93.6105% retained
at optional ply <=160. Its original validator attribution is retained.

A new bounded admission pilot can be reproduced with:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
F:/nnue_pytorch/venv/Scripts/python.exe astra_r8/datafilter/audit_forge_admission.py C:/astra8_data/NEW_admission_pilot --reference-profiles C:/astra8_data/quality6h_20261102/corpus_profile/SUMMARY.json C:/astra8_data/quality6h_20261102/corpus_profile_rest/SUMMARY.json --max-sources 1
```

A bounded or partitioned receipt cannot claim complete reference coverage;
`seal_admission.py` verifies the disjoint complete union and its original hashes.
Completed scans used two total CPU slots at BelowNormal. Keep D: >=50 GB,
C: >50 GB and aggregate task artifacts <=15 GB. Preserve all existing data.

Fresh [exact-lock UCI checks](evidence/extension5h/closed_0728/lock_correction_v1/REPORT.json)
match the five corrected bench pins plus startpos and Kiwipete perft5. Earlier
9,486 perft2 vectors and a separate 5,484-vector generated check retain their
original source identities. Perft establishes move/state compatibility, not
NNUE evaluation quality or playing strength. True static/root-qsearch filtering
remains blocked by the lock's UCI interface; no depth-one proxy is substituted.
Raw four-field Lichess exports also remain blocked because their counters are
unknown. Both recipes contain zero Lichess rows. See the focused
[Lichess](LICHESS_INPUT_REVIEW.md) and [native-input](NATIVE_INPUT_REVIEW.md) reviews.

## Interfaces

`convert_forge.py OUT --selfplay INPUT --keep-result` writes the established
32-byte REC format plus aligned train/val JSONL metadata. Byte 29 is `has_result`;
byte 30 is **side-to-move** loss/draw/win = 0/1/2; byte 31 is version 1.
Unknown outcomes have mask 0, payload 0 and semantic null. The historical
version-0 result bytes are White-relative; `result_codec.py` decodes both versions
and rejects unsupported versions or invalid masks/payloads. No existing binary
is rewritten. Scores remain White-relative in REC and STM-relative in JSONL.
Without `--keep-result`, legacy filters, first-occurrence deduplication,
shuffle and binary bytes are preserved. New `--pgn`, `--lichess` and `--normalized`
routes retain source/full-state metadata with `--keep-result`. Output directories
must not exist. REC is **not npt binpack**.

Result-aware PGN input is strict standard chess: conflicting semantic headers,
missing termination, damaged comments/variations, ignored garbage and invalid
UTF-8 fail before final publication. `--keep-result` also rejects malformed
self-play rows and invalid converter settings, and binds complete source hashes
before/after conversion. Legacy no-flag parsing and argument behavior is retained.
The metadata sidecar preserves the original score; REC keeps the established
`--clip` behavior. The audit reconstructs and verifies the clipped REC label from
that original score rather than pretending that clipping never occurred.

Original PGN FEN headers must already contain valid known clocks and state;
normalization cannot supply missing clocks or repair invalid text. SetUp=1
requires FEN. Ordinary PGNs without a custom setup still start from the standard
position. The no-flag legacy converter retains its previous parser behavior.

Normalized records contain original full FEN, source and source row, source kind,
raw score and type, STM score, White and STM results, result mask, zero-based ply,
depth if known, and genuine stored best move if available. Self-play scores are
STM-relative; its result field is White-relative. Lichess cp/mate values are
White-relative and outcomes remain unknown. Fastchess PGN evaluation comments
label the position **before** the played move; a PGN source row is game:move index.
Unlabelled PGN nodes are not evaluation records. Castling, EP and clocks are kept.
Result-aware admission requires single-line ASCII standard FEN understood by
the lock: no Unicode/control separators, Shredder rights, promotion markers or
underscored/overflowing clocks. Spaces and tabs remain valid, and original valid
text is preserved. The native probe uses the same validator. Legacy no-flag
converter parsing remains unchanged.

The final review also found impossible promotion inventories accepted by Python
and rejected by Forge. The shared validator now requires enough missing pawns
to account for extra queens, rooks, bishops and knights; 20 actual native boundary
checks and the v6 handoff refresh pass. This is a necessary material constraint,
not a proof of complete game-history reachability.

`filter_positions.py INPUT NEW_OUTPUT --kind normalized --workers 2` uses one
parser/writer process and one pool process, counting both toward the total budget.
It defaults to
no exclusion, clipping, deduplication or shuffle. Add only the desired flags:

- `--drop-in-check`
- `--drop-capture-bestmove` (capture, en passant or promotion; absent metadata fails)
- `--drop-mate-scores` (explicit mate or Forge abs(score)>=31872, before clipping)
- `--max-ply-from-start 160` (inclusive zero-based boundary)
- `--drop-qs-unquiet N` always fails capability preflight for FD3A5190.

Independent counts are computed for measurable rules; overlap and first-drop
counts cover enabled rules in check/capture/mate/ply order. Best-move coverage 0
means BLOCKED, never “100% quiet.” The two JSONL output streams preserve identical
row order. Their hashes are deterministic; reports also contain nondeterministic
wall time and throughput. Failures retain unpublished `.partial` evidence, and
existing final or partial destinations are refused.

Fresh single-rule measurements on the pinned 1,000,000 self-play rows use one
parser/writer plus one pool worker at BelowNormal priority (two total computing
processes). Source 88b7c6b1, unchanged filter SHA256 beginning b3fdda81. Earlier
two-pool-worker measurements remain historical evidence and are superseded here:

The table measures processing and final input-identity verification, excluding
startup/initial source fingerprinting and final output hashing. End-to-end
execution of all six self-play cases took
875.000 seconds for six million row visits (6,857 positions/s).

| Enabled rule | Kept | Keep rate | Seconds | Positions/s |
|---|---:|---:|---:|---:|
| None | 1,000,000 | 100% | 145.579 | 6,869 |
| Check | 1,000,000 | 100% | 142.983 | 6,994 |
| Mate | 1,000,000 | 100% | 144.569 | 6,917 |
| Ply <=160 | 909,569 | 90.9569% | 144.254 | 6,932 |
| Check + mate, run A | 1,000,000 | 100% | 143.428 | 6,972 |
| Check + mate, run B | 1,000,000 | 100% | 143.356 | 6,976 |

Runs A/B have identical payload hashes. These prefiltered self-play shards have
no stored best moves, so their capture rate is unavailable. Qsearch remains
BLOCKED on the exact lock. On the **separate measurement-only gate PGN cohort**,
all 1,000,000 rows have genuine baseline searched best moves. Capture/promotion
exclusion keeps **849,465 (84.9465%)**, dropping 150,535 in **154.994 seconds**
(6,452 positions/s, two total workers). The strict PGN freeze took 225.243 seconds with
one worker. The capture filter's complete command took 156.812 seconds
(6,377 positions/s). These rates cannot be substituted into the self-play table or pooled
with it. Neither recipe uses the gate PGNs.

The matched recipes use check/mate filtering and the same holdout-cleared rows:
evaluation-only lambda=1.0, or WDL lambda=0.8 on known-result self-play and 1.0
otherwise. Exact crew-owned commands and output names are in [MIX_SPEC.md](MIX_SPEC.md).

Holdout separation is a separate explicit stage, `clear_holdouts.py`. The complete
audit found 47 matching board+STM keys across 013/014. The separately named
`holdout_cleared` output excludes those keys, retains order/duplicates otherwise,
and carries a complete hash-bound clearance receipt. It does not change filter
defaults or erase the original failed overlap audit. Both recipes use this same
cleared selection.

`npt_adapter.py` uses installed `get_sparse_batch_from_fens`, clones all eight CPU
tensors before native free, and retains provenance/result masks as batch metadata.
Unknown outcomes require a neutral ABI placeholder, but lambda=1 masks that value;
the semantic result remains null. Isolated subclasses retain npt model, loss and
score scaling while supplying `[batch,1]` lambda. The Python sampler has constant
state and deterministic affine permutations; no fast-loader work is included.
Only one process/device and zero loader workers are supported. Training resume is
limited to checked epoch boundaries; sampler state itself can resume at any row.

## Evidence and handoff

See [EVIDENCE_INDEX.md](EVIDENCE_INDEX.md) for the current proof map, RESULTS.md
for statuses and REVIEW_LOG.md for candidate hashes, findings and fixes.
The user's latest override puts new outputs under `C:/astra8_data/`, with
C: above 50 GB including planned allocation. Existing D:/F: artifacts are read-only
and count with C: toward the 15 GB aggregate cap. The historical sample
is at most 20 MB. Inputs, original logs and failed attempts are preserved.
MIX_SPEC.md supplies the two crew-owned commands and exact recipe differences.

Run CPU tests with F:/nnue_pytorch/venv/Scripts/python.exe, bytecode disabled,
CUDA/HIP/ROCR devices hidden, OMP/MKL/OPENBLAS threads set to 1, and TEMP/TMP under
the new output root. No GPU is needed for native feature or scalar-reference loss
checks. All owned execution uses BelowNormal priority and at most two compute workers.

Reproduce CPU tests with a new destination (the wrapper sets those environment
limits and checks storage before creating it):

```powershell
./astra_r8/datafilter/run_cpu_tests.ps1 -OutputDirectory 'C:/astra8_data/review_tests_new'
```

Archived Python snapshots under `evidence/` are excluded from pytest collection;
their original bytes are preserved. The complete runnable suite is in `tests/`;
archived launchers never become tests when collecting the broader tool directory.

`audit_followup.py identity NEW_RUN_ROOT`, `orientation NEW_RUN_ROOT` and
`million NEW_RUN_ROOT` rerun the pinned legacy identity, actual binary result
round-trip, and independent single-rule/determinism measurements respectively.
Create a new run root under C: first, use the same CPU-only environment, and run stages sequentially.
Each stage refuses existing destinations. `refresh_handoff.py NEW_HANDOFF_DIR`
rehashes the approved unchanged cohort/holdouts and runs both CPU preflights
before publishing a refreshed manifest. It never starts training.

Historical first follow-up: `evidence/stm_v1/handoff_manifest.json`, full-output hashes
in `evidence/stm_v1/full_output_hashes_stm_v1.json`, and the separately named
`sample/positions_stm_v1.jsonl` (10,000 rows,3,139,111 bytes). That historical
manifest SHA256 is `67beceef2a033d62d6d8cf75dce8284b1935e5dfa65c75c6f2fde253c7b4a8df`.
Fresh sign audit: Pearson0.6635950368,1000 mirrors PASS; both CPU recipe
preflights and published handoff verification PASS. Missing results remain excluded
from correlation. The real cohort has no unknown results; synthetic tests cover them.

Handoff: Code Review → Engine NNUE → Engine QA. Subsequent FD3A5190 comparison,
UHO first, 8moves_v3 separately, and WAC300 remain crew-owned. Every recipe and
strength result remains UNPROVEN.
