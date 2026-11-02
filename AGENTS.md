# Forge Astra R11

Work only on astra-r11-gameprov from e6868fd56ebb3991ee197af6be29f3dd14a4d1c2. All worktrees, Git objects, outputs, runtime and caches belong under D:\a11. Never access F: or D:\a10. Existing datasets and historic source files are read-only. Do not access any .nnue file, lock FD3A5190, live queues or forge_queue_state.json. Never kill/suspend/pause other processes; no STOP/PAUSE files. CPU only, Idle, verified spare CPUs, no GPU/training/strength claims. Keep C: >=30 GiB and D: >=50 GiB plus next bounded reservation. Preserve all failed evidence.

Approved plan: astra_r11/PLAN.md. Complete original 013/014 authentic provenance is mandatory; missing holdout IDs means BLOCKED. Never fabricate IDs from row numbers, FEN boundaries or shard names. The exact CR prerequisite files are inert, hash-pinned historical repairs; implement R11 adaptations separately. Preserve all sealed R10 packs. All results UNPROVEN pending crew gates. Update STATUS.md and RESUME.md and commit/push hourly. Skill improvements stay in this branch, not C:.

## Review, fix and verification policy (Couns, verbatim)

Continue the current task, and make review, fixing, and verification
an automatic part of your development workflow from now on.

I will not monitor the terminal to decide when to type /review.
You are responsible for choosing appropriate review milestones
and acting on the findings.

After each meaningful implementation milestone, before expensive
validation of a new candidate, and before declaring completion:

1. Finish a coherent change and run the relevant quick build and
   correctness checks.

2. Arrange a focused review of the exact candidate, its requirements,
   and the relevant surrounding code. Use one reviewer subagent when
   available. Instruct it to inspect without editing and return concrete
   defects, evidence, and missing checks. Keep the reviewed files stable
   while that review runs.

3. You, the main agent, must read and assess the findings. Fix confirmed
   issues within the task's scope, explain rejected findings, and record
   anything unresolved. Do not stop after merely presenting the report.

4. Run the relevant checks after fixes. Have the reviewer recheck
   substantive fixes and affected areas when needed. Avoid repeated
   full reviews of unchanged code or endless speculative cleanup.

5. Continue the original task automatically within the existing
   permissions and resource limits. Do not wait for me to manually
   request each review, routine fix, or verification step.

For chess-engine work, focus review on the risks introduced by the
change. Preserve the accepted baseline, running experiments, and all
evidence. Never overwrite an executable being tested or attribute
results from one candidate to a later modified candidate.

Use review milestones based on actual progress, not a timer.
Keep review delegation small and avoid duplicate investigations.
If independent review is unavailable, state that clearly and perform
a structured self-review without calling it independent.

At each completed milestone, save a concise record of what was
reviewed, the candidate identity, findings, fixes, validation results,
and the next action. Do not call an unresolved candidate accepted.

Merge this policy into the project's existing AGENTS.md, preserving
its other instructions, and follow it in the current session too.
Apply the first review at the next suitable milestone, then continue
working without waiting for me.

Record each review milestone in the branch RESULTS.md (what was reviewed, candidate SHA/exe hash, findings, fixes, checks, next action).
