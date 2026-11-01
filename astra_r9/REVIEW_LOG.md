# Review log

## M1 — output SIMD implementation, pre-production-build review

Baseline c8fd0e6. Reviewed nnue.cpp SHA256
8F1CA99DC2FC4374F764A786C9933E0523C94F044C803FCE7AB42C7B635FDAC1.
Reviewer subagent review_wide01 inspected without edits. No production defect found.
Verified lane mapping, operand/order preservation, 32-byte-safe unaligned loads,
default OFF, non-AVX512 fallback, and stop/join before option writes.

Confirmed proof gaps: integer-only comparison did not prove intermediate bits;
HCE digest was not combined static eval; one-ply checks did not cover long sequences.
Fix: diagnostic-only lane/output snapshots, combined residual/HCE digest, and 64
deterministic legal playouts up to 128 plies followed by full unmake. No rejected findings.
Initial diagnostic: 12k FENs, 668216 evaluations, 316108 moves, 12000 nulls, digest
f2c3e077fc92a00 identical to separate unchanged-lock harness. Corpus child coverage:
725 castles, 636 promotions, 9 en-passant moves (reviewer count).
ASan and UBSan deliberate positive controls both produced expected reports and exit 1.
Next: re-run expanded diagnostics and request focused recheck. Candidate NOT accepted.

M1 focused recheck PASS: all three gaps closed, git diff --check clean. Reviewed
nnue.cpp D11B4EED401A3F6C05EA7A5C8917E1E7F933A9E1BDF3E3992D44C62424F3F635.
Expanded unchanged-lock/candidate digests both 3bd3b27ac5a60483, 684200 evaluations,
324100 moves, 12000 nulls. Proceed with production build; not accepted pending full proof.
