# Frozen23 evaluation screen — no qualifying new candidate

Source inspected: `1d3ed25bea2c8b781f7ee5a178af0f66061b3984` (parent-supplied verified frozen23 pin). Supplied actual SHA256 pins: `src/eval.cpp` = `21b82c53e2ea83120d58a024bd3eaa20b579bcdca63cd38e290944467b5cb8a3`; `include/forge/eval.hpp` = `e6cb2b620f5c7fd87cef7a680aea04c4ba756f106b78d5a8fa7ab3cdd5d0cc35`.

**Disposition: none.** This bounded read-only source screen did not identify a genuinely new, concrete evaluation correctness/move-selection defect or substantial surviving wasted computation with a defensible real-engine RED. It does not establish that evaluation is bug-free. No candidate, patch, engine execution, build, benchmark, Git command, network operation, or experiment launch was performed. Main experiment remains23.

## Inspected evidence

Read `AGENTS.md`, `src/eval.cpp:1–530`, and `include/forge/eval.hpp:1–68`; targeted history searches/readbacks covered `docs/CURRENT_BASELINE.md`, `docs/EXPERIMENT_LEDGER.md:249–340`, `docs/NEXT_EXPERIMENTS.md:1–108`, `validation/next-search-after22-20261021/REVIEW.md`, and the existing pawn-span next-review records. The latter review contains an actual-object code-generation result; this screen did not reproduce that result.

| Mechanism | Current source and historical evidence | Screen result |
| --- | --- | --- |
| Pawn structure/cache boundary | `eval.cpp:55–97` depends on pawn placement; cache hit/miss handling is `397–415`; king-dependent evaluation occurs separately at `198–273`. | No evident newly introduced non-pawn dependency in cached pawn score/passed masks. |
| Pawn attack span | `eval.cpp:109` uses existing `forward_fill` on the enemy pawn attack mask. `EXPERIMENT_LEDGER.md:320–331` records candidate20's replacement of the old per-pawn traversal, independent rank-walk/old-loop checks, and public trace comparisons. | Already implemented; do not re-propose. |
| King/nearest pawn distance | `eval.cpp:269–272` calls `nearest_square_distance`; current baseline/history identifies candidate21. | Already implemented; excluded. |
| Runtime material/PSQT | `eval.cpp:382–395,486–521`; `eval.hpp:36–42`; `EXPERIMENT_LEDGER.md:249–261,273–285` records candidate19 runtime replay, public live-table oracle retention and actual parity evidence. | Already implemented; excluded. |
| Repeated queen rays | `eval.cpp:131` computes queen attacks; `190–192` computes directional rays for WeakQueen. Existing `validation/pawn-span-fill-20261020/next-review/queen-rays-codegen.md:1–5` and companion JSON report actual frozen20 GCC14.2 Release reuse in both traced/untraced specializations and both colors. | Source duplication alone is insufficient; earlier actual code generation rejected this optimization premise. No fresh substantial waste established. |
| Mobility/king safety/threats/passed terms | `eval.cpp:117–195,230–267,275–344` intentionally use mobility/x-ray attack maps and tuned heuristic predicates. | Apparent differences from legal-move attacks are not themselves contract violations. No isolated concrete defect established. |
| Endgame scaling and packed scores | `eval.cpp:346–371,455–466`; `eval.hpp:13–27`. | Heuristic scaling choices and legal-position magnitude concerns did not yield a source-grounded failure witness in this screen. No arbitrary alternate score expectation is proposed as RED. |

## RED status and confounders

No new RED is proposed because no candidate cleared the source/evidence threshold. A change in a tuned evaluation term, score or chosen move would demonstrate behavior change, not correctness by itself. The existing attack-map x-rays, packed/tapered scores, material-dependent scaling, pawn-cache hits, runtime state and default residual NNUE path are potential confounders for any future evaluator experiment. Source-call duplication also needs attributable object/runtime evidence before calling it wasted computation.

Next action: retain this explicit negative screen and continue the parent frozen23 task. Do not open an evaluation patch, protocol, benchmark, or NNUE retraining task from these observations.
