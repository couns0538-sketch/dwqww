# Forge6.4.11 capture update fusion

Parent6.4.10 `36f5b2f6e1ff519e82a4b52edc85caceaf15aed0`; candidate
`c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`.

Normal captures, en passant and capture promotions produce exactly three dirty
changes: remove mover, remove victim, add mover/promoted piece. The original
update copies each perspective accumulator, then traverses it three times. This
guarded path computes `((parent - removed0) - removed1) + added` in one pass.
Each intermediate operation stays in original order, with no fast-math/FMA.
All other masks/counts retain the existing fallback. The earlier two-change
quiet path and accepted network/weights/search/time settings remain intact.

Source-level traffic reduces roughly11KiB to5KiB per capture update across both
128-float perspectives. This predicts less traffic and loop overhead; it does
not measure speed or Elo. Capture frequency/code size could limit the benefit.

Release9/9, actualAPI1644case update stream, original21.2MB NNUE stream and
six cold/warm single-thread search comparisons pass before source freezing.
The first sanitizer configure failed because the export omitted `bench/`;
no instrumented engine was built or run in that attempt. Both original logs
and incomplete export are retained; attempt2 uses a new complete source export
and build directory. No failed engine result is hidden.

Keep candidate isolated until sanitizer/Windows validation. Proposed strength
comparison is the combined6.4.10+6.4.11 fusion versus6.4.9, equal2+0.02 native
Linux0/+5SPRT with fresh paired openings; it cannot establish nativeWindows,
Ryzen or Stockfish superiority. No speed or positiveElo result exists yet.
