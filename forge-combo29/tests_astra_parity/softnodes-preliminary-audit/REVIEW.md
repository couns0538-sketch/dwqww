# Independent preliminary softnodes audit

**Passed for this retained preliminary run.** It used Step 1 source c488e88fddc71a7ceadddb15270d3f62f6add8d9 and is excluded from final-tree soak totals. The equality workload was running concurrently; no timing or performance conclusion follows.

| Workload | Completed games | Searches | Result |
|---|---:|---:|---|
| Ordinary nodes 2000 | 1 | 132 | No recorded failure; game ended in mate |
| Softnodes 2500 | 1 | 87 | All requested label properties passed; game ended in insufficient material |

Exactly one complete pair was recorded, with no partial-pair counts. Soft X values sum to 478625; their mean is 5501.436781609195. Eight searches reached X >= 10000. Whole stdout/stderr scanning found no sanitizer/abort diagnostic. The child exited normally without an injected signal; observed quit-to-exit time was 24.851733 ms, below 100 ms.

The independent JavaScript auditor reconstructed each of 219 search blocks directly from submitted UCI commands and raw engine output. For every soft search it independently selected the last exact-score info line, checked bestmove against its first PV move, checked the 2500/mate/10000 condition, and verified the unique softnodes-X line appeared before bestmove. It then compared these independently derived values with CHECK and SUMMARY records. It did not rely on their Boolean claims.

The audit also verified exact command metadata and raw-output hashes, declared engine/harness/transport/build flags, all frozen oracle pins, the 26 source/header/CMake blobs against the declared commit, all recorded preliminary driver build inputs, the two game resets, warm per-move command sequence, both eight-ply openings, and every subsequent full move-history prefix. A separate static chess review confirms the two terminal classifications in terminal-review.md. Legal-move generation for all 219 moves was not rerun; it was performed by the pinned native harness during the recorded workload.

The actual audit command, exit status and full output are audit.command.txt, audit.stdout.txt and audit.stderr.txt. The full output includes all independently reconstructed search records and input hashes. The audit launched no engines, changed no root state or Git data, and did not alter the frozen final plan or harness.
