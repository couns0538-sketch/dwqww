# Depth-64 acceptance amendment: fresh paired sanitizer workload

Prepared in the cloud on 2026-11-15. No engine was launched. The original `/workspace/work/parity-softnodes-preparation` source, binary, helpers, plan and evidence were retained unchanged and their original pins rechecked.

This is a new harness protocol under Fable's decision at `55ddf61a754ceffc4f940b847ad97143148d0434`, `forge-combo29/soak_all/FABLE_ANSWER_0013_0014_0015.md`. The exact decision text is adjacent, SHA256 `5e2d573b7e553ec49e84918bd1dfd6a28ccfd2ca7236b6834c3b041965945e2f`. The old item-4 contract finding remains recorded; no targeted engine reproduction or ten-repeat experiment was run during this preparation.

The sole runtime label-check change adds `(r.has_depth && r.depth == 64)` to item 4's alternatives, using the last complete exact-score line. The exact-line nodes requirement, item 2, item 3, threshold 2500 and hard-cap exception 10000 are unchanged. A bounded depth-64 line cannot replace an earlier exact line. The same frozen Board/bitboard oracle objects and measured UCI transport are used. Source and helper diffs with real diff output are adjacent.

The new native executable `softnodes_play_depth64` compiled successfully with the old recorded compiler arguments, changed only for the fresh source/output paths. Compile command, source/object pins and full stdout/stderr are in `compile.txt`; the native SHA256 is `ab59fdc0eabb037b417a5335dd2b7750fc077b1e0f087982f67782e8a9be602a`.

All 23 parser self-tests passed: the earlier 18 and five new cases covering depth 63 rejection, exact depth 64 acceptance, bounded depth 64 after exact depth 63, a later exact depth 63 replacing earlier exact depth 64, and depth 65 not being the specified exception. `parser-selftest.txt` retains the actual command and complete output. Both JavaScript helpers passed syntax checks. Five read-only consistency checks passed, including all twelve labels/seeds, decision pinning and unchanged original tools. These are preparation checks, not engine games or sanitizer coverage.

Root commands, after reviewing the amendment and the final source/build gates:

```text
node /workspace/work/parity-softnodes-depth64-preparation/control.mjs declare d9a8587df8ad4d0ff1231632cb1ac72b590c04bf --freeze-authorized
node /workspace/work/parity-softnodes-depth64-preparation/control.mjs run 0 --execute-authorized
node /workspace/work/parity-softnodes-depth64-preparation/audit.mjs 0
```

Use indices 0 through 11. Fresh labels start `depth64-`; seeds are 202611155101 through 202611155112. The unchanged twelve groups use the same final ASAN/UBSAN and TSan engines, 180-second pair-boundary targets, 420-second harness limit and 440-second outer limit. Launches require 475 seconds remaining before the unchanged Job A deadline, 2026-11-15 02:19:40 UTC.

Raw runs and the declaration are kept in `/workspace/work/parity-run/softnodes-depth64-batches`. The declaration pins the complete decision text, fresh plan/controller/auditor, native harness, source, engine binaries and objects. It does not clear any root stop state, change a previous declaration or alter the old failed batch. Root owns amendment classification, final-source validation, engine launches and report updates.

`FROZEN-PINS.txt` contains the final helper/native/source hashes. Only this documentation was added after that freeze. All controller/auditor executable sources also have inert `.mjs.txt` copies for text-only publication. The old recorder is not compatible with these new paths/pins; use the independently prepared depth-64 recorder supplied by the parent agent.
