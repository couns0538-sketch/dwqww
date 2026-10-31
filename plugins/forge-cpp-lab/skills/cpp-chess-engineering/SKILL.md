---
name: cpp-chess-engineering
description: Use when implementing, debugging, reviewing, profiling or researching C++ UCI chess engines such as Forge; investigating crashes, undefined behavior, SMP or TT races, search-state errors, NNUE arithmetic, compiler differences, unexplained bench changes or proposed playing-strength improvements. Not for playing chess or ordinary position advice.
---

# C++ Chess Engineering

Make one source-grounded improvement, test its actual behavior, preserve the evidence, then select the next useful experiment. A plugin supplies workflow and tools; it does not guarantee stronger play.

## Recover and route

Inspect the working tree, current accepted revision, open reviews and latest ledger before editing. Recover unfinished candidates rather than reverting to a remembered baseline. Read project instructions and record the current source/net hashes, build flags, platform, options and explicit pins. Never hardcode yesterday's Forge bench as today's lock.

Use existing `resume-engine-development`, `validate-chess-engine`, `native-experiment-integrity` and `preserve-chess-evidence` when available. Their ownership stays with the installed skills; this plugin adds C++ depth rather than copies. Discover callable tools: GitHub for exact revisions, Context7/vendor docs for APIs, CodeRabbit/Sonar for review, research connectors for primary sources. Use a connector only for a concrete question. Missing optional tools are not a reason to stop native work.

## Choose the smallest useful cycle

| Task | Read |
|---|---|
| Crash, illegal move, state bug, sanitizer failure | [C++ debugging](references/cpp-debugging.md) |
| SMP/TT race, publication, stop/resize problems | [Concurrency](references/concurrency.md) |
| NNUE, SIMD, profiling, exact speed | [Performance and NNUE](references/performance-nnue.md) |
| Search/evaluation idea or deep research | [Research](references/research.md) |
| Bench, platform, match decision or handoff | [Qualification](references/qualification.md) |

Reproduce the failure on the exact base. State a bounded hypothesis. For a bug fix, add a meaningful regression that fails first; for optimization/research, record baseline measurements and falsifiable acceptance criteria. Implement one isolated change, then run relevant native tests. Review real call sites and state ownership. Preserve existing accepted gains and original failed logs. Under an OFF-by-default contract, verify OFF identity on the candidate build itself; expose runtime options without racing worker threads. Keep uncertain work isolated.

For ideas, read original descriptions and author original code. Check dependency/include licenses; a permissive wrapper does not relicense compiled GPL contents. Do not copy other engines' code or tuned constants under an ideas-only contract.

Before claiming completion, separate correctness, measured speed and equal-time playing strength. A clean sanitizer run covers only executed paths; an NPS gain is not Elo. Research yields hypotheses, not accepted patches. Use [qualification](references/qualification.md) to distinguish incomplete evidence.

## Preserve and improve

Checkpoint to the authorized branch at the requested cadence, with exact commands, raw outputs, hashes, decisions and next actions. Verify publication. No force-push, accepted-branch replacement, production process interference, or unattended background promises. User task permissions still govern external writes and execution.

Run `python <this-skill>/scripts/check_evidence.py <record.json>` for read-only hash/pin checks; see [record format](references/evidence-format.md). Its PASS is an internal evidence check, not proof that a fix is correct or an SPRT succeeded.

When a recurring mistake appears, update this existing skill/reference or helper, add a reproducer and validate it; avoid duplicate routing skills. Report packaged, installed and behavior-tested states separately.
