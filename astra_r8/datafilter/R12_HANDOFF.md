# R12 continuation constraints from Couns — UNPROVEN

R12 must start from the **final reviewed tip of `astra-r8-datafilter`**, at
`d080df79142d5c61367d5eaab6355cf44876a6da` or later. The final tip is pending the
authorized R8 review hour; do not substitute `e526fc12` or treat d080df79 as
the final reviewed tip. This document records the handoff; R8 changes no engine.

The only accepted lock is `forge_ltopgo_x_al1s198_v23.exe`, SHA256
`fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072`.
Threads=1 and Hash=16:

| Check | Expected nodes |
|---|---:|
| bench d11 | 312866 |
| bench d13 | 862329 |
| bench d16 | 3024920 |
| bench d20 | 12389307 |
| bench d22 | 34048354 |
| startpos perft d5 | 4865609 |
| canonical Kiwipete perft d5 | 193690690 |

The previously supplied alternative three-number bench sequence is invalid.
A search of R8 tools/evidence and saved engine skills on 2026-11-03 found no
checks using it. Existing native R8 checks already use all five correct bench
pins above. Full startpos/Kiwipete d5 confirmation will run when a compute slot
is free, without interfering with the active source audits or crew processes.
Any R12 or external check that used rejected pins must be rerun; R8 cannot
certify uninspected external checks.

Keep D: at or above 50 GB free and C: above 50 GB. Preserve, without moving or
deleting, `C:/astra8_data/extension3h_20261103/handoff_v7/`, including manifest
SHA256 `52f39e0ceeb6fc6c63422514296b928b308ede862754e8d69addde1aa44fc720`.
That manifest hash was rechecked after the correction. A later handoff refresh
must use a new directory and retain v7 as evidence.

`D:/grok-pc-data/dwqww/astra8_data/holdout_cleared/metadata.jsonl` **is meant to
be byte-identical** to `records.jsonl` in the same directory. The explicit
holdout split writer writes the same retained JSONL line to both streams. They
contain complete normalized records and aligned metadata, with the same order,
999,953 rows and 315,036,094 bytes. Both recorded SHA256 values are
`0e73a87c2e1af035aed34f51fdd74daefc05833ce133f254845f09f23aeb5dce`.
The user's `aa3e9272` is a shortened MD5 identifier, not a full MD5 checksum.
Fresh full hashes will be recorded when a compute slot is free. This contract
is specific to normalized JSONL; converter binary REC and JSONL sidecars have
different formats and are not byte-identical.

No strength claim follows from these checks. Engine NNUE owns training; Engine
QA owns separate FD3A5190 UHO, 8moves_v3 and WAC300 qualification. UNPROVEN.
