# OSS scout for Forge - STATUS (handoff file)

Updated: 2026-11-06 19:26 (PC clock). Branch `opus-oss-scout-20261106` (from main 5176ddf7), repo copy of this file:
`opus_oss_scout/STATUS.md`. Plan: `C:\Users\Administrator\.claude\plans\velvet-seeking-meerkat.md`.

## Rules in force (brief of 2026-11-06 + findings)
- Research and sandbox trials only: no engine edits, no Elo claims, no helper agents.
- Own work: Idle priority, CPUs 2-3 (mask 0xC). The session process claude.exe pid 4532 was narrowed from 0xF to 0xC
  at 19:24 (PC clock); its children inherit Idle + 0xC. At most 2 heavy threads.
- Never touch: live gates, fastchess, forge_queue, self-play, NNUE training runs or their run dirs, locks, nets in use,
  datasets (copies of small samples only), other bots' configs, F:\ospd, C:\ospd_hunt. No deletes, no kills, no
  force-push, no main, no PATH changes or system installs. GPL / AGPL = ideas only.
- Disk: build and download only into `C:\opus_5h\oss_scout\` (target <= 10 GB, hard cap 15 GB). Stop downloading when
  C:, D: or F: is under 30 GB free. Nothing is written to D: or F:.
- Commits: identity couns0538-sketch, no vendor names, no trailer; push `git push -q -u origin opus-oss-scout-20261106`.

## Findings that change the brief (one sentence each)
1. The GPU is an AMD RX 7900 XT (no nvidia-smi); headroom is read from Windows GPU counters, the live trainer uses
   ~75-80 % compute and npt has the GPU booked to Nov 8, so this job uses no GPU and writes GPU steps as commands for an
   owner window.
2. E: is a 3 GB volume, so the 30 GB floor applies to C:, D: and F: only.
3. The Idle trainer shares CPUs 0-3, so own work runs on CPUs 2-3 only and every rate is written next to the crew load
   (CPUs 0-3 were 66-85 % busy at 19:25 before any own work).
4. Already with the crew (cited, not re-proved): bullet on ROCm for v2 nets (30-h job), Forge's own Syzygy reader
   (R13 P6, not in the lock exe), UHO_Lichess_4852_v1.epd on the PC (gates use 8moves_v3), large pages (H1/H7
   NO-WIN), own SPSA tuners, exact fastchess LLR tools.
5. Commit messages carry no vendor names and no trailer (same-day 5-h brief convention).

## Done
- Folder layout `C:\opus_5h\oss_scout\{dl,build,data,tools,tmp,logs}`; gate script `tools\scout_gate.ps1` (first run
  OK, log `logs\scout_gate.jsonl`).
- Shallow sparse clone `C:\opus_5h\oss_scout\repo` (sparse `/opus_oss_scout/`), branch created.

## In progress
- Step 1: first commit + push of this file.

## Exact next step
- Step 2: survey -> `repo\opus_oss_scout\CATALOG.md` (metadata via `gh api repos/<r>`; licence files for NOASSERTION).

## Resume commands
- Gate before any heavy step: `pwsh -NoProfile -File C:\opus_5h\oss_scout\tools\scout_gate.ps1 -Step "<what>" -PlannedGB <n>`
- Re-pin the session after an app restart: find the new claude.exe pid (parent chain of `$PID`), then
  `(Get-Process -Id <pid>).ProcessorAffinity = [IntPtr]0xC` (priority must stay Idle).
- Commit: copy `C:\opus_5h\oss_scout\STATUS.md` to `repo\opus_oss_scout\STATUS.md`, then in `C:\opus_5h\oss_scout\repo`:
  `git -c user.name=couns0538-sketch -c user.email=couns0538@gmail.com commit -F <msgfile>` and the literal push.

## Unproven claims
- None yet.
