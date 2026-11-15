# Narrow reference-cutoff continuation v5

Prepared 2026-11-15 around01:31UTC. No engines, Git, production source, root state or prior evidence changed. The v3 and v4 blocked audits/receipts remain intact.

This is root's narrowly defined interpretation of Fable0012 (“One event more on the reference changes nothing”) and the confirmed cutoff mechanism in decision55ddf61a. That later message approved the earlier exact event; this class rule is explicitly an interpretation for equivalent measured cutoff events, not a verbatim blanket authorization for reference signals or crashes.

Only an excluded partial **initial attempt0** qualifies. Both searches must have completed the same legal exact depth9 move/score/bound/nodes tuple. The candidate must have a clean shutdown and no faults. The reference must have only shutdown_timeouts1, quit attempted/sent, reaped exit_code−1/signal15 matching driver_sigterm=true, noSIGKILL, noerror/diagnostic/otherfault. Its total shutdown budget must be an integer strictlybetween0and250ms, with measured quit-to-exit at or after floor(3*budget/5) and no later than the total budget. Complete raw context/pair equality, native artifact hashes and existing source/build/binary pins are checked before classification.

Pinned native provenance shows this short budget is `max(1,min(250,remaining_deadline_ms))`; the transport's graceful fraction is3/5. No native comparator or timing rule was changed. The natural exit time without the driver's signal remains unknown.

Two actual events qualify in S2-0004's cumulative audit:

| Batch/index | Matching result | Total/graceful ms | Observed ms | Status |
|---|---|---|---|---|
| S2-0001/global15717 | f1a1,mate2,705nodes | 4/2 | 3.014613 | Reference driverSIGTERM; excluded pair |
| S2-0004/global68919 | g3f1,cp318,12391nodes | 8/4 | 5.197327 | Reference driverSIGTERM; excluded pair |

All raw counters/timings/signals and the original strict `decision0012` fields survive. `cutoffReferenceClassification` is supplemental. Its internal replay removes only qualifying operational findings from the old blocking-policy calculation; it does not erase them from any audit. Candidate occurrence counts and escalation remain unchanged, including the inherited original candidate occurrence. Unsolicited signals, SIGKILL, full-budget reference shutdowns, missing status, diagnostics, differing/incomplete searches and unrelated faults still block. A later matching cutoff is listed individually with hashes and measured fields.

Root commands:

```text
node /workspace/work/parity-reference-continuation-v5/control.mjs migrate final /workspace/work/parity-run/equality-final-v4/stage.txt
node /workspace/work/parity-reference-continuation-v5/control.mjs prepare final
node /workspace/work/parity-reference-continuation-v5/control.mjs run final S2-0005 --execute-authorized
node /workspace/work/parity-reference-continuation-v5/control.mjs audit final S2-0005
node /workspace/work/parity-reference-continuation-v5/record-equality.mjs final S2-0005
```

Migration inherits all4 distinct receipts (originalv3S2-0001 plusv4S2-0002/3/4). It continues unchanged cursors and seed1449540005, not a restart. New metadata is `equality-final-v5`; native batch/config directories stay the same. The native engine/reference/driver/corpus/source pins and02:19:40deadline remain fixed. A launch still requires480seconds remaining. No migration or engine continuation has been executed during preparation.

The recorder uses final-v5 metadata and adds `cutoffReferenceClassification` alongside preserved original policy fields. Existing state rows/packages remain unchanged; S2-0005 is the next new row. Binary bytes are never copied: the class declaration and stage retain and verify their hashes, while migration/publication snapshots include only text evidence. This distinction corrected a pre-freeze peer finding.

Validation actually completed:19 in-memory policy checks; five syntax checks; read-only migration preview; full cumulative S2-0001..4 re-audit. All original v3 audit fields match, two raw operational findings remain, candidate count remains1, and only supplemental continuation becomes allowed. The existing search difference still requires attribution. The first validation attempt mistakenly rejected a `.jsonl` text path in its snapshot-extension check; its script/output remain, and `validate-corrected.mjs` accepts `.jsonl`, matching the existing recorder. No native data or implementation policy was changed for that correction.

Independent peer review of the implementation reported11 read-only policy mutations passing and no blocking issue after the binary-copy correction. This is attributed review evidence; no engine coverage is implied.

Frozen implementation hashes:

- control.mjs: e4f3f3f09837674ec2494df24379b920b8edcad4ef2745747633ba3a96df0063
- cutoff-reference.mjs: badcb9a1dd3732a212ba9fb09379031e1f9ed27f3a23d29ae94cd656e4e46ec0
- record-equality.mjs:3b7d3a6aac27288cfe0f34c920df26e343a6c166f8b0b91a2f6dc22bdda24985

Actual commands/full outputs are in the adjacent `*.command.txt` and `VALIDATION.txt`; preview files are preparation evidence only. Helper sources have inert `.mjs.txt` twins for publication.
