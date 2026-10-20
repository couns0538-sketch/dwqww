---
name: coordinate-chess-engines
description: Use when coordinating Forge, GrokChess, or related UCI engine development across GitHub and experiments, continuing an improvement run, reviewing Sol's progress in couns0538-sketch/dwqww, or selecting skills and plugins for a source-grounded engine task. Apply to development, validation, handoff, and recovery requests; not unrelated chess questions.
---

# Forge and GrokChess Coordinator

Coordinate the existing engineering skills; do not replace them. Optimize useful progress per run, not tool-call counts or the number of patches produced.

## Establish the run

Read the current request, repository instructions, available skill metadata, and prior checkpoint. Before engine work, inspect `couns0538-sketch/dwqww` through the available GitHub connector: latest commits, relevant branch heads, pull requests and diffs, experiments, tests, Actions runs, and checkpoints. Read [Sol-first review](references/sol-first-review.md) for the audit contract. Record exact SHAs and what could not be inspected. Treat historical reports as leads, not current evidence.

Identify what Sol actually changed from the diff and evidence. Distinguish reported results from independently reproduced results. Avoid duplicating an existing fix or overwriting collaborators' branches. When GitHub is blocked, record that limitation and use a verified recoverable local baseline; never describe a blocked inspection as completed.

## Select relevant capabilities automatically

Use available skills and plugins without requiring the user to name them again. Load only what materially helps the task. Follow [plugin routing](references/plugin-routing.md); discover live tool schemas instead of guessing actions.

| Task | Required engineering skill when available |
| --- | --- |
| Search, evaluation, NNUE, development choice | `improve-grokchess` |
| JavaScript speed with identical search behavior | `optimize-grokchess-speed` |
| Correctness, UCI, SMP, match statistics, Elo claims | `validate-chess-engine` |

Use applicable debugging, test-driven development, isolation, review, and verification skills. Treat CodeRabbit as an actual review only after a successful review execution. Create or improve a helper skill through `skill-creator` when a repeated gap warrants it; first inspect existing skills to avoid duplicates. Package and validate it. Record installation separately from creation.

## Complete one valuable bounded task

Choose the best feasible task using benefit, evidence, implementation cost, risk, and collaborator overlap. Prefer executing an existing unrun regression or integrating a tested fix into matching authoritative source over repeatedly inventing adjacent mock-only fixes. Record the acceptance contract before editing. Use an isolated copy or branch.

For correctness, reproduce the failure before repair and test the actual engine when feasible. For exact-speed work, preserve required per-position behavior, not merely aggregate nodes. For strength, use the project's predeclared equal-time fastchess SPRT gate. Keep credible small speed gains; do not turn NPS into Elo or budget exhaustion into a pass. Preserve failures and inconclusive ideas with revisit conditions. Respect current CPU, runtime, platform, source-only, and permission constraints.

## Preserve and report

Follow [checkpoints](references/checkpoints.md). Fill [the run record](assets/run-record.json) with real observations, leaving unavailable values null. Use `python scripts/checkpoint.py create STAGING OUTPUT.zip`, then `python scripts/checkpoint.py verify OUTPUT.zip`, resolving scripts from this skill's directory. Read the helper limitations first.

Report: Sol's measured progress; this run's change or validation; exact tests and limits; separate correctness/speed/strength verdicts; verified artifact or commit locations; next action. Re-read any claimed remote save. Do not claim a local package is installed, a report-only commit contains code, or a skill provides continuous execution. Respect approval gates; do not alter global permissions or schedules as a side effect.
