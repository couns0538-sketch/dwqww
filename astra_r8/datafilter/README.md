# Astra R8 Job 2: result-aware data tools — UNPROVEN

The production converter and installed npt are untouched. This directory contains
an isolated compatibility extension, an independent deterministic filter, and an
original bounded Python adapter to installed npt. No training or GPU work is run
by this job. Correct conversion and loss checks establish no playing-strength gain.

## Interfaces

`convert_forge.py OUT --selfplay INPUT --keep-result` writes the established
32-byte REC format plus aligned train/val JSONL metadata. Byte 29 is `has_result`;
byte 30 is White loss/draw/win = 0/1/2. Unknown outcomes have mask 0 and semantic
null. Without `--keep-result`, legacy filters, first-occurrence deduplication,
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
wall time and throughput. Filter/holdout failures retain unpublished `.partial`
evidence, and existing final or partial destinations are refused. `rebind_manifest.py`
is the exception: on failure it deletes its own `<new>.partial`, so nothing is left.

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
score scaling while supplying `[batch,1]` lambda. The Python sampler ('perm-v1') has constant
state and a seeded full permutation per pass (numpy default_rng([seed, pass])); its
checkpoint state stores numpy.__version__ and a pass-1 order hash, and resume refuses a
different numpy or stream, old affine-v1 states, and old perm-v1 states written before
fix 7 (753a85a7) that lack those keys. No fast-loader work is included.
Only one process/device and zero loader workers are supported. Training resume is
limited to checked epoch boundaries; sampler state itself can resume at any row.

## Evidence and handoff

See RESULTS.md for statuses and REVIEW_LOG.md for candidate hashes, findings and
fixes. Full new outputs live under `D:/grok-pc-data/dwqww/astra8_data/`; the sample
is at most 20 MB. Inputs, original logs and failed attempts are preserved.
MIX_SPEC.md supplies the two crew-owned commands and exact recipe differences.

Run CPU tests with F:/nnue_pytorch/venv/Scripts/python.exe, bytecode disabled,
CUDA/HIP/ROCR devices hidden, OMP/MKL/OPENBLAS threads set to 1, and TEMP/TMP under
the new output root. No GPU is needed for native feature or scalar-reference loss
checks. All owned execution uses BelowNormal priority and at most two compute workers.

Handoff: Code Review → Engine NNUE → Engine QA. Subsequent FD3A5190 comparison,
UHO first, 8moves_v3 separately, and WAC300 remain crew-owned. Every recipe and
strength result remains UNPROVEN.
