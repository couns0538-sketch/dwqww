---
name: forge-pc-rules
description: Binding safety rules for ANY command run on the Forge PC (chess engine Forge, NNUE training, gates, self-play running permanently). Use before every build, test, benchmark, Python/NNUE run, git push, file write or sub-agent spawn in this repo or under F:\opus_scratch, and whenever a path, priority, thread count, process name or branch is chosen.
---

# Forge PC hard rules (check every command against these)

## Never
- Never run any `train_resid*` script under that name (no such name in any command line or file run). The
  NNUE supervisor (`F:\forge_nnue_train\supervisor.log`) adopts such processes and a failure pauses its queue.
  Keep the literal string out of read-only commands too (`git show`, `grep`, `sha256sum`, `cp`). Two sub-agents
  slipped on 2026-10-27; nothing was adopted, but it breaks the rule's letter. Reach the file by glob
  (`train_res*v3b.py`), or build the name at run time in a script, and work on a renamed copy
  `opus_nnue_smoke_*.py`. Before and after every torch step, count the "adopted running job" lines in
  supervisor.log (7 old ones, the latest 2026-10-27T08:55:34).
- Never delete anything (no `rm`, `rm -rf`, `rmdir`, `git clean`, `git worktree remove`, `Remove-Item`); leave
  scratch files in place. Never kill processes (`taskkill`, `Stop-Process`); stopping my own background shell
  task with TaskStop is fine.
- Never force-push, never `git reset --hard`, never touch `main` (no commits/pushes to main), never push to or
  edit Sol's branch (`forge/sol-pack31-20261025`, read with `git show 17aa0cae:<path>` only), never run Sol's
  lock-recipe / PGO / lock-transition (S28) / delivery scripts, never bare `git stash`.
- Never write to `F:\forge_nnue_train`, PC gate/lock/queue dirs, `C:\Users\Administrator\grok-pc\` (read-only),
  `D:\grok-pc-data\forge_push\` (read-only, including `nnue_data`), `D:\grok-pc-data\selfplay_out`.
- Never disturb gates, self-play or NNUE training. No Elo claims without a gate; no speed claims from a loaded PC.

## Always
- Fastchess gate games, NNUE training (`F:\forge_nnue_train`) and self-play data generation run permanently and
  must never be interrupted. Gates run at BelowNormal; my work runs at Idle (`nice -n 19` in Git Bash) so it
  only takes spare CPU.
- User, 2026-10-27 (speed-up): launch as many sub-agents as the machine allows while the main session keeps
  working; this replaces the earlier "2 agents / 3 threads" caps. Each process single-threaded at Idle, builds
  `JOBS=1`, one heavy step per agent at a time, free RAM >= 6 GB before every heavy step (16 logical CPUs,
  31.6 GB RAM; with one conc-8 gate plus training the PC sits near 55-60% load). Never wait idle on agents.
- New worktrees: `F:\opus_scratch\worktrees\<name>`; logs, builds and scratch: `F:\opus_scratch\<job>\...`,
  never D: (D: is filling up).
- Torch/NNUE/numpy work: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`, `TMP`/`TEMP` =
  `F:\opus_scratch\<job>\tmp`; stop if free RAM < 6 GB
  (`powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)"`).
- Trainer copies only as `F:\opus_scratch\<job>\opus_nnue_smoke_<name>.py`; output folders must not start with
  `runs_` or `smoke_kb`; after starting, check `F:\forge_nnue_train\supervisor.log` has no new
  "adopted running job" line.
- Python: the read-only venv `C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe` (3.10, numpy,
  torch cpu, python-chess) run with `-I -B`; scripts that read downloaded/untrusted data also `-I`.
- Push exactly `git push -q -u origin <branch>` as a literal command (loops with variable branch names get
  denied). Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; evidence-only
  pushes carry `[skip ci]`.
- New options default OFF; with the option OFF, bench/perft must stay identical to the lock pins; FMA count 0;
  every job folder has `IDEA_SOURCE.md`.
- If an action is denied, take another route; do not stop to ask.

## Tooling quirks seen on this PC
- Bash heredocs mangle backslash escapes (`\\`, `\n`, `\f`, `\b`) inside Python/C code: write such code with the
  Write tool and run the file.
- `printf 'uci\n...go ...\nquit\n' | engine` stops the search at `quit` before it prints anything: pause before
  `quit` (`(printf ...; sleep 1; printf 'quit\n') | engine`) or drive the engine from Python.
- Gate folder names are stale (see forge-gate-stats); read the opponent from RUN_INFO.json.
- `python` is native Windows (`os.linesep` = CRLF): `Path.write_text()` / `open(..., 'w')` turn an LF file into
  CRLF. When editing a report or source file from Python, use `read_bytes()`/`write_bytes()` or
  `open(..., 'w', newline='\n')`, and check `git ls-files --eol <file>` (`i/lf`) before committing.
- `git apply` run from a subdirectory of a git work tree silently skips `diff --git` paths (exit 0, nothing applied):
  apply patches with GNU `patch -p1 -F0` (dry run first) and check the result.
- The PC's UTC clock is 9 h ahead of GitHub's server time (time-zone setting); compare CI times with
  `gh api -i rate_limit | grep -i ^date:`, not `date -u`.
- `gh` needs a git checkout as its working directory (`failed to determine base repo` elsewhere): a background
  `gh run view` loop started from F:\opus_scratch never sees "completed".
- TaskStop on a background bash task does NOT stop the work on this PC: the bash itself, its Python children and
  grandchildren all kept running (FB2, three cases: a trainer, the chunk driver, and a bash loop that went on to
  start its next run and collided with a relaunch). Since killing processes is forbidden, give every long chain a
  cooperative stop BEFORE starting it: the FB2 trainer pauses on `<run>/pause.flag`, its driver stops on
  `<run>/driver_stop.flag` (tools/nnue/fable_nnue_chunks.py); loop scripts should test a stop file before each
  step. Never relaunch a chain after a TaskStop without checking `Get-CimInstance Win32_Process` for survivors.

- (R5, 2026-10-29) Never `sed -i` (or otherwise rewrite) a log that a running background chain still writes: the
  writer keeps its old file handle and the evidence file ends up truncated (lost the second search of a v4 engine
  smoke). Let chains write into scratch and copy/normalise into the job's logs/ after they finish.
- (R5) Paths handed to the Windows engine (setoption values, UCI files) must be Windows style (`F:/opus_scratch/...`),
  never MSYS `/f/...`: the engine cannot open those (`info string ERROR NNUE v4: cannot open /f/...`).
- (R5) Gate RUN_INFO.json files carry a UTF-8 BOM: read them with `encoding="utf-8-sig"`, and never let a survey
  script skip files on a parse error silently (it reported "0 string options" from 0 parsed files at first).

## User instructions added 2026-10-28 (FB1 session; binding until the user changes them)
- Push to GitHub at least every 30 minutes (commit + push, finished or not) and after every milestone; before
  usage/context runs out push EVERYTHING plus the job report (what is done, test numbers, what is left, exact next
  steps). Report-only pushes: `[skip ci]`.
- No sub-agents ("they burn tokens"); work alone, never stop while anything is pending (use background commands and
  Monitor, never idle sleeps).
- Every 30-60 minutes and at the end: re-read the finished work for bugs and fix what needs fixing (a review pass
  with a short commit).
- A failed GitHub Actions run must be fixed and re-published (push the fix; the run list must end green). A red run
  of a superseded commit cannot be turned green by re-running it; say so in the report.
- Thread budget is total: builds (`-j2`), trainings (`--threads`), benches and scorers together <= 3 threads.
- FB2 (2026-10-28): no sub-agents at all; do the shorter / feasible jobs first when a pack mixes long and short
  ones; after everything is done, run a dedicated 30-minute bug-test pass over all branches (re-run tests,
  identity checks, self-play smokes, read the diffs) before the final report.

## R5 rounds (2026-10-29, Engine QA job specs R5A-R5D; these override the older lines above where they differ)
- Push every **10 minutes** (finished or not, `[WIP]` ok) with the job report in the same commit; WIP pushes
  `[skip ci]`, the engine push that should be tested ends with a commit WITHOUT it (opus-ci triggers on opus-*,
  fable-*, forge-bundle-* pushes; astra3-* has no trigger).
- Priority BelowNormal (`nice -n 10` in Git Bash), at most 3 threads in total; engine Threads <= 3, Threads 4 only
  inside a 3-CPU affinity mask (`opus_r5/r5d/tools/run_pinned.py --mask 0x700 -- script.py`, children inherit it;
  `start "" /b /wait /belownormal /affinity 700 ...` from cmd for ctest).
- Pause own work while HWiNFO "CPU IOD Hotspot" > 80 C (`opus_r5/r5d/tools/cpu_temp.sh`; it reads ~50 C, Tctl ~81 C
  is the PC's own load).
- Worktrees under `D:\grok-pc-data\dwqww\.claude\worktrees\`, scratch under `F:\opus_scratch\r5\`; never write to E:.
- Never touch running gates, forge_queue.ps1, watchdog, forge_gates.json / manifest, forge_push\bin,
  FORGE_RESULTS.csv or any STOP/PAUSE file; never run Sol's lock / PGO / delivery scripts.
- Astra owns: SmpV2 mate selection, TimeManV2 soft>hard, the v3 loader size check, the unknown-option / strict UCI
  echo, the SingularV2 port, bench_matrix tooling: report findings there, do not fix them.
- End of every round: a 20-minute bug hunt over the own work (re-read diffs and reports, re-run checks), fix what is
  wrong, and keep every GitHub run green.

## R6 (2026-10-29, AMD GPU trainer job; see [[forge-nnue-pytorch-amd]])
- The live Forge trainer uses the **GPU** (torch-directml), not just the CPU. "Never slow it" means GPU runs of
  seconds or minutes at most: tests ~30 s, benchmark runs ~15-45 s each. Check its `pos/s` lines and the
  supervisor "adopted running job" count (7) before and after.
- Gate every torch run on free RAM >= 6 GB inside the runner itself (`bench_train.py` `ram_gate()`). The live
  trainer holds ~12-13 GB; free RAM swung between 5.1 and 9 GB within minutes, and a one-off check printed
  together with the run started a run at 5.1 GB once.
- **R6 INCIDENT, 14:29:05: the live trainer died with numpy `_ArrayMemoryError` (commit limit) during my
  benchmark** `c2_triton` (K32H3^, L1 1024, batch 16384, 2 loader workers, inductor compile). The start-time
  gate had passed. Rules from now on:
  - While the live trainer runs, only smoke-size GPU runs (batch <= 4096, L1 <= 256, 1 loader worker).
  - Bigger shapes or compile runs only when free RAM >= 6 GB + the run's measured peak (c2 used several GB),
    with RAM watched during the run.
  - Never two heavy runs back to back without re-checking.
  - If the trainer dies: stop all GPU/torch work, report the exact error, checkpoint and time, do not restart it
    yourself, and leave the restart to the owner.
- Another agent can be active on the PC: **Grok Bot** (`Grok Bot.exe` -> powershell -> uv/python) installed
  packages into `F:\nnue_pytorch\venv` during R6. Before relying on a shared tree or venv, list processes
  (`Get-CimInstance Win32_Process`, trace ParentProcessId), work in your own clone, and never edit its files.
- Git identity is not configured. Commit with
  `git -c user.name=couns0538-sketch -c user.email=couns0538@gmail.com commit ...`.
  `git worktree add -b X <path> origin/main` makes X track main: run `git branch --unset-upstream` at once.
- `cd` in one of two parallel Bash calls can leak into the other (the second call ran in the first call's
  directory). Use absolute paths or `git -C` in parallel calls.
- Main (`5176ddf7`) has no `.github/workflows`, so pushes to a branch made from main trigger no CI.

## R7 / R8 (2026-10-29; user rules for those jobs, keep unless changed)
- Limits: BelowNormal, <= 3 threads, free RAM >= 7 GB during GPU runs (R7) and >= 8 GB while testing (R8), and **total
  PC CPU under 70% while testing** (R8). GPU only at smoke size (batch <= 8192, in practice 4096, 1 loader thread).
- **Priorities on the PC**: live NNUE trainer (`python`, PID 12236 on 2026-10-29) = **Idle**; live self-play (engines +
  workers, pinned to **CPUs 12-15**) = **Idle**; gate fastchess + engines = BelowNormal. My BelowNormal work outranks
  the trainer and self-play, so pin it off their CPUs: `run_pinned.py --mask 0x0FFF -- script.py` (CPUs 0-11; builds
  `0x00FF`), copy at `opus-r8-datagen:r8/tools/run_pinned.py`. `cmd //c "start /affinity FF ..."` from Git Bash
  fails with "Access is denied" AND leaves hung `cmd`/`xargs` processes behind (TaskStop does not end them); run
  builds through a Python driver under run_pinned instead (`r8/tools/build_620.py`).
- **Incident 2026-10-29 17:04:36**: the live self-play stopped writing (all its processes alive at 0 CPU) while my
  unpinned conc-3 mini-gate ran; cause not proven (bounded output queue + Idle priority on CPUs 12-15; the Oct-18 log
  shows the same pipeline dying on "Engine returned no score" = OwnBook hit). Never restart it yourself; report it.
- The auto-mode permission classifier refused a GPU run at batch 8192 + 2 loader threads ("Interfere With
  Workloads"); the same job at batch 4096 + 1 loader thread was allowed. Long compound commands (copy + test + commit
  + push in one line) were refused twice; split them into single steps.

## Quick self-check before running something long
1. Name contains `train_resid`? -> rename the copy.  2. Output path on F:\opus_scratch? 3. nice 19 / threads?
4. Total threads with running jobs <= 3?  5. Reads PC data read-only (copy first if a tool might write)?
6. Free RAM >= 6 GB checked by the runner itself?  7. Another agent working in the same folder?

## R8 fixes + R9 (2026-10-29 evening; user rules for R9, keep unless changed)
- At most 4 threads, BelowNormal, pinned to **CPUs 0-3** (`run_pinned.py --mask 0x000F`); total PC CPU < 70%; free RAM
  > 8 GB; commit + push about every 10 minutes on the job branch; never stop/slow NNUE training, never touch gates or
  self-play; ideas only from other tools (IDEA_SOURCE per job).
- Measured load 2026-10-29 20:00-21:00 WITHOUT any of my work: 72-82% (gate conc 4 x Threads 2 = 8.0 CPUs, live
  self-play 2.1 CPUs again since its owner restart, trainer 1.3). Under the 70% cap no game-playing job fits while such a
  gate runs: give long jobs a load governor (sample the system CPU between batches, run only with the concurrency the
  cap allows, wait otherwise) instead of a fixed thread count (`opus_r9/tuner/r9_spsa.py governor()`).
- Gate runner fact: it checks that every option it passes to an engine is ADVERTISED in the engine's `uci` output
  (ENGINE_OPTIONS_CHECK.txt "options advertised"), so new tunables must be listed, not only accepted.
- Working copies here are CRLF (core.autocrlf=true, index LF): patch scripts must normalise `\r\n` before matching
  anchors (or the anchors never match) and write the file back in its own style.
- **R9 cap changed by the user (2026-10-29 ~23:35 PC clock):** total CPU cap 80% (start/continue own runs while the load
  without them is <= 80%), pause own runs (never kill them) when the total stays above 90% or free RAM < 8 GB; still at
  most 4 threads, BelowNormal, CPUs 0-3; keep pushing every 10 minutes. The owner paused self-play at ~23:30 (load 62%).

## R11 (2026-10-30, QA + Code Review rules for the NNUE pipeline; binding until changed) - see [[forge-nnue-pipeline]]
- Priority: **Idle (0x40) + I/O priority very low + memory priority low, at most 3 cores** (mask 0x700 = CPUs 8-10) for
  every own process; BelowNormal outranks the Idle trainer and self-play. All four are inherited by children. Do NOT use
  background mode (PROCESS_MODE_BACKGROUND_BEGIN; CR fix 2 amendment 2026-10-30): it caps the working set at 32 MB, so
  any process with a few hundred MB of data pages itself to death (dedup >18 min instead of ~2, 445k page faults/s).
- **No STOP/PAUSE control files** (they break the owner's rule); a hold is the named event `Local\Forge_R11_Hold`;
  stopping is by PID (the owner does it; Stop-Process is denied for the agent, even for its own processes) and every
  stage resumes from its done markers. A process can be lowered instead: `(Get-Process -Id N).PriorityClass='Idle'`.
- Disk: check free space before every write, download and extract; the drive a big run writes to keeps >= 40 GB free
  AFTER the run (D:); D: free space moves with other jobs by 10-20 GB per hour. Never overwrite
  `F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack` (the live trainer reads it); 013/014 stay out of training.
- Inputs: full sha256 for sealed inputs (no first/last-MiB fingerprints); outputs `.part` -> verify -> rename; delete
  only your own partial files after a failed check.
- GPU: yield-only (never train next to a production trainer, exit when one appears); the production-process check runs
  before `import torch`; psutil missing = FAIL, an unreadable python command line = production (wait).
- Engine for checks/gates: AVX2 `-march=x86-64-v3` build of the named commit (never znver5, never exe 9b7e2fcd);
  GATE_EXE is always the exe sha256, never the commit. Hand packages to QA; never queue (no queue.txt /
  queue_state.json / forge_gates.json / locks / baselines).
- Holdout must be proven on the real 013/014 data before any training. GPL tools stay run-only in tools/.
- The ask rule `Bash(git push *)` in the project settings prompts the owner on every push; the agent cannot change
  permission settings (auto-mode classifier: self-modification).
