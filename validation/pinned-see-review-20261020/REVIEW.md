# Independent review of isolated pin-aware SEE prototype

Decision: no patch-specific correctness blocker found in the reviewed change. The saved matrix supports a bounded pin-filter correctness result. It does not establish an exact legal-exchange implementation, full-engine acceptance, speed, or playing strength. Preserve the prototype and existing 6.4.14 evidence separately.

## Scope and identity

Read-only source/artifact review on 2026-10-20. No engine, compiler, match runner, network review service, or production-source mutation was run for this review. The only written artifact is this file. Python was used to inspect saved outputs/hashes and, for the inherited promotion limitation below, query python-chess legal captures without running an engine.

- Baseline source: `21538ec5416c909fc98a08688242a0b3b9710b25`. Current `src/board.cpp` and that commit's file independently hash to `5baa16d3f04f5aea2622480c02ba09fa094044bfc93754a075929ed39f3ff1e2`.
- Candidate: `validation/pinned-see-prototype-20261020/candidate-board.cpp`, SHA-256 `d8c5066db1381e03a72e2baceb65553277020880c78d84007db2e11ff2d46705`.
- Patch: `validation/pinned-see-prototype-20261020/pinned-see.patch`, SHA-256 `530118c886a5653776deb929b7ef9a85502b9e9efb057b66d7defed68fe83bf8`.
- The saved build record reports only `board.cpp.o` replaced in the frozen core. This review inspected that record; it did not rebuild or independently reconstruct the archive provenance.

## Source conclusions

1. **Virtual occupancy and removed masks are consistent for non-king recaptures** (`candidate-board.cpp:852`, `:860`–`:873`). Every consumed origin disappears from occupancy. Intersecting accumulated attackers with occupancy removes consumed pieces. `removed = ~occupancy | square_bb(to)` suppresses stale enemy pieces at empty origins and the original victim retained in the piece bitboards at the target. Original color bitboards are safe for selecting remaining origins because the virtual target is never its own attacker.

   Testing `occupancy ^ square_bb(square)` removes the candidate origin while leaving the target occupied by the hypothetical recapturer. The target must stay occupied to preserve legal captures along a pin ray. The candidate origin need not also be added to `removed`: it belongs to `stm`, while the helper queries only `opposite(stm)`. Marking all originally empty squares removed is harmless because the helper intersects with original piece bitboards.

2. **The filter handles every non-king candidate before LVA selection** (`:867`–`:874`). A low-square pinned knight cannot hide another legal knight of the same value. The existing authored `first_pinned_second_legal_knight` pair exercises that case. Existing LVA ordering and the `lsb` tie choice remain; this is not a search over every equally valued exchange continuation.

3. **New and released pin rays use the current virtual position.** The helper is called anew on each exchange ply with current occupancy and removed pieces. It does not cache the original pin set. Departed pinners disappear through `~occupancy`; the captured target pinner disappears through the explicit target mask. Orthogonal and diagonal newly exposed pins and target ghosts have saved controls. No stale-pin blocker was found.

4. **EP and initial promotion handling are retained.** Initial EP removes both the origin and the actual captured-pawn square before recomputing target attackers, so the added filter sees both opened rays. Initial promotion adjusts initial gain and attacker value before the early exits; the virtual promoted type is unnecessary for the non-king legality filter because the piece on the target is captured by the hypothetical recapture. Current EP controls are simple unrecaptured/rook-recaptured cases; they do not specifically exercise an EP-opened pin ray.

5. **The king branch remains unchanged** (`:897`–`:900`). Kings are excluded from the new filter and still use the existing geometric target-attacker check. Retaining geometric enemy attacks is appropriate for king safety, including enemy pieces constrained by a pin. Existing first king-recapture legal/illegal pairs remain in the matrix. Initial king captures cannot reach the new loop: their `SeeValue` is zero, so one of the two initial threshold exits decides the result. Castling returns immediately. Consequently the new helper does not use a stale king origin after an initial king move.

6. **The initial threshold exits remain material bounds, not legality validation** (`:848`–`:850`). They can return before any pin check. For the retained ordinary non-promotion-recapture SEE model, removing illegal recapture options does not invalidate those initial captured-value/lost-attacker bounds. The inner swap exits retain the existing parity and LVA behavior. A legal initial move is still required for a legal-exchange interpretation, and ordinary valid board/move fields are required for safe direct API access.

   `MovePicker::GoodCaptures` calls SEE on generated pseudo-legal captures before the main loop checks legality (`src/search.cpp:353`, `:501`, `:1028`). Thus the method must continue tolerating pseudo-legal initial moves; it must not be treated as a move-legality validator. The direct qsearch, ProbCut, pruning, and extension uses follow legality checks. The two saved illegal-initial controls check API legality agreement but deliberately exclude their SEE values from the oracle verdict.

## Saved oracle result independently checked

The corpus/output hashes match the recorded 300-case run. I reparsed the saved TSV outputs and recomputed exchange/threshold comparisons against the saved independent oracle values, without executing the diagnostic binaries.

- Main matrix: 300 positions/moves, comprising 12 original, 32 authored, and 256 seeded sparse cases. Two original initial moves are illegal; 298 legal cases contribute 5,960 threshold answers per build across 20 thresholds.
- Candidate: zero exchange-value mismatches and zero bad threshold answers on those 298 legal cases. Baseline: six mismatching cases. The candidate corrects absolute orthogonal pins, absolute diagonal pins, and newly exposed orthogonal pins for both colors.
- Supplement: four legal mirrored cases and 80 threshold answers per build. Candidate: zero mismatches. The two newly exposed diagonal-pin cases change from baseline -300 to oracle/candidate -800. The target-bishop ghost pair remains correctly -500 in both builds.
- Combined saved evidence: 302 legal cases, 6,040 threshold answers per build, eight corrected baseline cases, no candidate mismatch in the saved corpus. The rejected first supplement fixture was preserved and never executed against an engine; it is not an additional pass or failure.

Coverage is shallow: the main legal corpus has 235 cases with no target recapture, 48 with maximum exchange-tree depth 1, 11 at depth 2, and four at depth 3. Seventy-three seeded initial captures are king moves and therefore exercise only the unchanged initial threshold exits. Counts alone should not be read as broad dynamic-pin coverage. The independent oracle searches legal captures to the same target with optional stopping; it does not search off-target tactics.

## Inherited correctness limitation, not introduced by this patch

**Recapture promotions are still unsupported** (`candidate-board.cpp:878`–`:881`, unchanged from baseline). Only the initial move receives promotion gain/type handling. A later pawn recapture is charged as an ordinary pawn capture, and the initial threshold bounds can already decide the wrong answer for an exact promotion-aware exchange interpretation.

Concrete valid control: FEN `7k/8/8/8/8/1Q5K/p7/1r6 w - - 0 1`, initial move `b3b1`. The independent python-chess same-target oracle is -1200: White gains 500, then `a2b1q` gains 900+800=1700. In both source versions, threshold -400 takes the initial true exit (`swap = 900 - (500 - (-400)) = 0`), while the oracle answer is false. Following the unchanged pawn-value model yields -400. No actual baseline/candidate execution of this new control was performed in this review.

This is a blocker for claiming universally exact promotion-aware SEE, not evidence of a regression caused by the pin filter. The present matrix's eight initial capture-promotion and eight initial quiet-promotion controls do not cover it. Preserve the limitation explicitly if the candidate scope remains pin filtering; do not silently count this control as an exact-SEE pass.

## Bounded follow-up coverage before integration

1. Add mirrored EP controls where removing the origin/captured pawn opens an orthogonal or diagonal king ray affecting a later candidate; keep initial-illegal EP separate from legal EP continuations.
2. Add a three-or-more-recapture authored exchange where a pinner departs or is consumed mid-sequence, plus a control where the newly eligible piece is selected after its pin is released. The existing short fixtures and sparse depth distribution do not isolate this lifetime case.
3. Add a mixed attacker fixture with all non-king recapturers rejected and a remaining king, and a geometric pinned defender of the king's destination. This exercises the transition from the new filter to the unchanged king branch.
4. Add ordinary legal quiet moves whose SEE changes due to a pin, a checking initial move with an unrelated/discovered checker, and opposite equal-value-origin order controls. Current authored quiet tests concern promotion; pseudo-legal captures are the randomized input class.
5. Bracket every authored oracle value at `value-1`, `value`, and `value+1`, using actual `see_ge` calls. The saved fixed threshold grid plus `static_exchange` binary search is useful but does not explicitly test every case's adjacent boundary. Include the inherited recapture-promotion control as a documented limitation or a separately authorized repair.
6. After any source integration, run the repository's relevant full Release and sanitizer CTest gates and UCI/search legality regressions against the frozen candidate. The saved core diagnostic is not those gates, and search parity with the parent is not expected for an intentional SEE behavior change.

## Performance and strength are separate

The new loop performs a full enemy attack query for every available non-king recapturer on every visited exchange ply, before the existing material exit can stop that ply. That adds pawn, knight, king, bishop, and rook attack work even when no pin exists or an early material decision is close. This is a concrete hot-path cost concern; its magnitude is unmeasured. The tiny saved diagnostic elapsed times are not a calibrated benchmark, and the two supplement timings reverse direction.

No speed, equal-clock strength, Elo, Windows/Ryzen result, or release acceptance follows from this review. The next useful result is a compact expansion of the targeted correctness cases, followed by the required full-engine gates on an isolated frozen candidate. Performance needs its own bounded calibrated evidence; strength needs its separately declared validation protocol.
