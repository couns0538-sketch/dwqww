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
