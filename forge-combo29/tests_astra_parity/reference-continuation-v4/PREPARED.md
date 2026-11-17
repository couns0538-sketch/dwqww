# Exact-reference continuation adapter v4

Prepared 2026-11-15 01:02 UTC. No engines run, no Git operations, no root-state writes, no prior file overwritten. This is a metadata/policy adapter only. **The later independent softnodes item-4 failure still stops all engine work; readiness of this adapter does not clear that stop.**

The adapter implements root's existing-authorization interpretation of Fable answer0012, “One event more on the reference changes nothing.” It recognizes only S2-0001 / worker1 / local3929 / attempt0 / reference: completed exact f1a1, mate2, 705nodes at depth9; total shutdown budget4ms; driver SIGTERM after its2ms graceful stage; reaped signal15 at3.014613ms. The event, all original counters, incomplete-pair exclusion, and v3 blocked audit/receipt remain unchanged. It is not described as a normal exit or a250ms hang.

`EXACT-REFERENCE-EXCEPTION.txt` pins the original stage, receipt, audit, config, summary, artifact manifest, worker JSONL/evidence and invoked v3 helper files. It stores the exact context and initial pair. `exact-reference.mjs` checks those hashes and the complete audited event before an internal replay of the old policy that excludes this single authorized operational occurrence from the blocking set. This replay never mutates published raw fields. All other faults and second-candidate escalation remain governed by the frozen old policy. Any unfamiliar forced reference event remains blocking.

`audit-all-differences.mjs` invokes the unchanged v3 aggregator and appends only `supplementalReferenceClassification` and `continuationDecision`. The original `decision0012.continuationAllowed=false`, `pureShutdownAllowanceOccurrence=false`, operational count1, signal15 and timing survive verbatim. This explicitly separates the original strict classifier from the new exact-event decision.

The controller is restricted to final-stage migration. It inherits the original S2-0001 receipt, unchanged and hashed, into a new `/workspace/work/parity-run/equality-final-v4/stage.txt`. It leaves the existing speed-v3 stage alone. Candidate, reference, native comparator, corpus, search settings,330-second batches, deadlines and source pins are unchanged. Future final-stage seeds/IDs continue at S2-0002 /1449540002. The original cursors are worker0=3591/21409 remaining; worker1=3929/21118; worker2=3577/21423; worker3=3967/21091. S2-0001 is included exactly once in each cumulative audit.

Root commands after the higher-priority stop is resolved:

```text
node /workspace/work/parity-reference-continuation-v4/control.mjs migrate final /workspace/work/parity-run/equality-final-v3/stage.txt
node /workspace/work/parity-reference-continuation-v4/control.mjs prepare final
node /workspace/work/parity-reference-continuation-v4/control.mjs run final S2-0002 --execute-authorized
node /workspace/work/parity-reference-continuation-v4/control.mjs audit final S2-0002
node /workspace/work/parity-reference-continuation-v4/record-equality.mjs final S2-0002
```

The run command retains the480-second remaining-job guard and the absolute02:19:40 deadline. Migration/prepare are metadata operations; no native continuation has been performed in preparation. Do not run the actual migration until root is ready to pin this version. The preview stage is preparation evidence only and is not a live declaration.

The compatible recorder is the prior recorder with final-v4 paths/imports and one extra `supplementalReferenceClassification` field in its state row/totals. It retains the original `operationalClassification` field, which still explains v3's blocked decision. It does not replace or re-record the existing S2-0001 row/package. After S2-0002, cumulative totals advance from the new audit and no earlier position is credited twice. Root must set the active batch correctly before recording and must wait for state-writing operations to finish before checkpointing.

Validation actually completed:15 in-memory policy tests; syntax checks of all five new/changed helpers; read-only migration preview; read-only whole S2-0001 re-audit. Every original audit field compared equal, 14,959 committed positions and one operational finding were retained, the old blocked decision stayed false, and the supplemental continuation decision became true. Second-candidate, crash, missing result, unrequested signal, SIGSEGV, unreaped status, diagnostic, changed FEN/hash/side, additional forced reference event, other partial fault and validation-error cases were rejected. Strict equality rejects score differences; final-corpus continuation leaves attribution pending. Detailed actual command/output records and `VALIDATION.txt` are adjacent. No engine coverage is claimed.

An independent peer inspected the implementation and separately reported nine read-only policy tests passing; its review also emphasized that the new softnodes training-label stop remains in force. This is an attributed peer result, not an additional native test.

Frozen implementation SHA256:

| File | SHA256 |
|---|---|
| control.mjs | ba10d775f73760b37e97ea8f3b330c17966788a4ac951b3d33096693a79723ca |
| policy.mjs | c8f25c2caff663fc3faefa76a868d54e6573e629b3430b96b1fb20a25875e58a |
| exact-reference.mjs | 9025290bdadffb235ce6806ab6d7f8fa8360b4d5bc57d67eb31c1e82f1ad8a19 |
| record-equality.mjs | c6444695564305cf42f17ceaa9d8b5be1d831049da66f20278e040e6e4847949 |
| audit-all-differences.mjs | c4ce23306617ae3679a6a8c6b7c5bed57d8aac164d5b301a4e459a4f68eec521 |

Publish helper sources only as inert text through the existing evidence packager. No executable or live script belongs in the Git branch.
