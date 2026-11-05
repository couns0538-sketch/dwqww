# Forge deep research - STATUS

Branch `opus-deepres-20261104` (fresh from `main` 5176ddf7), repo couns0538-sketch/dwqww. Local clone `F:\odr\wt`
(partial + sparse: only `opus_deepres/` and `skills/` are checked out). Scratch `F:\odr\` (cap 5 GB). Nothing of
this job is written to D:.

## Clock and limits
- Start: **2026-11-04 22:23:27 PC clock** (first `date` of the job; the PC prints PST -0800, earlier notes call it
  the Vienna wall time - all times here are the PC clock as printed).
- Hard deadline (10 h): **2026-11-05 08:23:27**. No new research questions after **07:53:27** (9 h 30 min).
- INTERIM report due: about **2026-11-05 02:23** (4 h).
- Last update of this file: 22:46 (elapsed 0 h 23 min).
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
- Agents: 2 at a time at first; the owner allowed up to 12 at ~22:43 ("i allow you to launch more agents in the deep
  research up to 12"), so the optional tracks T6 / T7 / T12 started early in parallel (5 agents active).
- Workflow `wf_5cef37bf-0b9` (core): chain A = T1 then T4, chain B = T2 then T5, then the four verifiers.
- Workflow `wf_dcef6221-e3c` (extra): T6, T7, T12 in parallel, each followed by its verifier.
- The coordinator (this session) did T2-card-1 and owns STATUS / FINAL_REPORT / RESUME / LICENCES and every commit.

## Tracks (state / cards done / cards partial)
| track | state | done | partial | notes |
|---|---|---|---|---|
| T2-card-1 overlap to 0 | DONE | T02-01 | - | coordinator; drop key board+stm (7,700 train rows), block rule measured |
| T1 v2 features + recipe | RUNNING (core chain A) | - | T01-01 | worker started ~22:38 |
| T2 data quality | RUNNING (core chain B) | - | T02-02, T02-03 | worker started ~22:38 |
| T4 search features | QUEUED (chain A, after T1) | - | - | |
| T5 NNUE speed Zen 5 | QUEUED (chain B, after T2) | - | - | |
| T6 eval post-processing | RUNNING (extra) | - | - | started early (12-agent allowance) |
| T7 time management | RUNNING (extra) | - | - | started early |
| T12 testing / proofs | RUNNING (extra) | - | - | started early |

## Pushes
- 72c0de40 (22:27) start files; 69deca20 (22:36) tools + worker rules; next: this checkpoint.

## Blockers / stopping reason
- none
