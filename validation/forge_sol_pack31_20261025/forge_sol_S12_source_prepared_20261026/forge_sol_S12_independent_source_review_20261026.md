# S12 review-v2 source review, 2026-10-26

**No must-fix finding identified in this source-only review.** This is not native
acceptance. Patch SHA256:
`66efe4c94225d95a42e8754e3b11ff363cfb4903a855e60c0bbdfdf8b5a6ee8d`.
Regression source SHA256:
`6cc93b1b0c052fe7acad64c3f65b3cdf130c8586dd52af3209da54a7bc400b3a`.
All six changed sourceview_L_v2 hashes match the supplied v2 binding.

Reviewed alias lifetimes and all production accumulator/PSQT consumers, root and
child invalidation, current-board perspective, invalid-PSQT fallback, worker
snapshot/join ordering and compiled-out OFF guards. V2 rejects invalid/nonphysical
owner links in Release and clears aliases on fallback refresh. Zero edges borrow
only a physical ancestor; nonempty updates keep original float order. Refreshing
that owner's PSQT from the current zero-edge descendant is sound because its
piece placement/white score/phase are unchanged. Evaluation still uses the current
board. No NNUE/evaluation/TT algorithm source is changed.

The native regression source has no apparent API/fixture blocker. Its C++20 probes
allow a behavioral baseline RED; its ON oracle resolves the owner. The capture
promotion to knight avoids a following null move in check. The preregistration
explicitly matches the feature definition to the core ABI and separates complete
original CTest from the standalone ON regression.

No candidate file was edited. No compiler, engine, regression, sanitizer, match
or timing was run. Parent model/application/erasure results were not rerun. Actual
baseline RED, both-base OFF/ON node/perft/FMA gates, full CTest, ON/T2 sanitizers,
worker isolation, million-word parity and speed evidence remain UNVERIFIED.
