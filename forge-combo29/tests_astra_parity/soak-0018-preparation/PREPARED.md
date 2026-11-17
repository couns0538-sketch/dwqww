# 0018 sanitizer continuation: metadata only

Fable0018 authorizes the unaffected ASan groups immediately, and changes future ordinary TSan searches to `go nodes 20000`. The soft half remains `go softnodes 2500` under the already-approved SMP label rule. Decision commit fe59dc3ab072480f7360f0b356ff01a900d2ab35; exact file SHA256 a85053e51b66fb82cbc2033acf27d5e4cb83f22d64938c430870a15eeaf7fe3b. This is a new protocol; no old acceptance or evidence is rewritten.

The native executable remains `/workspace/work/parity-softnodes-smp-preparation/softnodes_play_smp`, SHA256 ab599afccbdd999555c4ba30c32e41d94b6a32de9ea1b13ebf4ebcaae6bc3af7. Its parser, transport and oracle pins are unchanged. Both sanitizer binaries, all26 engine source/header/CMake pins and all16 sanitizer objects are unchanged. No native compilation or execution was needed or performed for this metadata-only continuation.

Root commands, after recorder readiness and independent review:

```text
node /workspace/work/parity-soak-0018-preparation/control.mjs declare d9a8587df8ad4d0ff1231632cb1ac72b590c04bf --freeze-authorized
node /workspace/work/parity-soak-0018-preparation/control.mjs run INDEX --execute-authorized
node /workspace/work/parity-soak-0018-preparation/audit.mjs INDEX
```

Required new root authorization: `continuation0018Resolution = {commit:"fe59dc3ab072480f7360f0b356ff01a900d2ab35",sha256:"a85053e51b66fb82cbc2033acf27d5e4cb83f22d64938c430870a15eeaf7fe3b",oldAuditsUnchanged:true}`. Root explicitly clears only the effective global stop under that decision. These tools never clear it or historical flags. The new controller does not wait for classification of the prior TSan timeouts before starting the first ASan waves.

Runtime directory `/workspace/work/parity-run/softnodes-0018-batches`; labels `continuation0018-c01-...` through c06; protocol `softnodes-0018-continuation`. Fresh seeds202611170101..202611170112 in the first cycle, plus1000 per cycle. Six cycles reserve72 batches, with12 distinct conditions. Relative waves [[1,7],[3,9],[0,6],[2,8],[4,10],[5],[11]], plus12 each cycle, prioritize the missing ASan nodes20000 groups. TSan indices4/5/10/11 now use nodes20000 and depth0; every ASan condition is unchanged. Earlier waves need passing recorded audits, same-wave reservations are atomic and aggregate engine Threads stay<=4. Existing sibling supervision and no-match-overlap rules remain.

Deadline04:20 UTC, target180seconds per batch, native420/outer440second bounds and475second launch margin are unchanged. The number72 is reserved inventory, not a completion requirement. Root records/checkpoints serially. Any new failed/incomplete audit blocks new launches; item3/4 findings also set the effective global stop.

The matching new recorder is `/workspace/work/parity-soak-0018-recording-preparation/record.mjs`. It uses `continuationPairedSoftnodesRows` / `continuationPairedSoftnodes` and corresponding validation/finalTree fields. The old SMP two clean T2 batches (148games/21436searches), older two clean T1 batches (108games/15514searches), and all failed batches remain separate. In particular, both old TSan depth9 failures retain zero clean credit pending diagnostic classification. This continuation does not run, modify or interpret the separately prepared0018 diagnostic, nor start Job C.

`FINAL-VALIDATION.txt` retains exact syntax/metadata-check commands and output; `*.diff.txt` records changes from the frozen SMP tools; `FROZEN-PINS.txt` fixes all new metadata identities. Previous native, tools, evidence, source, Git and root state remain untouched.
