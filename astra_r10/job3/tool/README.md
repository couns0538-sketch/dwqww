# Full-state conversion and relabeling — UNPROVEN

These are owned copies from frozen `d8982bc0`; `SOURCE_COPY.json` records the
original file hashes. The live trainer, original source and default binary
formats are untouched. This is data-integrity work, with no strength claim.

The recovered REC32 encoder already stores castling and EP. Its default binary
does not store clocks or game identities. The recovered relabeler already writes
an exact `.fen` sidecar when supplied original full FENs; its explicit lossy
reconstruction cannot recover absent rights or clocks. The changes make a
full-state route available without enabling result-byte changes, and bind the
sidecars to all binary rows before relabeling.

`datafilter/convert_forge.py OUT --normalized INPUT --keep-fen --seed FRESH_SEED`
keeps the existing selection, deduplication, shuffle and REC32 bytes. It also
writes normalized metadata and `train.state.json` / `val.state.json`. Each state
manifest pins the binary, full-state rows, source hashes, counts and row hashes.
`--keep-result` remains independent. No flag means unchanged legacy behavior.
Source rows with authentic `game_id` fields retain them exactly. Rows without IDs
remain unknown; filenames and row numbers are never promoted to game IDs.

For FPOS1 input with known original FEN/provenance, call
`full_state.write_state(pos, rows, new_manifest, binary_format='fpos1', sources=[original_source])`.
Each row is a dictionary with its original six-field `fen` and existing
provenance. `game_id` is optional. Save the returned manifest file's SHA256 in
the external input record. This does not prove that supplied IDs are authentic;
missing IDs are reported `UNVERIFIED`.

Pass that independently pinned hash to the real relabeler:

```
python data/relabel_positions.py --pos INPUT.pos --sidecar ORIGINAL.fen \
  --state-manifest INPUT.state.json --state-sha256 PINNED_SHA256 \
  --probe FROZEN_PROBE --out NEW_OUTPUT --count COUNT --workers 1
```

The opt-in route validates every input row, not only the selected slice. It
checks binary and metadata hashes, row indices and row-record hashes, full FEN
feature compatibility, and all six fields against the supplied sidecar. It
preserves legal noncapturable EP squares. It rechecks inputs before sealing,
retains all supplied provenance, records the previous evaluation, and updates
the new evaluation fields. Output `.pos`, `.hce`, `.fen` keep their established
formats; an additional `.state.json` and aligned rows bind their provenance.
Existing output names are refused; partial evidence is retained.

The manifest checker holds verified metadata in memory. Use a bounded frozen
cohort under the job's disk/memory allowance; this is not a streaming training
loader. It does not repair earlier datasets whose original FENs or IDs are lost.
`npt_adapter.py` already passes the original FEN to the native feature API and
`train_adapter.py` retains hash-bound JSONL inputs; neither requires a behavior
change for this fix. No training is run.

`test_state.py` executes the real relabel orchestration with a clearly identified
fixture probe pool. Those tests prove preservation and refusal behavior only;
they are not native engine relabel/search evidence. The separate resume proof
uses the existing real `tools/data2/convert_dataset.py` adapter.

The legacy 73-test suite is handled separately by the parent job. These new
tests do not claim to replace it. All work remains UNPROVEN pending crew review.
