# S09 actual-f006 full synthetic holdout proof — prepared 2026-10-26

This is source preparation, not a native/Torch result. No archive, private Torch,
engine, training, GPU, Git or network operation was executed by this preparation.
The four source/layout/input guards pass; their original logs are retained.

The distinct question is full50k heldout MSE for the actual supplied f006 network
and its replicated8-head counterpart, using unchanged v3b data loading, targets
and the candidate trainer forward. The original failed full export/training
probe stays failed. This script neither retries that work nor exports/trains a
network. It reuses the separately successful minimal shutdown diagnostic's
hash-pinned sealed-library loader and normal-exit observation implementation.

The f006 include is parsed through the existing S09 converter and its unchanged
step1 parser. No FPOS reader/include parser was rewritten. Weight layout inverts
the original export: W1 input-major is transposed into torch [256,768]; integer
storage /4096 remains float32. Actual f006 ranges were read as w1[-12011,8322],
b1[-6528,4701], w2[-16778,15131], b2[165,165], all within the trainer's QAT clamp.

Both models load every parameter from that same actual include. All50000 rows
of the supplied synthetic h000 sample are evaluated in512-row batches, including
the336-row tail. Reported metrics are onehead MSE, replicated8-head MSE and
HCE-only MSE against unchanged targets at k2.25/blend0.6. A first-batch changed
bias control must affect every512 logit. One-vs8 logit tolerance is1e-5; this is
Torch parity, not native bit equality. No training improvement is claimed.

The source pins original/candidate trainer, net, converter, parser and sample
hashes before and after. Outputs are NEW descendants of the existing /tmp S09
native root. Child-only loader/thread limits/CUDA visibility are configured;
ordinary private Torch remains unavailable outside the owning loader process.
Work180s, hard240s reserve58s before first TERM. PASS requires normal rc0 with
all50000 rows, no forced stop, no remaining owned process group, unchanged
inputs, and conservatively summed parent/child peak RSS at most4GiB. Per-process
address space is capped4GiB. Original diagnostic process/proc/event/faulthandler
records are preserved. No shutdown-hang conclusion is inferred from timeout.

Exact command after the parent grants the runtime window (CPU1 must be free):

```sh
taskset -c 1 nice -n 19 python -B forge_sol_S09_full_holdout_20261026.py --execute --root-authorized-window ROOT_GRANT_REFERENCE --out /tmp/forge_sol_S09_native_20261026/full50k_actual_f006_holdout_once_20261026
```

UNVERIFIED: actual full50k Torch execution/loss/normal exit. Real holdouts013/014
are absent; this sample cannot substitute for their generalization evidence.
No new trained8-head net exists, no crew gate or GPU work was touched, and no
playing strength claim is made.
