# Independent application: cleanup and persistence failures

**Acceptance verdict: invalid attempt; fail closed. No accepted candidate gain or Elo conclusion.** The timeout already invalidates this strict protocol. An `OSError` while hashing partial stdout or writing `status-before-verdict.json` independently invalidates the attempt. An imminent deadline and a promising earlier candidate outcome do not change that verdict.

This is a documentation-only application of the supplied scenario. It does not execute or demonstrate engine behavior, collector cleanup, affinity restoration, parser correctness, match acceptance, or playing strength, and supplies no Elo proof.

## Required handling

Because spawning succeeded, bounded cleanup and reaping of the owned child or owned process group must run in an unconditional `finally` path. That path must be independent of hashing, assertions, and status-file writes, so either specified `OSError` cannot skip it. Attempt the appropriate bounded termination/escalation and reap operations for the owned workload; do not touch unrelated processes. Retain distinct cleanup actions, errors, and any observable post-cleanup final return code and group state.

Additional exceptions during cleanup or diagnostic persistence must not prevent the remaining feasible bounded cleanup/reaping attempts, and must not replace or erase the original timeout and hash/write failure. Capture each observable failure and preserve diagnostics wherever writable. If one status destination fails, retain the partial raw streams and any other successfully persisted evidence; report the persistence gap honestly. Do not claim that cleanup completed unless its actual observations support that claim.

Restore the caller's saved original affinity in an **outer `finally`**, regardless of hashing, status-writing, cleanup, or further persistence exceptions. Affinity restoration must not depend on a successful evidence write or successful child cleanup. If restoration itself fails, preserve that error wherever writable and leave restoration success explicitly unconfirmed. The reporting deadline does not waive these obligations. Bounded cleanup and evidence-finalization time must be reserved below the outer execution timeout; such headroom cannot guarantee survival after infrastructure loss.

## Facts and evidence

The supplied scenario establishes that the caller temporarily narrowed its affinity, successfully spawned an owned child, the child timed out, one of the two specified evidence operations raised `OSError`, and partial raw stream files remain. It does not establish that both evidence operations failed in the same attempt.

The original pre-verdict child return code, CPU use, and process-group state were never observed. Record each as **unknown**, with the reason that the original observation was absent. Unknown CPU use is not zero, a timeout does not establish a particular exit code, and group state cannot be inferred from later cleanup. The scenario supplies no numeric affinity masks, actual partial-stream contents, actual stream hashes, complete command/stdin, or actual cleanup results; do not invent them. Retain whatever command/stdin, raw bytes, and other facts are genuinely available. A failed or uncomputed stream hash is explicitly unavailable, not a fabricated digest.

Keep original pre-verdict observations and gaps separate from post-cleanup observations, cleanup actions/errors, and any later final return code/group state. A later observation may describe that later state only. Preserve all attempted games and failed exchanges/logs; do not discard the timeout, trim faulty games, pool interrupted attempts, or restart repeatedly until H1 appears.

## Consequences and future validation

Successful later cleanup does not rescue this attempt. A parser replay with an assumed exit code cannot recover the missing original process status or rescue this attempt. A later successful replay, rerun, or passing experiment also cannot retroactively validate it. Any future result is a separately identified experiment with its own evidence and limits.

Investigate the timeout and evidence/persistence failures first. Before freezing a repaired runner, fault-inject **both** hashing failures and status-write failures after successful spawn and verify, using actual observations, that each path still attempts bounded owned-child/group cleanup and reaping and restores the saved caller affinity. Include additional cleanup/persistence exceptions in these controls, retain the failures and pre-verdict/post-cleanup observations separately, and reserve cleanup/finalization headroom. This document does not perform those tests.

Preregister a fresh validation run with a new evidence location after investigating failures. Freeze complete source/build provenance, binary/runner/input hashes, settings, resource allocation, openings, and stopping rule. Validate readiness and acceptance parsers against byte-exact captures from the frozen producer and intended transport, including malformed/warning/stderr/nonzero-exit controls. Require the complete source/build evidence before readiness processes; missing evidence fails closed.

Use fresh eligible unique openings, excluding earlier calibration/pilot/test selections. Pass normal complete deterministic A/A calibration before A/B. For the pinned Fastchess runner described by the skill, use serial native SPRT; preserve every attempt and audit complete unique color-swapped pairs, the exact frozen opening prefix, counts, input/proof/build hashes, and native acceptance. Only a separately valid run with exactly one explicit native H1, a finite final LLR, and all audits passing can support gain under its frozen protocol. Fixed-node results do not establish equal-clock strength or broader hardware/opponent claims.

## Guidance identity and observed file actions

- Guidance read: `/workspace/dwqww/.agents/skills/validating-chess-strength/SKILL.md`.
- SHA-256 of the exact bytes read: `f1e59d7b26cab2d25c57a018a49d7809b4b34b5830c990343194a0e90a242e4a`.
- Observed task-content read action: exactly one `Path.read_bytes()` call for that absolute path; the resulting bytes were decoded for reading and hashed in memory.
- No scenario expected answers, previous applications, old skill, parent task files, source files, raw streams, or experiment artifacts were read. Claims about this scenario come from the supplied task text, not observed process telemetry.
- Created only this new Markdown file and its sibling `independent-application.json`. No engine, build, collector, match, affinity operation, process-management experiment, network request, or Git operation was performed. Documentation I/O used the tool execution facility.
