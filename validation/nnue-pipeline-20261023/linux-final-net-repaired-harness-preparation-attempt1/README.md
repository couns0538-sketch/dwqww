# Fresh Linux qualification with an explicitly repaired test harness

This is a separate variant of the previously reviewed runner/helper. Every original script, failed Release run and failed separate ASan/UBSan observation remains unchanged. Their depth8 start-position null-counter assertion was evaluation-dependent: the selected engine had zero attempts there but 45 attempts/25 cutoffs at the predefined depth10 diagnostic. Neither original suite is relabeled as passing.

Root repaired that coverage fixture with a controlled two-node TT/null-child test and checked complete original/new test translation units against both old and selected cores. Its NMP-disabled negative control fails the new assertion. Original positive/negative evidence is retained at `null-pruning-controlled-test-repair-attempt1`; its exact hashes are referenced by PINS.json. This variant does not modify search, evaluation, headers, tuning values or either network.

The new helper starts from original1ab Git blobs, verifies that clean commit `6e9622fd5be18e0155fc3ed5fcf6c4586705cca6` differs from1ab only in the selected include and that its include equals the explicit input. It then applies exactly `tests/tests.cpp` from `f4a1ed6be3921a024e0d876cac2433153a96c66c`, SHA256 `6dec8511d6107511cae182dc6169122b48b41e00c5033738f8b04ab027441dce`. Thus all74 source files must equal clean6e except that exact test file. Relative to1ab, the two explicit source deltas are weights and tests; production engine source remains exactly clean6e.

```bash
/workspace/.cloud-setup/nnue-pipeline-20261023-venv/bin/python -B \
  /workspace/forge-nnue-handoff-20261023/linux-final-net-repaired-harness-preparation-attempt1/run_linux_trial.py \
  --inc /workspace/forge-nnue-handoff-20261023/full-trained-net-freeze-attempt1/nnue_weights.inc \
  --sha256 a52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7 \
  --pins /workspace/forge-nnue-handoff-20261023/linux-final-net-repaired-harness-preparation-attempt1/PINS.json \
  --out /workspace/.cloud-setup/nnue-final-linux-a52efa5f7864-repaired-harness-attempt1
```

Root's immutable network selection receipt is `full-trained-net-freeze-attempt1/FREEZE.json`, SHA256 `3d945dc1f0e20d3469791eeb36b9ad5b23a1e70c87f6615703d0fda3442e211c`. The actual invocation wrapper must bind these inputs and both source commits before execution. The output directory must not exist; preserve every failure and never retry into an old directory.

The reviewed strict build/test/lifecycle gates remain unchanged: fresh complete Release and separate non-PIE RelWithDebInfo ASan/UBSan builds, exactly fourteen discovered/executed/passing non-skipped CTests each, source/tool/net byte and source-mode guards around commands, genuine first unknown new-network bench11 signature frozen before one repeat, owned process-group cleanup on errors, and all original commands/streams/return codes/build files retained. No old signature, automatic retry or test failure suppression is allowed.

The new result explicitly names the controlled test-harness repair. A pass would establish Linux correctness and deterministic bench behavior under that exact harness. It would not establish a speedup, Windows/Ryzen qualification, Elo gain, Stockfish result or promotion. The original acceptance baseline and default network remain unchanged.
