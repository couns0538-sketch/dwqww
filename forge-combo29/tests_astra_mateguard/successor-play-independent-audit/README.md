# Independent final successor self-play audit

PASS: all 12 planned batches match state and retained evidence. The verifier exited 0; actual invocation/exit are in `audit.command.txt`, full machine-readable report in `audit.stdout.txt`, and empty stderr in `audit.stderr.txt`. Exact verifier: `verify-soak.mjs`; identical inert publication copy: `verify-soak.mjs.txt`.

- Completed: 708 games and 97,576 searches, with 0 fault-aborted games, 0 engine faults, and 0 sanitizer diagnostics.
- ASAN/UBSAN: 8 batches, 687 games, 95,136 searches.
- TSan: 4 batches, 21 games, 2,440 searches.
- Verified all stdout/stderr hashes, reconstructed full-stream state hashes, actual recorded exit 0/signal null, single final SUMMARY and single CONFIG, six termination-counter sums plus fault-abort relation, plan seeds/argv/options, per-batch source/binary provenance, and both sanitizer build object/binary manifests.
- Scanned 77,347,433 bytes of full stdout/stderr; total stderr bytes: 0. Parsed and independently counted every one of the 97,576 TRIGGER records, validating options and contiguous game/ply progression against final summaries.

The first batch lacks explicit completedGames/faultAbortedGames convenience fields; its six termination counters independently establish 120 completed games and zero aborted games. Existing combined `.txt` logs intentionally contain a tail preview for large stdout; full sibling stdout files were read, hashed, and scanned. The first verifier attempt incorrectly assumed combined logs held full stdout; that audit assertion was corrected after reading command.mjs. Its exact verifier and failure outputs remain under `initial-*` for transparency. This was an audit assumption error, not an evidence failure.

No native binaries were launched, no engine/source/state/log files were modified, and no Git operations were performed. Verification outputs only were written under this directory. Exit status is checked against retained process metadata; terminated historical processes were not rerun. These totals describe completed workload, not speed, strength, or a bound on undiscovered bugs.
