# Opt-in SMP node-accounting regressions

`FORGE_FIX_SMP_NODE_RESET=1` clears every published worker counter synchronously
before launching workers. Default 0 retains the lock behavior. This addresses
previous-search node totals being charged to a new search while a helper has
not started. It does not make multi-thread node budgets exact.

On Linux with GCC 14:

```sh
tests/run_smp_nodes.sh /tmp/smp-reset -DFORGE_FIX_SMP_NODE_RESET=1
```

The test first obtains worker pointers through the existing Worker test friend,
then seeds a helper with 1,000,000 previous-search nodes. Linker wrappers hold
that helper before Worker::search until the controller joins it, making the
schedule deterministic. Main must consume its fresh 100-node budget. With the
switch disabled, the test must fail with main=0 and returned=1000000.

Static libstdc++ is required so linker wrapping intercepts its pthread calls.
The harness explicitly verifies that the helper creation was intercepted.
No test hook is added to production code. These focused tests do not replace
scripts/check_pins.sh, legality tests, or native engine-strength testing.

## Final totals after joining helpers

`FORGE_FIX_SMP_FINAL_NODES=1` replaces the returned `SearchInfo.nodes` with the
sum of the workers' final counters after all helpers join. Default 0 retains
the earlier main-worker snapshot. Iterative UCI info lines remain live samples.

```sh
SMP_NODES_FINAL=1 tests/run_smp_nodes.sh /tmp/smp-final \
  -DFORGE_FIX_SMP_NODE_RESET=1 -DFORGE_FIX_SMP_FINAL_NODES=1
/tmp/smp-final # also checks the stale-counter case
```

The final-total test holds the helper until join, then clears the shared stop
flag through the existing test friend so the helper performs a real depth-one
search before returning. This deliberately models tail work after the main
snapshot without relying on a scheduler race. This is a test-only cancellation
intervention, not a claim that a blocked production helper normally ignores
stop. On the old accounting path: main=21, returned=21, final=42. With the final
accounting switch on: returned=42, equal to the sum after joining.
