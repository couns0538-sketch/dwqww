---
name: native-experiment-integrity
description: Use when freezing, recovering, resuming, auditing, or accepting a native chess-engine experiment, especially fastchess SPRT, paired PGNs, interrupted concurrent matches, changed binaries or networks, missing checkpoints, or claimed Elo gains. Not for ordinary chess-position analysis.
---

# Native Experiment Integrity

Preserve file identity, experiment identity, and real native decisions. Use `validate-chess-engine` for engine correctness and strength interpretation. Read [forge-protocol.md](references/forge-protocol.md) for the user's TT-tag protocol; do not silently apply it to unrelated experiments.

## Freeze before execution

Read current source/state and actual owned jobs. Recover baseline/candidate revisions, dirty patches, binaries, networks, runner/version, opening order, settings, hardware allocation, and the preregistration. Freeze all identities before starting. A changed binary, network, runner, source, setting, or protocol requires a separately identified test, not a statistical continuation.

Use `python scripts/verify_frozen.py MANIFEST.json --root ARTIFACT_DIRECTORY` as a read-only file-identity check. Follow [frozen-files.md](references/frozen-files.md). Resolve the script relative to this skill. A successful hash check does not authenticate the supplied manifest, validate PGNs, prove a native decision, or authorize resumption.

## Decide whether recovery permits continuation

| Observed evidence | Required action |
| --- | --- |
| An owned foreground experiment is live | Inspect it; do not duplicate it or overlap CPU measurements. |
| Native H0 or H1 already occurred | Preserve the terminal result. Never resume a decided test. |
| Naturally completed prefix, unchanged identities/settings, verified complete pairs and native counts | Resume only through the installed runner's verified cumulative-round semantics. |
| Interrupted concurrent match, orphan games, unverified prefix, or inconsistent counts | Preserve all evidence. Do not use routine SIGINT/native-count resume. |
| Frozen bytes missing or mismatching | Recover exact bytes or start a separately preregistered test. |
| Budget exhausted without a native decision | Record inconclusive; do not manufacture a pass. |

Inspect the installed runner's help/source for exact flags and checkpoint semantics. Do not guess an API or reconstruct native state from game totals.

## Validate results and preserve evidence

Verify paired openings, color reversal, game completion, unique pair indices, result/termination tags, and legal moves. Reconcile original PGNs against native W/D/L and pentanomial counts using version-matched tooling. Keep native LLR, bounds, and terminal output. Never replace a native SPRT decision with a custom calculation. Keep real terminal decisions even when ancillary integrity checks fail; report both and never resume to repair the statistics.

Accept a stronger-engine claim only with the required preregistered native H1 and validated evidence. Correctness passes, positive short scores, faster NPS, or fixed-node wins are not that acceptance. Preserve H0, inconclusive runs, timeouts, crashes, and orphans.

Save immutable source/config snapshots, stdout/stderr, PGNs, UCI traces, native checkpoints, manifests, commands, and reviews to the authorized branch with a checked expected head. Verify saved links. For archives, verify restored bytes and retain restoration instructions. Report separate correctness, speed, strength, and persistence verdicts.
