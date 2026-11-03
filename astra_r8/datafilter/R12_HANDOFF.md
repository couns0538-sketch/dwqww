# R12 continuation constraints from Couns — UNPROVEN

R12 must start from the **final reviewed tip of `astra-r8-datafilter`**, at
`d080df79142d5c61367d5eaab6355cf44876a6da` or later. The final tip is pending the
authorized R8 review hour; do not substitute `e526fc12` or treat d080df79 as
the final reviewed tip. This document records the handoff; R8 changes no engine.

The tested implementation is `4a3d46710f88d5760e50738715f412f0704b3b6e`;
its reviewed packer and updated handoff are committed at
`cb3d24a14234625682567e29a3e5633366e4f253`. The final branch tip also contains
closed evidence and documentation. Resolve that final tip after the review-hour
closure; do not branch R12 directly from an earlier implementation checkpoint.
Current v9 manifest SHA256:
`c43e2498ec6256035d64e39f64093692b77239b585ed87eb5a74ba9361056291`.
The complete suite passes 564 tests and 11 subtests, and both CPU recipe
preflights pass. Final pack:32,548 files; Forge checker:95 references/18checks PASS.
No R12 engine implementation has been started by this data-only job.


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
accepted checks using it. Existing native R8 checks already use all five correct
bench pins above. Fresh exact-lock UCI verification completed at 07:04 UTC:
all five bench pins and both depth-5 perft counts PASS, engine exit zero.
Evidence: evidence/extension5h/closed_0728/lock_correction_v1/REPORT.json and
the adjacent original UCI stdin/stdout/stderr. Wrong numbers occur only in
deliberate rejection fixtures; they cannot qualify evidence.
Any R12 or external check that used rejected pins must be rerun; R8 cannot
certify uninspected external checks.

Keep D: at or above 50 GB free and C: above 50 GB. Preserve, without moving or
deleting, `C:/astra8_data/extension3h_20261103/handoff_v7/`, including manifest
SHA256 `52f39e0ceeb6fc6c63422514296b928b308ede862754e8d69addde1aa44fc720`.
The complete v7 tree was hashed before and after the corrected-lock/data check
and remained unchanged. A later handoff refresh must use a new directory and
retain v7 as evidence.

`D:/grok-pc-data/dwqww/astra8_data/holdout_cleared/metadata.jsonl` **is meant to
be byte-identical** to `records.jsonl` in the same directory. The explicit
holdout split writer writes the same retained JSONL line to both streams. They
contain complete normalized records and aligned metadata, with the same order,
999,953 rows and 315,036,094 bytes. Both recorded SHA256 values are
`0e73a87c2e1af035aed34f51fdd74daefc05833ce133f254845f09f23aeb5dce`.
Fresh direct byte comparison and full hashes PASS. Both full MD5 values are
`aa3e9272d686356ef6a9e25003c52546`; the user's `aa3e9272` is its shortened prefix.
This contract is specific to normalized JSONL; converter binary REC and JSONL
sidecars have different formats and are not byte-identical.

No strength claim follows from these checks. Engine NNUE owns training; Engine
QA owns separate FD3A5190 UHO, 8moves_v3 and WAC300 qualification. UNPROVEN.

The [closing preservation check](evidence/extension5h/final_pack_v2/post_pack_safety.json)
at 09:07 UTC repeats the direct JSONL byte comparison, confirms all full hashes,
checks all v7 files and the exact lock executable, and verifies no C/C++ or build
file changes since either recorded baseline. It confirms ancestry from d080df79.
This does not substitute for external R12 checks that used the rejected pins.
