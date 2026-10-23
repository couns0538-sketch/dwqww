# Independent data-component source review

PASS for the four exact final data-tool/test hashes in DATA-REVIEW.json, with both concrete review findings fixed. This is a bounded source and retained-evidence review, not a replay of generation or a trained-network acceptance.

## Source flow reviewed

The generator adds an optional record hook to the original self-play function. The default return format is unchanged. It captures the actual pre-move FEN, side-to-move score, legal best move and board ply, then publishes only after a game has an actual outcome under its declared terminal/adjudication rules. A None/interrupted game writes no labels; the completed-game writer validates and serializes the entire game before appending. Run UUID plus game index supplies authentic identities. Max-ply draws are explicitly adjudicated, not described as natural draws. Engine/options/network/source hashes and observed process closure are recorded; unchanged engine/network bytes and generator code are checked at completion.

The preparer requires a successful, complete generation manifest, exact position-file hash/row count, matching engine digests/options and closed workers. Each authentic game goes to one deterministic ID-hash fold. Unknown legacy game IDs are never invented; legacy rows are training-only, and all held-out first-four-FEN keys are removed from both fresh and legacy training. Fresh data validates the recorded best move; legacy data conservatively rejects every position with any legal capture, promotion or checking move because its actual best move is absent. In-check, terminal and capped-score filters remain enforced. Black results convert White→STM once, and already-STM teacher scores are not flipped.

Fresh training rows have explicit priority. Eligible unique legacy positions across all supplied files are selected by seeded Algorithm R reservoir sampling, with examined/filter/selected counts per file. Native HCE and feature arrays come from the actual probe. The output retains ordered source-line/game provenance, hashes the NPZ arrays and provenance JSONLs, and rechecks the original input identities at the end. Zero exact first-four-FEN overlap is checked in code; no completed full-corpus zero-overlap result is asserted by this review.

## Resolved findings

1. Native process success followed by parser/schema failure previously discarded raw streams. The final postprocess try/except retains all three original streams and marks the receipt failed for malformed JSON, row-count and schema errors. New inert-producer controls demonstrate the old failure and current repair.
2. A worker could fail before delivering its final done record, causing an unbounded parent wait. The final parent loop observes completed exceptional Futures and records closure/returncode as unknown rather than inventing success. The injected pre-engine trace-open failure now yields a failed manifest without a hang. No actual Forge engine was needed for this control.

## Evidence and scope limits

The final29 unit tests passed, including both new controls. Their retained stdout includes an intentionally FAILED generation fixture; the unittest result is29/OK. Four original test/control log hashes were independently checked. Actual two-game smoke evidence records124 positions and two closed engine PIDs with returncode0, but it executed the earlier frozen generator a1b3a032 and helper c5669684, not the new failure-handling revision902b1c70. That earlier normal-path runtime evidence stays honestly labeled. The separate larger run likewise executes its own immutable v1 bundle; its final outcome and corpus acceptance require a later audit.

Successful full-corpus derived probe JSON streams are explicitly hashed rather than retained wholesale; arrays and source-line recipes are retained, while failed native streams are retained verbatim. This limited retention is declared, not mislabeled as saved raw successful transcripts. Legacy teacher-engine provenance and historical game IDs remain unknown. New authentic held-out game IDs and exact-position exclusion do not reconstruct the old games or establish universal sequence-level independence for legacy data.

The reviewer authored the probe/include parser, so those files are excluded from the independent source-review claim. No engines, compilers, CTests, benchmarks, generation, training or matches were executed by this review. No source changes were made. Real held-out loss, candidate export parity and playing strength remain separate gates.
