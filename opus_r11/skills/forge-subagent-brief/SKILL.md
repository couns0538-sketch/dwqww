---
name: forge-subagent-brief
description: Template and checklist for delegating a Forge job to a background sub-agent (Agent tool) - scope, binding PC rules, paths, deliverables, hand-back format. Use whenever spawning or messaging a sub-agent for Forge/NNUE/Sol-leftover work.
---

# Briefing a Forge sub-agent

FIRST check the user's LATEST instruction on sub-agents (memory `no-subagents-cost`): it changes per job and
overrides everything below. R11 (2026-10-30): "no subagents they burn tokens only you alone work till its done" -
the user stopped a read-only review agent; do reviews and second reads yourself.

Limits when agents ARE allowed (user, 2026-10-27 speed-up): as many sub-agents as the machine allows (RAM floor 6 GB
free, Idle priority, one heavy single-threaded step per agent); the main session keeps working meanwhile; never wait
idle on them; give each a disjoint job list and its own worktrees; only the main session edits the progress file.

## Brief template (fill every line)
1. Goal and jobs in order (IDs + one-line spec each; point to `SOL_LEFTOVERS_FOR_CLAUDE.md` section/lines and
   `F:\opus_scratch\sol_inventory_17aa0cae.json` `jobs[]` for the verbatim spec).
2. What is already done / ruled out (branch heads, files, numbers they can reuse).
3. Rules: "Read and follow `D:\grok-pc-data\dwqww\.claude\skills\forge-pc-rules\SKILL.md`,
   `forge-job-workflow` and (engine jobs) `forge-engine-verify`." Restate the top ones inline: no train_resid*
   names, no deletes, no process kills, no force-push, never main or Sol's branch, nice 19, 1 thread
   (builds JOBS=1), outputs only under `F:\opus_scratch\...`, worktrees under `F:\opus_scratch\worktrees\`,
   PC data read-only (copy first), RAM floor 6 GB, push with the literal `git push -q -u origin <branch>`.
   Spell out that `train_resid` must not appear in ANY command line, read-only ones included (use globs or
   renamed copies), and that the agent must not create releases, issues or anything outside git branches
   unless the spec asks for it (S48-4's prerelease was spec-driven).
   Re-use finished agents: a hand-back agent can take a related follow-up through SendMessage and keeps its
   context. Examples: S39/S50 → S-A3 (v3d), S09fix → S-A2 trainer work.
4. Deliverables per job: the folder layout from forge-job-workflow; agents cannot write REPORT.md, so they
   return the full REPORT.md text in the final message plus a one-line progress entry
   (`<JOB> | <branch> | DONE (<sha>) | <summary>`).
5. Hand-back: what to include (acceptance table, key numbers, UNVERIFIED list, branch heads verified with
   `git ls-remote`).

## On hand-back
Follow the "Sub-agent hand-backs" section of forge-job-workflow (copy REPORT text, spot-check numbers,
finish_report.sh, commit, push, verify, update progress).
