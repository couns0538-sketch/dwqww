# Astra R8 datafilter

Scope: result-aware data tools only. All strength claims are UNPROVEN.
Production tools, datasets, networks, installed npt and crew processes are read-only.
No training, GPU work, relabeling, engine edits, STOP/PAUSE files or fast-loader work.
Owned computation: BelowNormal priority, at most two workers. New artifacts under
`C:/astra8_data` under the user's 2026-11-02 override; keep C: above 50 GB,
including the next allocation. Retain D: 50 GB. Existing D:/F: datasets and
artifacts remain read-only; F: being below 50 GB does not block authorized C: work.
Count preserved D:/F: and new C: artifacts together toward the 15 GB cap.
Checkpoint RESULTS.md before each push, approximately every ten minutes. No force push.
Read-only milestone reviews: converter, filter before million-row run, adapter, final evidence.
Freeze candidate hashes during reviews; record findings, dispositions and rechecks in REVIEW_LOG.md.
Handoff: Code Review -> Engine NNUE -> Engine QA. Strength gates remain crew-owned.

MIT/BSD/Apache code may be copied only with full notices. GPL/AGPL code,
including npt/Stockfish tools, is ideas-only. No Leela data without a quoted
permissive licence in IDEA_SOURCE.md. Never modify, move or delete datasets or
.nnue files. Do not allocate new artifacts on F:. No engine changes: lock FD3A5190,
OFF bench 312866/862329/3024920/12389307/34048354. No loader-throughput work.
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
