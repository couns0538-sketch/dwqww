# Independent review of the frozen producer-subtree pass

I inspected the second-pass source/diff and parsed the retained native output; I ran no engine or compiler. This review covers `/workspace/work/all-run/part4-origin-secondpass/`. The earlier accepted-writer/endpoint conclusions remain in `REVIEW.md`.

The full second-pass trace contains 704 contiguous events. Its selected subtree has exactly 20 frames, 23225–23244, with one recorded RETURN and one FRAME_LEAVE for every frame. I independently reproduced full stdout equality after removing only numeric time/nps, and full repeated-trace equality after remapping only table addresses. The supplied native comparison records all 12 identity checks true. Raw trace-r1 stderr SHA256 is `18cb6cb51285063982d4d58e4d2afb191b9e7a381803d62c9be703dabfcf6802`.

The extra instrumentation expands observation to frame 23225's descendants, wraps existing recursive calls in a lambda invoked exactly once, and emits the existing returned value unchanged. Added terminal-return wrappers also return their original expressions. It adds no engine probe, generation assignment, pruning condition, or depth/window mutation. Physical cluster snapshots still surround existing TT operations. This is a static assessment plus deterministic identity evidence for this fixture; it is not a general timing or SMP guarantee.

## The limiting branch

Initial writer frame 23225 (black, ply 9, entry depth 6, root iteration 13) examines three legal replies. Its recorded CHILD_RESULT values are in the **child's** side-to-move convention; the caller then negates them:

| Black reply at frame 23225 | White child's returned score | Black candidate score |
|---|---:|---:|
| b2b1 | 31973 | −31973 |
| b2a2 | 31987 | −31987 |
| b2a1 | 31985 | −31985 |

The maximum is −31973, below entry alpha −495, and MAIN_FINAL stores BoundUpper raw −31982. Its b2b1 branch continues through `d2d1 b1b2 f3d3` to black frame 23229 at ply 13. That deeper frame's legal responses are:

| Black reply at frame 23229 | White child | Returned score |
|---|---:|---:|
| b2b1 | 23230 | 31979 |
| b2a2 | 23232 | 31983 |
| b2a1 | **23233** | **31973** |

Thus the relevant `b2a1`/frame 23233 is a **deeper** reply at ply 13, not the initial writer's own b2a1 branch. The limiting chain back to writer 23225 is `b2b1 d2d1 b1b2 f3d3 b2a1`.

Frame 23233 enters at ply 14, depth 1, alpha 494, beta 495, FEN `8/8/8/8/8/3R4/8/k2K4 w - - 14 8`. Raw trace sequences 425–427 show cluster 24539, slot 0, full key `1726806482296082090`, raw **31987**, **BoundLower=2**, depth 6, stored clock 8. Conversion subtracts current ply 14 to give **31973**, and sequence 428 records **MAIN_TT** returning that value with PV length 0. The depth-qualified Lower-bound cutoff therefore directly accounts for this leaf result. It does not by itself identify the earlier store that established the positive mate-valued payload.

All these clocks are below the near-50 threshold. The different stored/current clocks (8 versus 14) are explicit, not an observed rule-50 gate violation. The stored score is position-relative and the probe intentionally adjusts it by current search ply. This supports the trace arithmetic; it does not make a Lower classification a proof of exact mate distance or certify every transposition/history context.

## Legality and coverage

I independently checked the already-recorded boards with a small plain-JavaScript KRK geometry validator, without calling Forge or running any search. All **19** recorded parent→child edges are legal moves and reproduce the exact child FEN including side, halfmove clock and fullmove number. The check uses king adjacency, rook rays/blockers, captures and own-king safety. The three losing defender frames 23225, 23227 and 23229 each searched **all three legal king replies**; no defender reply is missing in those three frames. All 20 entry histories contain unique keys and all subtree edges are ordinary move edges.

This does not claim that every white move was searched, or that every other black node was exhaustive. For example, frame 23236 cuts off after one reply with an ordinary centipawn result. Search cutoffs and existing mate-valued TT leaves remain part of the observed algorithm. The subtree accounts for how the target writer obtained its number; it is not an independent full-width proof that all leaf bounds are sound.

At the time of this report, the prior-entry writer and fresh oracle checks are being collected in a separate third pass. Their conclusions are deliberately not assumed here. The existing root oracle still supports only a conservative 33-ply deadline for the printed unqualified `mate 17`, with root DTM 15 and chosen-move DTM 17, not an exact score-distance certification.

Evidence: `secondpass-incremental-diff.txt`, `secondpass-independent-check-command.txt`, `secondpass-independent-ledger.json.txt`, and `secondpass-static-legality-command.txt` retain the exact read/parse commands and real outputs. Scratch source SHA256 is `cb1636708511d8448bdbcd111b5791be06b2d9d90566d373089f182608c6dd45`; helper is `12d900c0ac9480bc064f00f3b1775c578607afc7f397f2d2030bec44f32d21f0`. No production source, refs, controller, state, or native artifacts were changed by this reviewer.
