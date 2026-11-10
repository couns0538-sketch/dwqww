# Incremental NNUE and HCE evaluation audit

Status: **PASS for the tested fixtures and seeds; broader correctness and performance remain UNPROVEN.** No production edits.

## What was checked

At each visited position, compare incremental state against independently refreshed state:

- Every raw float bit in both perspectives of the 256-unit NNUE accumulator.
- NNUE output evaluation from incremental versus refreshed accumulators.
- Runtime HCE PSQT validity, packed score and uncapped phase against `refresh_runtime_psqt`.
- `evaluate_runtime` and regular cached HCE evaluation against `evaluate_uncached`.

The test requires the shipped residual256 network. Its integer/4096 first-layer weights make exact bit comparisons reasonable for these bounded legal-board sums. No numeric mismatch occurred, so no tolerance or approximate comparison was used. This is a tested result, not a proof for different networks or compiler floating-point transformations.

Each seed runs 32 legal playouts of up to 256 plies from the starting position and seven committed fixtures. Every sixteenth ply explores every legal sibling before choosing the next random move. The full played path is then unmade one ply at a time, checking parent FEN and restored evaluation state. Dedicated fixtures guarantee both colors' castling on both wings, both colors' en passant, and all four promotion choices with quiet and capturing promotions. Null moves are tested only when not in check and when the moving side has non-pawn material. The test checks the null position, a legal child below it, null unmake and restored parent state. A null move is a search operation, not a legal chess move.

Coverage guards fail if special-move categories, castling directions or promotion types are absent. Full fixtures and deterministic `mt19937` seeds are in the source/script. The test exercises update/refresh APIs, not the private Worker lazy-stack traversal itself.

## Reproduce

Requires GCC 14 and an x86-64-v4-capable CPU:

```sh
CXX=g++-14 bash forge-combo29/tests/eval_incremental_check.sh /workspace/shared/forge-build/eval-incremental
```

The script uses strict floating point (`-ffp-contract=off -fno-fast-math`), NNUE hidden size 256 and the current nine-switch candidate configuration. It builds only evaluation/board dependencies; search-only switches do not add search coverage. The test-only access override exposes private HCE helpers without changing production headers.

## Results

Three release seeds: **121,960 checks**, **48,336 move transitions**, zero differences. Detailed per-seed counts are committed in `eval_incremental_release.jsonl`.

- Seed 3886096422: 39,954 checks; 15,745 transitions; 813 captures; 9 EP; 127 promotions; 33 castles; 241 nulls.
- Seed 20261110: 41,440 checks; 16,489 transitions; 918 captures; 9 EP; 116 promotions; 32 castles; 270 nulls.
- Seed 305419896: 40,566 checks; 16,102 transitions; 872 captures; 10 EP; 121 promotions; 39 castles; 259 nulls.

ASan+UBSan, with nonrecovering sanitizer errors, passed seed 3886096422 and the same 39,954 checks without diagnostics. Output is in `eval_incremental_sanitize.jsonl`. Leak detection was disabled because LeakSanitizer cannot run under this environment's ptrace; leak checking remains unverified.

No speed, Elo, all-position, or Windows/Clang claim follows from these tests.
