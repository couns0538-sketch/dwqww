# IDEA_SOURCE — fc_buckets8_h256e12

- Idea source: Couns's own Forge repo, dwqww commit bde3dc9d38c270d6c93193f04660b728e866ef13 ("buckets8", by Sol;
  release forge-6.4.24-buckets8-experimental-windows-zen5). Forge is Couns's engine, so reusing its design is allowed.
  Read for the design: Sol's src/nnue.cpp and include/forge/nnue.hpp at that commit (head-count macro, piece-count
  band formula, head-major W2 layout). QA's review: /workspace/forge-sol-buckets8/QA_REVIEW.md.
- General technique: piece-count output buckets (several output heads selected by material phase) are a common,
  general NNUE technique; no other engine's code was read or copied for this candidate.
- Our implementation: written fresh on the h256_e12 lock (H256, float, g++). Differences from bde3dc9d:
  runtime always has 8 heads (legacy include replicated into every head, instead of a 1-head compile-time path);
  head weights+bias stored together per head (OutputHead struct); own constexpr `output_head(int)` with clamp,
  testable at compile time; own tools (make_heads_inc.py replicate/check/control, heads_parity.cpp); own ctest
  (forge_nnue_heads_tests). Kept from the design: band formula clamp((pieces-1)>>2,0,7), head-major W2, int16/4096
  quantisation, FORGE_NNUE_WEIGHTS_FILE diagnostic include (and FORGE_NNUE_OUTPUT_BUCKETS accepted as alias).
- Not ported: Sol's trainer/exporter (train_bucketed_nnue.py), Windows release files, the learned epoch-7 net.
- Weights: step 1 = h256_e12 net md5 6d22f612c855e17c62d396d32da99ea4 replicated 8x (no new learning).
- Verified here only: bench, parity, perft, ctest, SIMD/FMA screens listed in README.md. No Elo/strength claim.
