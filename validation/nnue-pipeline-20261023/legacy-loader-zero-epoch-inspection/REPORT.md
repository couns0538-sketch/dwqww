# Legacy C++ zero-epoch round-trip: blocked

The actual unchanged `tools/tune/nnue_train.cpp` cannot export at `--epochs 0`. Both binary saving and include export occur only inside the epoch loop (lines 318, 358–364). The unconditional final `wrote` message at line 369 does not establish that either file exists.

The pilot Python residual binary and include exist and their exact hashes and sizes are preserved in `RESULT.json`. Source inspection is complete. Per the assigned stop condition, no compiler, loader execution, substitute training epoch, source modification, or Git action was performed. Therefore this checkpoint does **not** verify actual C++ loader acceptance or round-trip equivalence.

Next action: use a separately scoped read-only loader harness or add and validate an explicit export-only mode in a later task. Do not treat a zero-epoch exit code or the unconditional message as export evidence.
