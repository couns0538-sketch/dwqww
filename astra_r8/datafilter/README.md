# Astra R8 Job 2: result-aware data tools — UNPROVEN

The production converter and installed npt are untouched. This directory contains
an isolated compatibility extension, an independent deterministic filter, and an
original bounded Python adapter to installed npt. No training or GPU work is run
by this job. Correct conversion and loss checks establish no playing-strength gain.

Previous verified handoff: `C:/astra8_data/quality6h_20261102/handoff_v3/manifest.json`,
SHA256 `9a7f019d757976955662381207efeededf8cc55181142271c5ae80552eef80be`.
The six-hour continuation fixes strict PGN/schema admission, source identity,
complete proof binding and aggregate CPU allocation. The latest full CPU suite
passes **290 tests + 11 subtests**.
Both actual recipe preflights and published-manifest verification pass on source
7ba94a6c. The final review and complete-corpus checks are still in progress.
The 999,953 selected rows and 10,000-row sample remain byte-identical; fresh
Pearson correlation is 0.6635950368 with 1,000 passing mirror checks.
The approved runtime-proof completeness fix requires the next manifest refresh
before current-source crew use. Commands are in MIX_SPEC.md. Older handoffs remain evidence and
deliberately fail current runtime/tooling checks after the reviewed local fixes.
Historical native proof covers 62 sample/edge/mirrored FENs and all five supplied
FD3A5190 bench counts; the expanded corpus-reservoir proof is pending. These checks
establish data and interface compatibility; strength remains UNPROVEN.

The broader closed-source profile is still running. It creates descriptive
histograms and bounded audit samples only; these are not new training inputs.

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

Normalized records contain original full FEN, source and source row, source kind,
raw score and type, STM score, White and STM results, result mask, zero-based ply,
depth if known, and genuine stored best move if available. Self-play scores are
STM-relative; its result field is White-relative. Lichess cp/mate values are
White-relative and outcomes remain unknown. Fastchess PGN evaluation comments
label the position **before** the played move; a PGN source row is game:move index.
Unlabelled PGN nodes are not evaluation records. Castling, EP and clocks are kept.
Result-aware admission rejects CR/LF inside FEN strings so accepted data remains
usable as a single UCI command. Valid original FEN text is preserved unchanged.

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
one worker. These rates cannot be substituted into the self-play table or pooled
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

See RESULTS.md for statuses and REVIEW_LOG.md for candidate hashes, findings and
fixes. The user's latest override puts new outputs under `C:/astra8_data/`, with
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
