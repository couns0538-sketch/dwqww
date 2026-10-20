# Correction-history residual-update ablation: internal arithmetic protocol

Frozen engine source: `47f0560221d986e41a309853e1295c557fcf5bf6` (Forge 6.4.17). This is one independent search ablation, not a demonstrated correctness repair or strength improvement.

The only proposed engine change is the assignment inside `Worker::update_correction`:

```diff
-        entry = std::clamp((entry * (256 - weight) + diff * weight) / 256, -CorrectionLimit, CorrectionLimit);
+        entry = std::clamp(entry + diff * weight / 256, -CorrectionLimit, CorrectionLimit);
```

Keep both table keys, the material coefficient (100 in the candidate), caller guards, depth weight, diff clamp, entry clamp, and all other search/evaluation/network code unchanged. Do not implement simultaneously a raw-eval target, table renormalization, gain retune, clamp retune, or extra table.

## Scope and stopping rule

Export exact tracked `src/` and `include/` from the frozen revision. Compile one driver against the actual complete core, using the existing `SearcherTestProbe` friendship to call the real `Worker::corrected_eval` and `Worker::update_correction` and inspect their tables. The baseline export is unchanged; the candidate export differs in exactly the assignment above. No copied correction implementation serves as the system under test. No chess matches, engine search workload, speed measurement, Git mutation, production edit, or frozen-package edit is authorized here.

Finite checks, selected before building:

- One-step signed updates, depth 0/14/15/100, positive/negative residuals and the ±8cp diff clip.
- Existing entry clamp endpoints, deliberately seeded endpoint states, and output mate-bound clamp.
- Signed integer division and zero-residual decay versus retention.
- Material weight 0 isolates one table; 100 exercises both. Nondefault 33 only verifies scaling/rounding; it is not a candidate tuning change.
- Repeated fixed raw=100, target raw±6, depth15, 4096 updates. Ideal integer endpoints: one-table EMA ±768/±3cp versus increment ±1536/±6cp; equal two-table EMA ±512 each/±4cp total versus increment ±768 each/±6cp total.
- Repeated large fixed residuals, demonstrating current effective range and the unchanged clamp's larger reachable range after the proposed change.
- Two FENs with equal material and distinct pawn indices: observe material-table contamination across keys, one opposite-side FEN for side separation, and preseeded unequal table values for joint-residual behavior.

Save selected iteration states and raw pass/fail output. The baseline's failure of the requested incremental contract is expected RED evidence of the difference, not a failed correctness test. The candidate must pass that contract and shared arithmetic invariants. Stop after Release and targeted ASan/UBSan builds of both cores and these checks; no parameter sweep or timing rerun.

## Interpretation

The current EMA may provide useful regularization. Search results include selected bounds and aliased tables, so closer agreement with a constant synthetic target does not establish better chess evaluation or Elo. Removing decay also expands reachable corrections from approximately ±8cp/table to the existing ±32cp/table clamp; this is part of the one-line ablation and must be carried into any strength interpretation. An implementation recommendation is conditional on these arithmetic checks and fresh full regression/strength gates owned by the parent task.
