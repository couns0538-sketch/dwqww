# Astra R8 Job 2: result-aware data tools — UNPROVEN

The production converter and installed npt are untouched. This directory contains
an isolated compatibility extension, an independent deterministic filter, and an
original bounded Python adapter to installed npt. No training or GPU work is run
by this job. Correct conversion and loss checks establish no playing-strength gain.

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

Normalized records contain original full FEN, source and source row, source kind,
raw score and type, STM score, White and STM results, result mask, zero-based ply,
depth if known, and genuine stored best move if available. Self-play scores are
STM-relative; its result field is White-relative. Lichess cp/mate values are
White-relative and outcomes remain unknown. Fastchess PGN evaluation comments
label the position **before** the played move; a PGN source row is game:move index.
Unlabelled PGN nodes are not evaluation records. Castling, EP and clocks are kept.

`filter_positions.py INPUT NEW_OUTPUT --kind normalized --workers 2` defaults to
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

Fresh single-rule measurements on the pinned 1,000,000 self-play rows, two
compute workers at BelowNormal priority:

| Enabled rule | Kept | Keep rate | Seconds | Positions/s |
|---|---:|---:|---:|---:|
| None | 1,000,000 | 100% | 70.715 | 14,141 |
| Check | 1,000,000 | 100% | 73.420 | 13,620 |
| Mate | 1,000,000 | 100% | 70.300 | 14,225 |
| Ply <=160 | 909,569 | 90.9569% | 73.503 | 13,605 |
| Check + mate, run A | 1,000,000 | 100% | 72.303 | 13,831 |
| Check + mate, run B | 1,000,000 | 100% | 69.276 | 14,435 |

Runs A/B have identical payload hashes. These prefiltered self-play shards have
no stored best moves, so their capture rate is unavailable. Qsearch remains
BLOCKED on the exact lock. Capture statistics from the separately pinned gate
PGN cohort will be reported separately; they cannot be substituted into this table.

The matched recipes use check/mate filtering and the same holdout-cleared rows:
evaluation-only lambda=1.0, or WDL lambda=0.8 on known-result self-play and1.0
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

Handoff: Code Review → Engine NNUE → Engine QA. Subsequent FD3A5190 comparison,
UHO first, 8moves_v3 separately, and WAC300 remain crew-owned. Every recipe and
strength result remains UNPROVEN.
