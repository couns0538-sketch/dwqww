---
name: coordinate-chess-pipeline
description: Coordinate evidence-based chess-engine stages. Use for Forge or GrokChess hourly pipelines, independent tester handoffs, late investigator or strength findings, shared GitHub issues and branches, unavailable current builds, or automatically choosing relevant development plugins. Do not use for ordinary chess play or unrelated tasks.
---

# Coordinate Chess Pipeline

Resolve the current task against live records, choose the necessary specialist skills and connectors, and deliver one verified handoff. Do not turn a testing task into unauthorized engine development.

## Establish the run

Read the current request and repository instructions. Recover the role, authorized writes, repository, integration branch, cycle time, and evidence destination. For the user's Forge pipeline, read [the project profile](references/forge-profile.md). Use real UTC and timezone-offset timestamps; never manufacture the next scheduled time from the previous response.

Read the live integration SHA and substantive upstream reports through GitHub. A timestamped branch without a distinct report is not a completed stage. Record report time, inspection time, tested SHA, and freshness separately. Fall back to the last verified record when a stage is late; state its age and what could not be checked.

## Route work automatically

Read [tool routing](references/tool-routing.md). Load `validate-chess-engine` for independent checks, `optimize-grokchess-speed` for behavior-identical JS speed work, or `improve-grokchess` for authorized strength development. Add debugging, TDD, or review skills only where applicable. Use available connectors without requiring another user mention. Preserve existing permission boundaries.

## Recover the exact candidate

Pin source and binary provenance before testing. If a network route fails, inspect authorized connector artifacts, repository trees/blobs, and existing mounted sources. Verify completeness and hashes. Do not equate shell DNS failure with universal source unavailability, and do not bypass an authorization denial. Follow the bounded recovery procedure in the routing reference.

Prefer a useful current-candidate check over another unrelated archived-binary smoke test. If the candidate remains unavailable, report the concrete blocker, preserve current records, and run only a test that resolves a distinct remaining question. Do not manufacture an engine from incomplete snippets.

## Test and preserve

Use the specialist validation workflow for perft, UCI, regressions, sanitizers, deterministic bench, and preregistered equal-time paired fastchess SPRT. Keep current-candidate, archived-binary, hosted-CI, source-inspection, and synthetic-model evidence separate. A mock race is not a reproduced production race; well-formed UCI is not move-legality verification; inconclusive strength is not a release PASS.

Use `preserve-chess-evidence` when available for file integrity and match-ledger checks. Preserve failures, raw logs/PGNs, incomplete games, exact commands, source/binary/network/opening hashes, and runner checkpoints. Resume only after reconciling actual runner state; never rerun completed game slots or combine changed protocols.

## Publish and close

Use [the handoff contract](references/handoff.md). Publish only to the authorized shared issue or isolated testing branch. Read the result back and verify report content, commit, and links. An empty branch is not publication. If publication is denied, preserve the exact error and local report; do not circumvent controls or repeatedly retry denied writes.

Do not merge, reset, force-push, or overwrite the integration branch. Do not create or alter schedules merely because this skill ran. End with separate correctness/speed/strength decisions, freshness, actual coverage, artifact location, publication state, and one next useful action.

Use [scenario cases](references/scenarios.md) to review changes to this workflow. They are test specifications, not evidence of agent compliance.
