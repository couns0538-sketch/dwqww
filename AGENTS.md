# Forge - agent instructions for the Opus branches (opus-r13-*, opus_r14, opus-r14b-*)

The repo has no AGENTS.md on main. The crew's AGENTS.md files on astra-* branches (astra-r8-datafilter, astra-r8-tmfit,
astra-r9-nnue-speed, astra-r10-3jobs) carry Astra-specific rules and stay untouched; their review policy section is the same
verbatim text as below. This file merges that policy with the Opus rules (R14, 2026-11-02).

## Opus R14 rules (Couns; details in `.claude/skills/forge-pc-rules/SKILL.md` and `opus_r14/PLAN.md`)
- Lock FD3A5190 (AL1 s198, LTO+PGO kit v2.3 `-Expose`, znver5); lock source `...\qa_ltopgo_al1_stage\src_al1s198_clean`
  (= git d4f4312) is read-only. Every engine change is an off-by-default UCI option or a build switch; everything OFF =
  node-identical to the lock: bench d11/13/16/20/22 = 312866 / 862329 / 3024920 / 12389307 / 34048354, perft 5 startpos
  4865609, kiwipete 193690690.
- Proof per candidate: pc1 = pc2 exe sha256, OFF pins exact, ON bench per line differs, perft, T1/T4 movetime smoke with
  legal bestmoves, ASan+UBSan self-play (default and max), mate-line probe OFF/ON for pruning / reduction lines; speed only
  by paired ABBA (>= 10 pairs, same core, identical nodes), advisory; QA does official timing.
- No Elo claims: UNPROVEN everywhere; crew gates vs FD3A5190 on UHO (8moves_v3 second, never pooled).
- grok-pc: never stop / pause / re-pin training, gates, self-play, guards or foreign processes; no STOP/PAUSE files; never
  delete or overwrite datasets, nets, locks, logs; never edit forge_queue_state.json, forge_gates.json, CURRENT_LOCK.json or
  the trainer queue; own work BelowNormal (Idle for long jobs), <= 2 threads; C: >= 30 GB, D: >= 50 GB, scratch `D:\o14a\`
  <= 10 GB, F: write-forbidden while below its reserve; GPU only in a window Engine NNUE gives.
- Git: one branch per phase, push about every 10 minutes, stage files by name, never force-push, never touch main or other
  people's branches; RESULTS.md per phase and opus_r13/STATUS.md current at every push.
- Licences: MIT / BSD / Apache code may be copied with its notice (and IDEA_SOURCE.md); GPL / AGPL is ideas only.
- **No sub-agents** (Couns, 2026-11-02, overriding the "one reviewer subagent" of the brief): independent review is
  unavailable, so every review below is a structured self-review and is recorded as NOT independent.

## Opus R14-B additions (Couns, 2026-11-02 12:05 PC clock; binding until changed)
- Branches `opus-r14b-status` / `opus-r14b-fast-loader` / `opus-r14b-relabel`; scratch `D:\o14b\` <= 10 GB (D: >= 50 GB,
  C: >= 30 GB, F: write-forbidden); RESULTS.md per item (`opus_r14b/item1|item2/`) and `opus_r14b/STATUS.md` current at
  every push.
- Sub-agents: the R14-B brief allowed one reviewer; one read-only review of item 1 ran (13:00-13:45). Then Couns
  (13:45): "no subagents allowed they burn tokens and after youre done with all do a 30min review and look for bugs
  glitches etc and fix them". From then on: no sub-agents; every review is a structured self-review recorded as NOT
  independent; the job ends with a 30-minute bug-hunt review pass whose findings are fixed and recorded.
- npt work: never touch the live trainer, its queue, its runs or its loader DLL; work on copies; no HIP runtime next to the
  npt line; GPU only in a window Engine NNUE gives (request in `opus_r14b/item1/GPU_REQUEST.md`).
- A blocked item: write the blocker in its RESULTS.md, push, and spend the time on the other item.

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
