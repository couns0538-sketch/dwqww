# Explicit bilateral cutoff continuation, decision 0016

READY. New immutable metadata only; no native execution, engine-source change, Git change, root-state write, or alteration of older evidence was performed during preparation.

Decision `6f52b2dfe18d289a201e3a06fd756152ba28a539`, SHA `1ca13976a15e8e8b7dbd994aeca5176d8158a18ff71db87422095adf83d6c1b2`, explicitly authorizes both candidate and reference cutoff events when the driver supplied less than 250 ms, sent its own SIGTERM, and reaped that signal or exit 0. It extends Job A to 2026-11-15 04:20 UTC. The actual 2000-cycle diagnostic AUDIT is pinned at SHA `53a478edfe391e56004d1b1a5c08d21c7673d9fe5b7c08f72358484257f887a8`; its declaration, command and process result are pinned too.

The supplemental classifier preserves the original raw `decision0012`, occurrence counts and escalation flag. It classifies the two reference cutoffs and candidate global85545 individually, retaining budgets, measured times, exit/signal and full evidence hashes. Only excluded initial pairs qualify. A partner interrupted by the native batch deadline may be incomplete; an actual search error outside that budget, diagnostic, unsolicited signal, SIGKILL, full-250-ms timeout, other fault, or difference outside known same-clock position036729 remains blocking. Every unclassified occurrence remains blocking. No repeat diagnostic is requested for the explicitly authorized measured sub250 class. Final narrow source attribution remains a separate acceptance step.

Root commands:

```text
node /workspace/work/parity-reference-continuation-v6/control.mjs migrate final /workspace/work/parity-run/equality-final-v5/stage.txt
node /workspace/work/parity-reference-continuation-v6/control.mjs prepare final
node /workspace/work/parity-reference-continuation-v6/control.mjs run final S2-0006 --execute-authorized
node /workspace/work/parity-reference-continuation-v6/control.mjs audit final S2-0006
node /workspace/work/parity-reference-continuation-v6/record-equality.mjs final S2-0006
```

All five existing receipts are inherited unchanged. The next batch resumes the original shard cursors and seed1449540006. Candidate, reference, native driver, source/build pins, corpus, runtime defaults and per-command/batch bounds remain unchanged. Only metadata namespace, supplemental explicit policy and absolute deadline change. No binary bytes are included in migration publication snapshots.

Validation actually completed:18 policy checks, five syntax checks, read-only five-receipt migration preview, and full cumulative re-audit of S2-0001 through S2-0005. Every original audit field matches; raw candidate count2, raw escalationtrue and all three operational findings remain. Supplementary continuation is true and effective escalation false under decision0016. Actual commands/outputs are retained in adjacent command files. No engine coverage is claimed for these metadata tests.

Frozen hashes:

- control.mjs `1b89ff7cdb546f0f32544443a252080e884039c4d67828b00bdf6ac8a546757b`
- cutoff-reference.mjs `d67c1ecc8afe6afd60e6a4a6532ddb493911030cd756d3b72c9aa0733d1382f6`
- record-equality.mjs `8dde48bab7b0c1e825be7daa8f7df0fec0948d828bfe4f5d92c9c3b5cea9925b`
