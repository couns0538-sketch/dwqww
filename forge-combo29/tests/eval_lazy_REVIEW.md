# Worker lazy evaluation traversal audit

Status: **PASS for the recorded cases; broader correctness and performance remain UNPROVEN.** No production edits or test hooks.

This closes the specific traversal coverage gap in the separate incremental-update audit by calling the actual private `Worker::record_move`, `record_null_move`, and `static_evaluate` methods through the existing `SearcherTestProbe` friendship. The harness links the real search implementation. It does not run a full alpha-beta search or assert playing strength.

## Scenarios

- Stack setup mirrors production's four-frame prefix and ply numbering; all accumulator/PSQT validity bits initially clear.
- Both NNUE modes, and root evaluated up front versus left initially invalid. With NNUE disabled, evaluation follows the HCE bypass rather than filling the NNUE cache.
- Deferred evaluation intervals of 1, 2, 7, 31 and 96 plies. Coverage guards require actual nearest-valid ancestors at all five distances, plus no-valid-ancestor refresh and already-valid cache hits.
- Long legal chains, full make/unmake restoration, and reuse of child slots for deferred sibling subtrees.
- Every legal root move in seven fixtures, guaranteeing all four castling directions, en passant for both colors, quiet/capture promotions and all promotion types.
- Null records and their descendants, limited to non-check positions with non-pawn material, followed by unmake and parent evaluation.

At every check, `Worker::static_evaluate` must equal a fresh NNUE evaluation plus uncached HCE, clamped exactly as the residual path does. When NNUE is off, it must equal the uncached HCE oracle. With NNUE on, all 512 accumulator float values must also match fresh-refresh bits, and both accumulator and runtime PSQT must be valid.

## Reproduce

Requires GCC 14 and x86-64-v4 support:

```sh
CXX=g++-14 bash forge-combo29/tests/eval_lazy_check.sh /workspace/shared/forge-build/eval-lazy
```

The script uses strict FP, the shipped residual256 network and the nine-switch candidate configuration. No evaluation constants change. The fixture FENs, `mt19937` seeds and traversal rules are committed in the harness and script.

## Recorded results

Three release seeds passed **45,787 evaluations**, with zero oracle or accumulator-bit differences:

- Seed 3886096422: 15,288 evaluations, 39,268 move records, 2,512 null records, 41,780 restores.
- Seed 20261110: 15,211 evaluations, 39,289 move records, 2,508 null records, 41,797 restores.
- Seed 305419896: 15,288 evaluations, 39,426 move records, 2,482 null records, 41,908 restores.

Each seed exercised 1,883 no-valid-ancestor refresh cases and seven 96-ply replays. Full distance histograms and special-move counts are in `eval_lazy_release.jsonl`.

ASan+UBSan, configured to stop on sanitizer errors, passed seed 3886096422 with the same **15,288 evaluations** and no diagnostics. Output is in `eval_lazy_sanitize.jsonl`. LeakSanitizer was disabled because it cannot operate under this environment's ptrace; leak checking remains unverified.

The oracle shares the real NNUE output kernel but independently refreshes accumulator inputs; exact accumulator comparisons additionally check traversal rather than relying only on rounded output scores. No speed, Elo, all-position, or Windows/Clang claim is made.
