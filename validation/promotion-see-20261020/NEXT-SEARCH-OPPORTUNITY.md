# Next search opportunity: source-only triage

Reviewed targeted ranges of frozen17 `47f0560221d986e41a309853e1295c557fcf5bf6`. No engines, builds, profiles, Internet research, production/package edits or Git mutations. These are unimplemented hypotheses with source-demonstrated mechanisms, not measured Elo gains or reproduced chess defects. The current17 experiment remains frozen.

## 1. Test correction-history feedback without its extra decay — first recommendation

**Source fact:** `corrected_eval` adds pawn and material corrections (`src/search.cpp:614–620`). `update_correction` then forms its target from `best_score - static_eval`, but the caller passes that already-corrected static evaluation (`:1190–1196`). The entry update is an EMA **towards that remaining residual**, rather than a residual increment (`:623–631`). Default material weight is100 (`:50`).

For a repeated identical key and fixed true raw-evaluation error Δ, with no competing alias updates and ignoring integer rounding/clipping, one active entry obeys `x'=(1-w)x+w(Δ-x)` and settles at Δ/2. With both equal entries active, each obeys `x'=(1-w)x+w(Δ-2x)`; total correction settles at2Δ/3. This attenuation follows from the arithmetic. Whether it is useful regularization or unnecessary under-correction is an **unmeasured strength question**, not an established bug.

**Why first by expected gain per engineering minute:** a small, isolated arithmetic ablation affects corrected evaluation used by several main-search pruning decisions, works on hosted x86-64-v3 and Zen5, and needs no network change. Do not retune other search constants simultaneously.

**Minimal counterfactual:** use the actual correction methods in an untimed internal driver with fixed raw eval/target, identical keys, unclipped errors and both one-table/two-table controls. Compare the current update with only `entry += diff * weight / 256` under the existing clamp; retain the same call guards, depth weight and material coefficient. Verify convergence, rounding and saturation first. Reject/deprioritize if greater correction only amplifies noisy search bounds; any strength claim still needs a fresh equal-clock experiment. No runtime test was executed here.

## 2. Check history pruning of quiet main-search evasions

**Source fact:** the main move loop's shallow-pruning outer guard does not exclude `in_check` (`src/search.cpp:1038`). Only the futility condition has `!in_check` (`:1042`); the immediately following history and SEE prunes do not (`:1047–1048`). At a qualifying material node, after one non-mate evasion has been searched, a later quiet nonchecking legal evasion can therefore be discarded for sufficiently negative history. The MovePicker's evasion stage itself ignores `skip_quiets` (`:404–414`), so merely disabling late-move skipping would not remove this separate history gate. This is main-search selectivity, not qsearch check generation, extension or TT work.

**Hypothesis:** ordinary quiet-move history is an unreliable reason to discard a forced defensive move; exempting only quiet evasions from history pruning could recover defenses. This has no demonstrated tactical witness or Elo result yet.

**Minimal counterfactual:** count actual history-pruned quiet evasions and retain the first bounded set of exact FEN/history/window/depth witnesses. Replay each through the same node with only that history prune disabled, keeping SEE, LMR, move ordering and all other rules unchanged. A legal defensive improvement against a deeper reference justifies a strength test; zero occurrences or no useful counterexample deprioritizes it. Do not broadly disable all pruning in check.

## 3. Add a conditional512-bit NNUE output kernel

**Countable source opportunity:** `src/nnue.cpp:171–185` selects the256-bit AVX2 implementation even on targets with AVX-512; there is no explicit512-bit branch. For16 hidden units it expresses8 vector loads and20 clamp/multiply/add operations. An equivalent16-lane512-bit path expresses4 loads and10 operations with unchanged256-byte input/weight traffic. This is a source operation count, not measured instruction throughput or whole-engine speed. The existing16-lane accumulation/final ordered sum (`:164–169` and `:211–214`) provides an association-preserving route without retraining.

**Limits/test:** no gain to the current `-march=x86-64-v3` hosted build. Only pursue after confirming a qualified AVX-512 target; use unaligned512-bit loads unless stronger alignment is proved (weights are only32-byte aligned at`:49`). First require bitwise outputs/lane parity against AVX2 on clipping endpoints and reachable accumulators, then inspect emitted code and count output-layer calls. Preserve `-ffp-contract=off` and lane/final-add order. A calibrated target-specific kernel/whole-engine test comes later; no small/shared-host timing rerun is authorized by this report.

Startup conversion/initialization is outside this per-node triage.

## Source identity

- `src/search.cpp` SHA256 `e766f20fb1fe21262b8ba45f46987fee949340f9af0f92ec296db5c158028bad`.
- `src/eval.cpp` SHA256 `05f23be48f04149e1ab0b6988160928a64a5a193e5b6d472ec5156cf0245bd1a`.
- `src/nnue.cpp` SHA256 `86aec39feecf029e73510e7e5fadf9e9878c94744f0380c4149edf04da02cdcd`.
