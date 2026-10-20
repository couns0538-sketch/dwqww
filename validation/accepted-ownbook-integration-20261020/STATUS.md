# Accepted-lineage OwnBook validation: complete and stable

The exact existing candidate 5101c2529d386b7c3a04ba9156a69ee34df6bb43 suppresses the external-book
leak reproduced on baseline 356e863dbd86d2ce24b8ee9486d7406f1d525480. No implementation was changed.
The only production difference is the existing one-line UCI OwnBook condition; the original
156-line candidate test was used byte-for-byte against all three builds.

| Profile | Existing CTests | Original OwnBook test | Disabled book, before/after toggle |
| --- | --- | --- | --- |
| Baseline Release |4/4 PASS|PASS with --expect-leak yes|true / true: leak reproduced|
| Candidate Release |4/4 PASS|PASS with --expect-leak no|false / false|
| Candidate ASan/UBSan |4/4 PASS|PASS with --expect-leak no|false / false|

All builds also selected external e2e4 with OwnBook enabled and bypassed the book for depth 2.
The shared one-entry fixture SHA256 is 584586429bc5c26dc8b4f439991cf0548d9474d4013be9950cef8dacdcda64ff.
Original test SHA256 is 220648e27b1a45af593174321a093c0947b4599b3fe315048f0f4001529f8588.
The independent read-only audit passed 807 checks without running engines or tests.
No phase failed, timed out or retried. Owned process groups were cleaned/reaped and no live
owned processes remain. Full source/binary/core/config identities were checked before/after;
Release baseline/candidate static cores are byte-identical. GCC 14.2.0, FORGE_NATIVE=OFF and
identical strict Release float flags were used; candidate sanitizer checks were fatal with leaks enabled.

Exact commands are in TESTCOMMANDS.json and TESTCOMMANDS.md. Source Git/tree/blob/mode/hash
manifests are baseline-source.json and candidate-source.json. Each *-attempt1 directory contains
separate command stdout/stderr, command/cleanup/identity records and ownbook-original raw_uci.log/result.json.
These are the original harness's directional text UCI transcripts, with engine stderr combined and CRLF
stripped by that unmodified harness; they are not byte-level process captures. All source/build trees remain
at /workspace/.cloud-setup/accepted-ownbook-{baseline,candidate}-{source,release,asan}, with baseline-asan unused.

This is new local accepted-lineage evidence, not recovery of inaccessible CI39446498263 raw artifacts
or transferred 17 proof. It supports the specific external Polyglot toggle/depth contract; moves are syntax
checked by the original script, not independently legality checked. No strength/speed claim follows.
No integration, branch/reset/source edit, Git mutation, merge or push was performed. Root owns the decision.
All evidence is now stable; no further engine or file-writing actions are planned.
