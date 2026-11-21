# Forge evidence, status and inter-agent handoff

## Separate four kinds of recency

- **Activity recency**: newest commit message or agent assignment.
- **Source recency**: latest effective change to C++ source, embedded nets and build flags.
- **Build recency**: newest traceable native executable built from a stated source revision and net.
- **Accepted-strength recency**: latest candidate explicitly accepted through the project's recorded validation and playing-strength decision, not merely recent or fastest.

A newer status note does not prove a new engine; a newer binary does not prove strength; a high-speed result does not prove Elo. If ownership or acceptance is ambiguous, say `UNDETERMINED`.

## Evidence grades (local reporting convention, not an official Forge release policy)

- **A - accepted**: explicit acceptance/promotion record, traceable exact artifact and build/net hashes, relevant correctness gates, valid competitive comparison and intact raw evidence.
- **B - tested candidate**: reproducible source/build and substantial appropriate testing, but no verified promotion or remaining tests unresolved.
- **C - experimental**: source changes or limited measurements, incomplete controls, missing confidence, or no full evidence.
- **D - report-only / unknown**: coordination notes, forecasts, proposals or test claims without matching artifacts.
- **F - known failed**: reproducible correctness defect, failed relevant gate, or invalidated claimed result. A failure in one option need not invalidate unrelated default behavior, but scope it explicitly.

Never assign A solely because an agent says "ship", a branch is called `integrate`, or the assistant cannot find counterevidence. A status grade applies to the *exact tested candidate*, not every branch sharing some files.

## Essential Forge validation gates

Use the target revision's actual contract. As a **historical example only**, original Combo29 documented start-position perft 5 = 4,865,609 and Threads=1/Hash=16/OwnBook=false bench depths with specific nodes. A strength-altering variant need not match old search nodes. Incorrect chess rules are unacceptable even when NPS improves.

- Correctness: legal moves and perft, castling/en-passant/promotion, repetition, fifty-move handling, mate-score encoding, TT, SMP, UCI stop/ponder/movetime, regression fixtures.
- Native build: compiler, optimization and target ISA, sanitizer coverage, binary identity and embedded/external NNUE weights.
- Speed: paired measurements with equal affinity, threads, hash, clock, warmup and workload; compare wall time/NPS with uncertainty.
- Strength: UCI game matches with paired openings and fixed time control, opponent source/build, raw PGNs, WLD, error bars or SPRT decisions and completed-game counts. Stopped matches and synthesized results are not a pass.
- Reconcile known failing fixtures, sanitizers, omitted promotions, and local-only source changes rather than hiding them in a final report.

## Agent ownership and bounded handoffs

Before assigning a new job, read the most recent relevant Opus/Fable/Astra/Sol/Kimi/DeepSeek/Carbon notes and claimed job ownership. Avoid duplicate work unless it is *explicitly* an independent validation. Do not overwrite another agent's branch or files.

A portable handoff should contain:

```
UTC timestamp:
Repo and base source SHA:
Candidate/source SHA and net hash:
Task and owner:
Other concurrent work and CPU ownership:
Exact changes (paths and commit):
Correctness PASS/FAIL/INCOMPLETE and evidence URLs:
Speed PASS/FAIL/INCOMPLETE and evidence URLs:
Strength PASS/FAIL/INCOMPLETE and raw PGNs:
Open blockers and required checks:
Next safe action, permitted branch, resource budget:
```

If execution is interrupted or context expires, checkpoint only through an already authorized destination. Keep the user-supplied model, effort, compute budget, permission gates and required work duration; a skill cannot guarantee persistent autonomous execution.
