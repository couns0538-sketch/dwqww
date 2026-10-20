---
name: resume-engine-development
description: Use when continuing Forge, GrokChess, Aurora, or another UCI engine from a saved branch, checkpoint, interrupted experiment, hourly cycle, or handoff, especially after stale reports, missing binaries, blocked publication, or repeated diagnostic-only cycles. Not for unrelated programming tasks.
---

# Resume Engine Development

Turn a continuation request into progress on the unfinished engine experiment, with recoverable evidence. Use `improve-grokchess` and `validate-chess-engine` when available; use `optimize-grokchess-speed` for an exact-behavior speed contract.

## Establish the live state

1. Read repository instructions, current branch head, validation README, STATE, latest reports, exact relevant source, and retained raw logs. Resolve conflicts by inspecting evidence; never promote a previous chat summary into current state. For the user's Forge project, read [forge-profile.md](references/forge-profile.md).
2. Check the saved lease and actual owned jobs, including accessible CI jobs. An expired lease is not proof a process stopped; an empty local process list says nothing about another runner. Inspect ownership, commands, host, and allocation. Do not duplicate a live experiment or overlap CPU measurements. Resolve uncertain ownership before starting CPU work.
3. Identify the unfinished candidate, current blocking gate, previous completed checks, and exact next executable action. Keep existing gains and selective search. Do not start another hypothesis merely because the current one is difficult.

## Advance the experiment

4. Attempt authorized artifact/source recovery using [recovery.md](references/recovery.md). A missing local executable is not automatically an unavailable native-testing capability. Recover exact frozen bytes or rebuild a separately identified test. Never invent source, binaries, job status, or a successful build.
5. Prefer the pending native reproducer or test to another synthetic-only harness change. Repair tooling only for a demonstrated blocker to that test. If consecutive cycles produce no native progress, change the recovery/execution approach or report the precise blocker; do not relabel diagnostic maintenance as engine improvement.
6. Apply one source-grounded hypothesis, reproduce before repair, and run the relevant real suite. Keep correctness, speed, and playing-strength verdicts separate. Use `native-experiment-integrity` for frozen experiments, resume decisions, and native SPRT evidence when available. Retain negative and inconclusive findings.

## Checkpoint and report

7. Save source, commands, configs, hashes, raw output, PGNs/UCI traces, native checkpoints, reviews, and failures before long steps and before ending. Use a supported expected-head conditional GitHub write on the authorized work branch; verify the resulting branch and retrievable files. If the head changes, reread and reconcile. Never force-push, bypass a blocked write, or describe a dangling commit object as a saved branch checkpoint.
8. Complete [cycle-record.md](references/cycle-record.md). Distinguish verified GitHub saves from local-only artifacts. Retain every earlier checkpoint. Stop safely at a natural boundary or record the exact interrupted state. Do not claim work will continue after the active execution session without an actual authorized job mechanism.
