# f023 completed proof, failed process exit, and minimal diagnostic preparation

The f023 controller outcome remains **FAIL**: watchdog150.33s, child return
code-15 (root observed outer status241). The child completed its mathematical
work and wrote a complete result; that does not override the failed process
exit. Originals, including the child PASS string, remain byte-for-byte intact.

Actual completed work includes Torch2.4.1+cpu import, bucket1 initialization/
forward/export identity, three CPU Adam steps on192 synthetic training rows,
and a512-row synthetic holdout check. Losses were
0.05097170174121857 / 0.04247596859931946 / 0.05361563339829445;
holdout MSE was0.04203268885612488 then0.04203213378787041. The replicated8
Torch maximum logit difference was1.1920928955078125e-7 within its1e-5 tolerance.
These are bounded smoke facts, not training-gain, full50k, real013014, native1M,
Std/null-pruning or strength results.

Independent verification now covers all six gzip compressed and decoded byte
hashes/sizes, using both Python gzip and GNU gzip. NPZ SHA256/ZIP CRC and all
eight finite float32 arrays verify. Legacy/one raw binary exports equal the
checkpoint's before-state; the trained8 raw binary equals its after-state.
Changed elements are189919 FT weights,256 FT biases,2874 output weights and6
output biases. No Torch, archive-library reload or training was used for this
artifact audit. Reports retain full hashes and array shapes.

The complete result and byte-identical regular-file stdout were last written
at14:04:29.970464UTC; controller receipt at14:04:31.905004UTC. The work therefore
finished approximately148.398s into its150s allowance. At most1.935s remained
for natural exit, and SIGTERM preceded the receipt write. A reproducible
shutdown hang is **not established**. Ordinary teardown just exceeding the
remaining margin and a finalizer stall remain distinguishable hypotheses.
No original per-thread/proc capture exists. Stdout/stderr were regular files;
there is no source-supported pipe-backpressure explanation.

Source confirms that the sealed fd was closed, temporary raw exports removed,
artifact/source checks completed and _real_probe returned before JSON/print.
Library mappings may remain until process exit. Root waited/reaped the signaled
child, releasing its mappings/resources. No disk library was restored; normal
environment import remains unready. The original ordinary-import RED and f022
loader failure are retained.

The controller's archive_contents_read:false was static build_plan metadata.
It is not a claim about child I/O: the child verified/decoded the full pinned
archive/raw bytes and seals15. The derived receipt explains these scopes and
does not edit the original field.

The new diagnostic is prepared only. **Do not execute without a new root grant
after all S26 timing closes.** Its default case is import plus two-element CPU
autograd; it does not rerun S09 models, data, exports or192/512 training work.
Separate import-only and tiny optimizer cases are available only if explicitly
requested later; there is no automatic case matrix.

Preregistered limits are90s work and150s total. A child SIGALRM requests ordinary
Python failure handling, and the external observer also enforces90s if no
MAIN_RETURN/WORK_FAILED marker exists. Deferred signal delivery inside native
loading cannot silently extend work. Such a cutoff is work-budget failure,
not evidence of a shutdown stall. First forced TERM is148s, KILL by150s;
default usable natural-exit reserve is58s. At least30 usable seconds are
required before drawing a shutdown observation. There is no os._exit or
deadline increase. Observer errors always terminate and reap only its child.

Evidence consists of flushed/fsynced monotonic+wall JSONL milestones, separate
preload/import/thread-config/autograd markers, before/after Python atexit
markers, periodic10s faulthandler traces and owned /proc status/task/wchan
snapshots. The atexit markers bracket registered Python callbacks, not all C++
finalization. Faulthandler gives Python stacks and introduces one diagnostic
watchdog thread; thread counts alone do not identify a culprit. Kernel-stack
permission failures are recorded, never escalated. No diagnostic signal is sent
to an unregistered handler during late interpreter teardown.

Both stdout/stderr remain regular files. The observer rereads the final journal
after reaping so a fast clean exit cannot lose MAIN_RETURN. Its clock starts
before child spawn. Work completion, ordinary process exit and overall outcome
are recorded separately. Source/helper/dependency hashes and child-only loader
environment are checked; no package or host setting is changed.

The exact plan is in forge_sol_S09_shutdown_preregistered_plan_20261026.json.
Fourteen public-Python protocol tests pass, including ordinary toy exit/atexit
markers, external work cutoff, owned-child cleanup after observer I/O error,
proc disappearance, final-journal timing, TERM-margin accounting and refusal
of plan/toy flags that could otherwise be silently ignored. These
tests load no Torch or library archive. Actual diagnostic execution remains
UNVERIFIED and pending the new root grant.
