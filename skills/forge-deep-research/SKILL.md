---
name: forge-deep-research
description: Run a licence-gated deep-research job for Forge (what other chess engines, trainers and tools do that Forge lacks) as cards with source numbers, licence at the exact commit, a lock-source grep and a gate route - setup (partial sparse clone, Idle CPU mask inherited by every tool, vendor-name clean filter), the helper tools (commit/SPRT miner, licence-at-commit, lock grep, card lint, tried gates, block rule), the worker rules and card template, the custom Workflow (one worker + one adversarial verifier per track), checkpoints, the low-usage stop, and the pitfalls of 2026-11-04. Use for any Forge research / idea-mining / "what do other engines do" job, a resumed one, or a new track.
---

# Forge deep research (cards, licence-gated)

Built in the job of 2026-11-04 (branch `opus-deepres-20261104`, folder `opus_deepres/`). Everything below was used
there; paths are the ones of that job.

## Setup (10 minutes)
1. Clone only what you write (the repo is ~8 GB): `git clone -q --filter=blob:none --depth 1 --single-branch --branch
   main --no-checkout https://github.com/couns0538-sketch/dwqww.git F:/odr/wt`, then
   `MSYS_NO_PATHCONV=1 git sparse-checkout set --no-cone '/opus_deepres/' '/skills/'` (without MSYS_NO_PATHCONV Git
   Bash turns '/x/' into 'C:/Program Files/Git/x/'), `git checkout -q -b <branch>`, `git config core.autocrlf false`.
   Fetch another branch's file without touching D:: `git fetch -q --depth 1 --filter=blob:none origin <branch>` then
   `git show FETCH_HEAD:<path>`.
2. CPU rule "Idle, <= 2 threads, never CPUs 7-15": set the session's own agent CLI process (the exe that spawns the
   tool shells; find it by walking ParentProcessId up from `$PID`, check its path) to `PriorityClass='Idle'` and
   `ProcessorAffinity=3`; every Bash / PowerShell tool process and every workflow agent's tools inherit both (check
   one child). Never touch anybody else's process.
3. Vendor names: paths through the agent configuration folder contain a vendor name. Commit through the clean
   filter `tools/novendor_filter.py` (`git config filter.novendor.clean "<python> -I -B .../novendor_filter.py"`,
   `filter.novendor.required true`, `* filter=novendor` in `opus_deepres/.gitattributes` and `skills/.gitattributes`);
   it writes that folder as `<cfg>` in the committed blobs only. Before every push: `git grep --cached -i -E
   '(^|[^a-z0-9])(<names>)([^a-z0-9]|$)'` must print nothing. No commit trailer naming a model company.
4. Start files at once and push: STATUS.md (start, deadline, USAGE UNKNOWN unless a meter is readable), FINAL_REPORT.md
   marked IN PROGRESS, LICENCES.md, RESUME.md. Push with the literal `git push -q -u origin <branch>`, verify with
   `git ls-remote origin refs/heads/<branch>`.

## Tools (opus_deepres/tools/, python = the read-only venv with -I -B)
- `mine_commits.py OWNER/REPO [--since 2024-01-01] [--top N] [--grep RX] [--show SHA]` - titles + parsed SPRT blocks
  (OpenBench "Elo | x +- y", fishtest "Total: W L D" -> ~Elo), cache F:/odr/cache/commits; labels STC/LTC by TC, the
  TC printed is the truth. `--show` only for the few commits a card cites.
- `licence_at.py OWNER/REPO [SHA] [--row]` - LICENSE files at the exact commit, guessed SPDX, GitHub's detection;
  "absent" for repos without one (e.g. Integral).
- `forge_has.sh 'REGEX' [N]` - grep of the lock source (src_al1s198_clean) without the generated tables.
- `card_lint.py [files]` - 8 fields in order, <= 60 lines, UNPROVEN in Expected gain, SPRT/ABBA in Test plan, Status
  line, one-line cards, vendor names, licence headers.
- `tried_gates.py [--grep RX]` - compact "already gated" list from the crew's FORGE_RESULTS.csv (the QUEUE_PENDING.md
  tried list could not be found on 2026-11-04; FORGE_RESULTS is the authoritative gate record).
- `block_rule_check.py` - cheap game-block rule on self-play text (result change or ply not increasing) vs the R14 scan.
- `workflow_prompts.py <workflow transcript dir> <out>` - save the exact task each workflow agent received.

## Workers
- `WORKER_RULES.md` + `cards/TEMPLATE.md` are the brief every worker reads first (licence tiers and the no-source rule
  for GPL / AGPL / unlicensed repos, caps, save-as-you-go, names, outputs only in `cards/T<nn>/` + `notes/T<nn>/`).
- Do NOT run the stock deep-research workflow for this: it has no per-source licence gate and no card output (the
  30-Oct round was also stopped before its costly verify phase). Use `tools/workflows/deepres_tracks.js`: one research
  worker per track, then one adversarial verifier per track (pipeline). Each agent's first message relays the owner's
  brief verbatim, so the ground rules reach it; put the track brief, local pointers and minutes in `args.tracks`.
- Save-as-you-go is what makes a stop safe: each card file exists from its first source (PENDING fields), every source
  gets a line in `notes/T<nn>/sources.md`. Stopping a workflow (TaskStop) keeps every file; a relaunch with
  `continue_note` lets the new worker extend the old files instead of re-reading sources.
- Agent count follows the owner's latest word (2026-11-04: 2 at a time, then "up to 12"): when more are allowed, run the
  core tracks in parallel first (the low-usage risk favours finishing core tracks early), optional tracks next.

## What one round cost and caught (2026-11-04, measured)
- 7 tracks x (1 research + 1 verify) = 14 agents: 2,952,180 agent tokens for 14 agents of the two finished
  workflows (~190-225k each), 45-55 min wall time with 7 in parallel. Researchers stop at the 6-card cap after 20-45
  min, so once a track's cap is hit more research agents add nothing; use phase 2 instead: ONE cross-track critic
  (coverage matrix of every brief question + a number-by-number check of the report against the cards) and ONE
  independent second vote on the top cards (`tools/workflows/deepres_phase2_checks.js`). Phase-2 agents write only
  their own note file; the coordinator applies fixes (no edit races).
- Verifiers caught: a stale control number (pre-fix exe), a path that vanished because another job restructured a
  folder (cite durable branch copies, not scratch paths), a tuned constant of another engine carried over as a Forge
  value, wrong commit dates, licence-tool misreads. Keep the verifier step.
- Give every worker a scratch folder (`F:/odr/work/T<nn>/`) in WORKER_RULES from the start: without it four of seven
  first-round workers put temp files into the session scratchpad on C:.
- `licence_at.py` guesses from the licence title first (the GPL-3.0 text names the Affero licence in section 13; LLVM's
  file starts with Apache-2.0 WITH LLVM-exception but also carries MIT-like legacy text; CC0 is "Creative Commons
  Legal Code"). Re-run every merged row with `merge_licences.py` after a tool fix.
- Read hand-backs with `tools/handbacks.py <workflow transcript dir> --json out.json` instead of the long
  notification text.
- For a long run with a fixed agent count (owner 2026-11-04: "10 agents for 5 hours, then 5"), use ONE dynamic
  workflow, not several rounds (owner's suggestion): `tools/workflows/deepres_pool.js` = a task queue + N worker loops
  (promise-based wait / notify), verify tasks pushed to the queue FRONT after each research task, a planner agent that
  proposes new sub-tracks when the queue is empty (keys checked against a used set), late tasks (critic, ranking draft)
  queued at a clock threshold. Workflow scripts cannot read the clock (no Date): every schema carries a `clock` field
  (`date +%H:%M` at hand-back) and the script switches the pool size / stops new tasks from the latest clock seen
  (minutes after 22:00, midnight handled). Each prompt also has its own "stop at <time>" rule because the script's
  clock lags by up to one task length.
- Stopping a workflow (TaskStop) and relaunching its unfinished tasks as continuations (files on disk + a
  `continue_note`) worked twice in this job; nothing written by the stopped agents was lost.
- NEVER resume (resumeFromRunId) a pooled workflow: its cache replays an order-dependent prefix of agent() calls, and
  a pool's call order changes on replay, so finished agents start again live (2026-11-05 01:25-01:29: verifiers,
  research and specs restarted; stopped within ~2 min). Start a FRESH run seeded with only the remaining tasks.
- Refill the queue BEFORE it is empty (planner when fewer than 3 research tasks wait); planning only on an empty queue
  left 4 of 10 slots idle while the planner read the notes.

## Worker cap, board and the 3-worker pool (2026-11-05)
- Owner cap: at most 3 agents in total, agent types `fable` or `opus-max` only. A PreToolUse hook
  (`<cfg>/hooks/worker_cap.ps1`) counts `agent-*.jsonl` transcripts written in the last 3 minutes (all projects,
  workflow agents included) and refuses Agent / Task / Workflow calls at >= 3 - TaskStop too. A finished worker counts
  for 3 more minutes: wait before launching. Agent calls inside a running workflow are not hooked: the script caps
  itself (`N <= 3`).
- Because TaskStop can be refused, every pool has a cooperative wrap-up note (`F:/odr/work/pool_wrapup.txt`): workers
  test it before each source and every 10 minutes, save, free their slot and hand back with `wrapup_seen`, and the
  script then starts nothing new.
- Crew board `D:/grok-pc-data/dwqww/WORKER_BOARD.md` (three slot lines): `tools/board.py start S<n> "<worker>" "<task>"`
  first, `... done S<n> ... "<result path>"` last (appends the done line). `start` takes another idle slot when the
  named one is busy (two runs can share the board) and refuses after 10 minutes when all 3 are busy; `done` releases by
  worker + task. `board.py check` exits 1 above 3.
- `tools/workflows/deepres_pool3.js`: task fields `kind` (research / note; a Fable verifier goes to the queue front
  after each research task), `agent` (fable | opus-max), `after` (keys `kind:key` that must be done first),
  `latest_start` (minutes after 22:00), `outputs`, `verify_brief`, `minutes`, `max_cards`.
- Agent types added after the session started are not in its registry: every `agentType: opus-max` spawn failed at
  once (journal "failed", empty agentId, no tokens). The script now runs opus-max work as the session model at effort
  max directly; `fable` works as an agent type.
- When a pool has only sequential work left, its other slots sit idle: start a separate 1-worker run (same script,
  fresh run) for a non-overlapping task, keep the total <= 3, add each run to STATUS and to `checkpoint.sh`.
- Round 3 measured: POOL3 10 agents 1,690,105 tokens (65 min); 1-worker runs 334,288 (2 agents) and 514,776 (3).
  Late-round yield: a lock-source audit against the bug checklist found nothing >= 1 Elo; mining a 20th-plus engine
  gives 0-1 card; counter-evidence for the top 10, own-words specs and a Fable spec review changed the gate plan most.

## Checkpoints and the low-usage stop
- Commit + push about every 10 minutes (the coordinator only; workers never commit). Update STATUS (track table,
  latest pushed commit), RESUME and the report state line each time; merge `notes/T<nn>/licences.md` into LICENCES.md.
- Low usage (a readable meter <= 10 %, or an explicit warning): TaskStop the workflows, `git add opus_deepres skills`,
  commit, push, verify the remote head, then write STOPPED EARLY - LOW USAGE into the report / status / resume and push
  again. Never wait for a worker to finish first.

## Pitfalls of 2026-11-04
- Times: read `date` before writing any time; the message time of an owner instruction is not known - write the
  bracket ("before 22:45, the next script file's stamp"), not a guess. Script / transcript file stamps are measured
  times.
- `nnue_weights.inc` line 1 names the residual trainer script (the forbidden name): never print that file's head.
- The J1 npt binpack stores no castling / EP (FPOS rows): the leak key for nets is board + side to move.
- A shell `cd` outside the session's working folders resets to the start folder: use absolute paths.
