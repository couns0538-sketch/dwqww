---
name: improve-grokchess
description: Improve GrokChess and other UCI chess engines through source-grounded engineering. Use when asked to make GrokChess stronger, pursue Stockfish-level play, choose or implement search or NNUE improvements, continue experiments, or plan the next development cycle. Prioritize TypeScript/JavaScript GrokChess; adapt to Forge and other engines when requested.
---

# Improve GrokChess

Turn an authorized improvement request into a tested code change and a recoverable experiment. Optimize playing strength at the intended wall-clock time. Treat beating full-strength Stockfish as a research goal whose achievement requires direct match evidence.

## Establish the actual engine

1. Read repository instructions, the latest checkpoint, experiment index, and relevant source. Locate the complete matching source tree, build command, UCI entry point, network, and benchmarks. Identify source, dirty changes, binary/JavaScript, network, runtime, and opening-suite hashes.
2. Read [project-context.md](references/project-context.md). Treat historical facts as retrieval leads; let current explicit instructions and verified source determine this run. A patch archive or executable does not establish a complete source baseline. Recover available files before asking for missing source; never invent it.
3. Reproduce the current baseline and its relevant failure or profile. Preserve it separately. Keep authoritative TypeScript and generated JavaScript synchronized when both are present; follow a JavaScript-only task's restrictions.
4. Select the acceptance contract below. State the choice briefly and proceed with work already authorized. Do not require the user to approve routine local experiments again.

| Task | Required evidence | Companion skill |
| --- | --- | --- |
| Faster with unchanged behavior | Exact per-position search results and credible paired timing | `optimize-grokchess-speed` |
| Stronger search/evaluation/NNUE | Correctness plus a predeclared fastchess improvement test at equal time | `validate-chess-engine` |
| Correctness repair | Minimal failing reproduction, targeted fix, related regressions, and relevant strength follow-up | `validate-chess-engine` |

Do not impose an old node signature on an authorized strength change. Do not relax an exact-behavior contract because a candidate appears stronger or faster.

## Run the development cycle

1. Inspect the actual hot path and its callers. Consult [engineering-guide.md](references/engineering-guide.md) for search, state, evaluation, and JavaScript questions. For NNUE changes also read [gknn-contract.md](references/gknn-contract.md).
2. Rank a short list of hypotheses by likely equal-time benefit, evidence, cost, and risk. State the mechanism, affected code, predicted measurement, and result that would disprove each. Keep measured small gains, including roughly 3% speedups; do not invent a minimum Elo or speed threshold.
3. Implement the most promising bounded hypothesis in an isolated branch or copy. Preserve unrelated edits and accepted improvements. Make dependencies explicit; test components before combining them. Use a controlled ablation to isolate an interaction instead of removing entire pruning families to hide a symptom.
4. Use profiling, differential tests, and small match screens to decide which candidates justify more expensive testing. Change one idea at a time unless the components are inseparable. Stop a candidate early for a reproduced correctness failure or a clearly unfavorable screen; retain its evidence and revisit condition.
5. Obtain an independent source/diff review for substantial changes. Give reviewers the code and raw artifacts, not a desired verdict. Delegate separate investigations when available, isolate writes, and run timings without competing benchmark jobs. Respect the user's selected model; when model controls are exposed, GPT-6.1-sol with ultra reasoning is the user's preferred configuration. A skill cannot select unavailable models or change model weights.
6. Apply the selected acceptance gate. Mark the candidate **accepted**, **rejected**, **inconclusive**, or **blocked**, with separate correctness, speed, and strength findings. Match the claim to the test's purpose: a tolerated-loss non-regression PASS does not establish positive improvement. A bug fix may be correct while its strength effect remains unmeasured. Do not describe that as an Elo gain.
7. Checkpoint before risky operations, after each experiment, and before ending the session using [experiment-record.md](references/experiment-record.md). Continue useful authorized work within the active session; create actual automations only when requested and available. A skill does not itself run continuously.

## Finish with evidence and a next move

Return the code revision or artifact, what changed and why, exact tests and results, limits of the evidence, checkpoint location, and the next highest-value experiment. Save raw failures as well as successes. Never replace original fastchess PGNs/logs with reconstructed summaries.

Load references only for the current task. Resolve bundled script paths relative to this skill's directory, not the engine working directory. Use `node scripts/inspect_gknn.mjs PATH` to inspect a declared GKNN-v1 file; this checks structure, not inference or playing strength. Use [sources.md](references/sources.md) to find primary documentation and verify version-sensitive details.

