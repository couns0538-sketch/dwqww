# Native validation

All four stages exited 0: compile current guarded search.cpp (5.885 s), compile test (2.096 s), link (0.056 s), run (0.031 s). These elapsed values document the execution only and are not speed measurements. Every child command had a timeout of 180 seconds or less. No checkout/source/ref/state changes or push were made.

Exact arguments, working directories, timestamps, timeouts, exits, stdout and stderr are retained in `01-compile-search.*`, `02-compile-test.*`, `03-link.*`, and `04-run.*`. `native-inputs.json` hashes the tested source/header, test, flags.make, and baseline objects. `validate.py` is the exact driver. It read the guarded checkout `/workspace/work/dwqww-r4-guard`, using baseline-release objects for unchanged non-search/non-UCI translation units and compiling search/test with matching feature flags plus `FORGE_MATE_ALPHA_GUARD=1`.

| Witness | Off or narrow pruning | Narrow or targeted positive control |
|---|---|---|
| Known-history quiet, ply 8/depth 5 | off 31979; 2 nodes | narrow 31987; 4 nodes |
| Capture futility, positive base margin | off 31979; 3 nodes | narrow 31987; 4 nodes |
| Ordinary-alpha quiet | off 100; 2 nodes | narrow 100; 2 nodes |
| Ordinary-alpha capture | off 100; 3 nodes | narrow 100; 3 nodes |
| LMP | narrow 31979; 3 nodes | LmpBase 20: 31987; 4 nodes |
| Negative history | narrow 31979; 4 nodes | neutral history: 31987; 3 nodes |
| Quiet SEE | narrow 31979; 6 nodes | looser quiet SEE: 31987; 4 nodes |
| Noisy SEE | narrow 31979; 5 nodes | looser noisy SEE: 31987; 6 nodes |

For the last four witnesses, the isolated broad SoundArmMateAlpha arm independently reaches the target marker (4, 3, 4, and 28 nodes respectively). All 20 score assertions and both ordinary-alpha node equalities pass. The known-history legal mating continuation, unique Black replies, absence of repetition, final checkmate at clock 13, target legality, non-checking targets, SEE geometry, TT seed retention, and board restoration assertions also pass.

This is controlled supplemental move-reachability evidence. Child TT answers, move ordering, and selected history/static-eval context are artificial. It does not certify synthetic capture-fixture mate scores or reproduce the complete original-root search. The root agent owns original-root semantic tracing, the dynamic ordinary-alpha-to-mate-alpha transition, ten repeats, UCI/default/hash tests, and remaining acceptance checks.
