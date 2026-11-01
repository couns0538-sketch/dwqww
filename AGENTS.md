# Development review and verification

Review, fixing, and verification are automatic parts of the development workflow.
Do not wait for the user to request `/review` or monitor the terminal.

After each meaningful implementation milestone, before expensive validation of
a new candidate, and before declaring completion:

1. Finish a coherent change and run the relevant quick build and correctness checks.
2. Arrange a focused review of the exact candidate, its requirements, and relevant
   surrounding code. Use one reviewer subagent when available. Instruct the reviewer
   to inspect without editing and return concrete defects, supporting evidence,
   and missing checks. Keep the reviewed files stable while review is in progress.
3. The main agent reads and assesses every finding. Fix confirmed issues within
   scope, explain rejected findings, and record unresolved issues. Merely presenting
   the review report does not complete the work.
4. Run relevant checks after fixes. Have the reviewer recheck substantive fixes
   and affected areas when needed. Avoid repeated full reviews of unchanged code
   and speculative cleanup without evidence.
5. Continue the original task automatically within existing permissions and
   resource limits; routine review, fixes, and verification need no new user request.

Choose milestones from actual progress, not a timer. Keep review delegation small
and avoid duplicate investigations. If an independent reviewer is unavailable,
state that and perform a structured self-review; do not call it independent.

For chess engines, focus on risks introduced by the change. Preserve the accepted
baseline, running experiments, and all evidence. Never overwrite an executable
being tested or attribute an earlier candidate's results to modified code.

At each completed milestone, save a concise record of the reviewed scope,
candidate identity, findings, fixes, validation results, and next action in the
task's evidence directory. Never call an unresolved candidate accepted.

## Shared-PC execution for Astra R8

Use CR's sleep-based governor for native grok-pc work: start below80%CPU,
wait when CPU reaches90%, and require8GiB free physical RAM. Preserve the
mandated BelowNormal priority and at most two active engine/build workers.
Do not suspend any process, including owned processes. An owned-process pause
step may only be considered after its code is committed to astra-r8-tmfit and
CR has explicitly passed it; that approval has not been given. Never control
crew gates, fastchess, NNUE training, or self-play processes. The earlier
scratch pause-attempt helper is not an authorized execution path.
