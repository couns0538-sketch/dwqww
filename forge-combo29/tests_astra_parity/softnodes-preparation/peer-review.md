# Softnodes harness read-only review

Reviewed initial source SHA256 `4069633e006c00b1d3c9c3d33f97a004fa9c86a755e424cd9190edb14cddc116` (`softnodes_play.cpp`), parser `b338c6b3091abaeefbee8fa21eea0de77fd9fd6f5d119a0100ecd3233df9eab6`, and unchanged measured transport `606bd7cd54e94acba10da32bacc9c2620b7e5d8882b360e2492294ac197d40d2`.

No engine/test executions, source edits, Git actions or root-state writes were performed by this review.

1. Acceptance gap: the `ucinewgame`/`ready` reset transcript is published at original line 152 without a diagnostic scan; the next search starts its slice after that output. Final shutdown checks scan only the shutdown delta. Therefore a reset-time sanitizer report can remain in retained raw text while SUMMARY reports no fault. Check all process diagnostics before success, and preferably scan reset output immediately.
2. Parser gap: `nodes` is extracted directly into an unsigned integer. A malformed negative token can wrap to a huge unsigned count and falsely satisfy the 2,500-node predicate. Parse a strictly decimal nonnegative token, as already done for softnodes X.
3. Protocol coverage gap: labels emitted outside checked search slices, particularly a late duplicate during final shutdown or between games, are not rejected. Retain and inspect out-of-search output for unexpected softnodes labels.

The main intended logic is sound on the reviewed paths: one usual and one soft game per accepted pair; accepted snapshots updated only after both finish; partial observations kept separate; last exact score line retained as a unit; bound lines ignored; item 3/4 failure stops before applying the returned move or launching another search. The ready barrier catches labels that arrive before readyok. Every search trigger retains position history and FEN. The outer timeout plus inner deadlines bound runs; actual invocation still requires the root recorder.

This review concerns the validation harness, not evidence of engine defects. Corrections and new parser checks remain the parent agent's responsibility.

## Follow-up review

Current source `b4fccde476db249dc3ee9b06bd3834aeb9bded1ca3201de4750eda420721fd9e` and parser `4287ec2a4252b58faeb6efef5bd4664d4bd9e0f0823558b56045c795bad1a292` address all three reported gaps: reset output is scanned, all process diagnostics are checked before success independently of the primary fault, strict decimal conversion rejects signed/overflowing node values, and global-minus-checked label counts expose out-of-search labels. Opening terminal positions now terminate normally and are counted explicitly; no searched position receives an item-4 exception beyond the requested mate/cap cases.

No new blocking source issue found in this limited read-only follow-up. The accounting auditor should additionally require at least one completed pair and positive usual/soft search counts, or explicitly report no coverage: its current pass predicate accepts an otherwise clean zero-work summary. This is an acceptance-accounting concern, not an observed engine failure. No native runs were made by this reviewer.
