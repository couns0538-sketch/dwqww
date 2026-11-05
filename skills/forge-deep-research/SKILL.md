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
