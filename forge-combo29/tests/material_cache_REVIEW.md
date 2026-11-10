# Lazy material-correction index reuse

Status: **UNPROVEN** for speed or playing strength. Default-off experiment behind `FORGE_SPD_MATERIAL_CORRECTION_CACHE=1`. No evaluation constants or network data change.

## Design and invariants

Each SearchStack stores one material-correction index with `CorrectionSize` as the invalid sentinel. Both main search and qsearch reset the sentinel as their first action, including early exits, depth-zero dispatch, sibling reuse and same-ply re-entry. The original material hash calculation remains unchanged.

Only the existing positive material-correction-weight branches request an index. Corrected evaluation computes it lazily, and correction-history update reuses it after the board is restored. Nodes skipping correction do not compute it. No NNUE validity or enablement condition controls invalidation.

Same-ply singular, razoring and verification searches operate on the same board and restore it before returning. They may invalidate and recompute the shared slot, but any stored index still describes the outer node's material. A same-ply early return may leave it invalid; a subsequent correction update computes it again lazily. Child searches use the next slot. Default-off code retains the original material-key expressions under `#else`, without the cache field or entry invalidations.

## Reproduce

From the repository root, on an x86-64-v4-capable machine with GCC 14:

```sh
CXX=g++-14 bash forge-combo29/tests/material_cache_check.sh /workspace/shared/forge-build/material-cache
```

The script builds otherwise identical strict-FP default-off and enabled engines, runs the focused contract test and the existing 128-FEN, depth-7, single-thread equivalence screen with NNUE both enabled and disabled. OwnBook is off, Hash is 16 MB and each position starts with `ucinewgame` followed by `isready`. No timing or Elo inference is made.

## Observed results

- 256 position/configuration comparisons: **zero failures**, matching final depth, nodes, score, PV and best move. Detailed binary hashes, fixture hash, FENs and outputs are preserved in `material_cache_results.json`.
- Focused `material_cache_unit.cpp`: **PASS** for lazy index calculation, weight-zero skip, NNUE independence, cached reuse and entry invalidation on qsearch, positive-depth main search, depth-zero main dispatch, and repeated same-ply calls. It uses a test-only access-control override, without production test hooks.
- Focused test was built with GCC 14, C++20, `-O2 -ffp-contract=off -fno-fast-math -pthread`, `FORGE_NNUE_HIDDEN=256`, and `FORGE_SPD_MATERIAL_CORRECTION_CACHE=1`; it includes `search.cpp` and links `bitboard.cpp`, `board.cpp`, `book.cpp`, `eval.cpp`, `eval_params.cpp`, and `nnue.cpp`. The reproduction script also runs this test with its engine flags.

The parent review performs deeper bench/perft pins separately. These results do not establish all-position equivalence, performance benefit, or Windows/Clang parity.
