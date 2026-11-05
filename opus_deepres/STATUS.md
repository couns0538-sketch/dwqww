# Forge deep research - STATUS

Branch `opus-deepres-20261104` (fresh from `main` 5176ddf7), repo couns0538-sketch/dwqww. Local clone `F:\odr\wt`
(partial + sparse: only `opus_deepres/` and `skills/` are checked out). Scratch `F:\odr\` (cap 5 GB). Nothing of
this job is written to D:.

## Clock and limits
- Start: **2026-11-04 22:23:27 PC clock** (first `date` of the job; the PC prints PST -0800, earlier notes call it
  the Vienna wall time - all times here are the PC clock as printed).
- Hard deadline (10 h): **2026-11-05 08:23:27**. No new research questions after **07:53:27** (9 h 30 min).
- INTERIM report due: about **2026-11-05 02:23** (4 h).
- Last update of this file: 23:06 (elapsed 0 h 43 min). Disk at 23:04: C: 98.8 GB, D: 50.9 GB, F: 61.3 GB free;
  RAM 20.3 GB free; F:\odr uses 5.9 MB.
- Usage: **USAGE UNKNOWN** - this session cannot read a usage meter; the regular 10-minute checkpoints are kept and
  any explicit low-usage warning triggers the immediate save-and-push.
- Process limits: this session's own process was set to Idle with affinity CPUs 0-1 at 22:26 (all tool processes
  inherit both; checked on a child process), so every command runs at Idle on at most 2 logical CPUs, never on
  CPUs 7-15. Disk at start: C: 84.6 GB, D: 51.8 GB, F: 59.6 GB free; RAM 23.1 GB free.

## How the research runs
- Not the stock deep-research workflow: its shape (5 search angles, 15 fetches, 3-vote claim check, one report) has
  no per-source licence gate and no card output, and the 30-Oct round was stopped before its verify phase for
  usage. Instead two custom workflows: one worker per track writes cards to disk as it reads (WORKER_RULES.md), then
  one adversarial verifier per track re-checks numbers, links, licences, the reading rule and the Forge greps.
- Agents: 2 at a time at first; then the owner allowed up to 12 ("i allow you to launch more agents in the deep
  research up to 12"; received before 22:45 - the next workflow's script file is stamped 22:45; the exact minute was
  not recorded). Used for: the optional tracks T6 / T7 / T12 in parallel, and the core tracks all in parallel.
- Workflow `wf_5cef37bf-0b9` (first core run, script stamped 22:39): chain A = T1 then T4, chain B = T2 then T5;
  STOPPED at 22:47 to re-plan (its T1 / T2 workers' files stayed on disk and are continued, not redone).
- Workflow `wf_b823f43e-496` (core2, 22:48): T1, T2 (continuing), T4, T5 in parallel, each followed by its verifier.
- Workflow `wf_dcef6221-e3c` (extra, 22:45): T6, T7, T12 in parallel, each followed by its verifier.
- 7 research workers active from 22:48.
- The coordinator (this session) did T2-card-1 and owns STATUS / FINAL_REPORT / RESUME / LICENCES and every commit.

## Tracks (state / cards done / cards partial)
| track | state | done | partial | notes |
|---|---|---|---|---|
| T2-card-1 overlap to 0 | DONE | T02-01 | - | coordinator; drop key board+stm (7,700 train rows), block rule measured |
| T1 v2 features + recipe | RUNNING (core2 since 22:48; first worker 22:39-22:47) | - | 6 cards on disk at 23:04 | |
| T2 data quality | RUNNING (core2 since 22:48; first worker 22:39-22:47) | T02-01 | 3 worker cards at 23:04 | |
| T4 search features | RUNNING (core2 since 22:48) | - | 6 cards at 23:04 | |
| T5 NNUE speed Zen 5 | RUNNING (core2 since 22:48) | - | 3 cards at 23:04 | |
| T6 eval post-processing | RUNNING (extra since 22:45) | - | 5 cards at 23:04 | started early (12-agent allowance) |
| T7 time management | RUNNING (extra since 22:45) | - | 2 cards at 23:04 | started early |
| T12 testing / proofs | RUNNING (extra since 22:45) | - | 3 cards at 23:04 | started early |
(Card states are the workers' until their verifier has run; "done" = verified.)

## Pushes
- 72c0de40 (22:27) start files; 69deca20 (22:36) tools + worker rules; d97bee72 (22:46) T02-01; 8a505482 (22:50)
  workflow scripts + prompts + redaction filter; 223ad8c4 (22:53) skills; 298a09b0 (22:55) licence fix + resume;
  next: this checkpoint (23:06).

## Blockers / stopping reason
- none
