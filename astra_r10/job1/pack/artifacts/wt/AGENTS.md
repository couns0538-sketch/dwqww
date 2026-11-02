# Forge Astra R10

Work only on astra-r10-3jobs, under D:\a10. The imported src/ and include/ retain the R9 candidate over AL1 s198. Preserve all evidence and immutable candidate binaries. Never alter accepted weights; the explicit one-weight negative control belongs in a separately identified disposable copy. All task-specific instructions in Couns's request and the approved R10 plan apply. Earlier branches, Opus folders/branches and production queues are read-only and must remain untouched. F: is forbidden. All results are UNPROVEN pending crew gates.

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
