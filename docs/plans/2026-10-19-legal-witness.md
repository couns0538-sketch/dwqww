# Legal-witness candidate

Parent checkpointcb1cafa6048976382da6bcd8616da53771176af0 publishes tested6.4.4
source816423b1ddac23a00244449deef59dba736055a9. The accepted reference9108d012
remains unchanged. All later work is preserved in this isolated6.4.5 candidate.

Hypothesis: terminal detection currently generates a complete pseudo-legal move
list at every queried search node. One exactly legal nonpromotion pawn push
already proves a position has legal moves, avoiding that list. Generate one
empty-square single push, call the existing exact is_legal, and return true only
on success. Preserve the complete original fallback for absent/failed witnesses,
promotions, pins, checks, en passant and castling. No pruning or score changes.

Before implementation, the unmodified6.4.4 library passed18947 Boolean checks:
23curated fixtures, all10000 corpus positions and deterministic legal walks.
Checks compare against both the exact old full-generator algorithm and actual
make/unmake followed by own-king safety; they also verify board/key/checker state
is unchanged. The make oracle shares pseudo-generation/castling transit filters,
so it is not a fully independent chess implementation. Preserve these limits.

Compile fresh Release, run all eight CTest suites and the complete differential
corpus. Require exact cold/warm one-thread output/node parity and appropriate
sanitizers. Run the bounded prepared kernel harness only after correctness,
checking emitted indirect dispatch, data/checksums and same-function AA noise.
Freeze repetitions before AA/AB outcomes, retain all60 required blocks, and mark
any incomplete/noisy run inconclusive. No retries, trimmed pairs or automatic
speed acceptance. This compares the actual API kernel with an old-algorithm
public-helper reference whose translation-unit inlining may differ; it cannot
prove isolated pure fast-path cost, whole-engine NPS or Elo.

The earlier whole-engine same-binary A/A showed severe real execution variance.
Do not repeat a full A/B on that calibration or claim small speed gains. Native
stable equal-clock SPRT remains the playing-strength gate. Retain promising
correctness-preserving work even when speed/strength are inconclusive.
