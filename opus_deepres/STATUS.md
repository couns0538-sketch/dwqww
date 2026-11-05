# Forge deep research - STATUS

Branch `opus-deepres-20261104` (fresh from `main` 5176ddf7), repo couns0538-sketch/dwqww. Local clone `F:\odr\wt`
(partial + sparse: only `opus_deepres/` and `skills/` are checked out). Scratch `F:\odr\` (cap 5 GB). Nothing of
this job is written to D:.

## Clock and limits
- Start: **2026-11-04 22:23:27 PC clock** (first `date` of the job; the PC prints PST -0800, earlier notes call it
  the Vienna wall time - all times here are the PC clock as printed).
- Hard deadline (10 h): **2026-11-05 08:23:27**. No new research questions after **07:53:27** (9 h 30 min).
- INTERIM report due: about **2026-11-05 02:23** (4 h).
- Last update of this file: 06:24 (elapsed 8 h 01 min).
- INTERIM report: written 23:40 (FINAL_REPORT.md state line), well before the 02:23 due time.
- Measured agent spend so far: core workflow wf_b823f43e-496 = 1,802,872 agent tokens (8 agents, 2,710 s); extra
  workflow wf_dcef6221-e3c = 1,149,308 (6 agents, 3,325 s); together 2,952,180, plus the stopped first run (2 agents,
  22:39-22:47, not reported by the tool). All 34 cards lint clean at 23:43.
- Usage: this session cannot read a usage meter itself. Readings given by the owner: before 01:35 "usage limit of 5h
  is running out" (agents cut from 10 to 3); just before 02:26:51 "5 hour window is at 77 percent resets in 1 hour
  14min" = 23 % left, reset about 03:40. Plan: no new agents until the reset (the light pool's last verifier finishes
  by itself), the coordinator writes the FINAL report now; after 03:40 a 3-worker pool (owner cap: at most 3 parallel workers, fable / opus-max only, coordinated via D:\grok-pc-data\dwqww\WORKER_BOARD.md) on non-overlapping tasks until
  07:20. The low-usage rule (<= 10 % left) still triggers the immediate save-and-push.
- POOL3 started 03:42 (wf_8ee06337-6bc, right after the reset). Stop path: the owner's worker-cap hook refuses every Agent /
  Task / Workflow tool call, TaskStop included, while 3 agents are active, so the pool has a cooperative wrap-up
  note for its own workers (`F:/odr/work/pool_wrapup.txt`; every worker checks it before each source and every
  10 minutes, saves, frees its board slot and hands back; no new task starts after one sees it).
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

## Owner instruction of ~23:55 (round 2)
- Received before 23:55:24 (clock read right after it): "use 10 agents for the next 5 hours then 5 agents for 5 hours
  and only finish when the 10h window is done find more improvements for forge even if more agents are needed and dont
  use [name withheld] or [name withheld] use yourself opus 5.5 at max or fable 5.1 at max".
- Read as: 10 agents at a time until ~04:55, then 5 agents until the job's 10-hour window ends at 08:23 (the brief's hard
  deadline stays; the owner was told this reading and can extend it). Agents: research workers inherit this session's
  model at max effort; verifiers run as Fable 5.1 at max effort; no smaller models. More cards than the brief's
  6-per-track / 60-total caps are wanted now: new sub-tracks (T04B ... T05C) have at most 4 cards each, and the total
  can exceed 60 - that is the owner's call of 23:55, recorded here.
- Workflow `wf_3b675c3a-16b` (round 2A, script file stamped 23:57:02; an earlier push of this line said "23:58",
  written before the clock was read - corrected): T04B Stormphrax + Obsidian logs, T04C PlentyChess + Berserk
  + Alexandria logs, T04D Stockfish search commits since 2024, T04E Reckless + Viridithas, T04F feature diff vs Caissa,
  T04G move ordering / history diff vs Altair + Patricia, T05B HCE eval speed (own code), T05C board / movegen / SEE
  speed (own code); each followed by a Fable verifier. With phase 2's two agents: 10 agents active.

## Crew decisions and owner cap (received before 02:37)
- Crew decision (7-0 vote, received 2026-11-05 before 02:37): every search gate runs Threads=1; SPRT [0,5] in normalized Elo (not BayesElo), alpha = beta = 0.05, pentanomial, cap 3,000 games; a run that hits the cap without a decision is logged UNPROVEN / no decision (not H0, not a pass), and if its Elo is positive it gets exactly one extension.
- Owner cap: at most 3 parallel workers (not 5), fable or opus-max agents only, coordinating via `D:\grok-pc-data\dwqww\WORKER_BOARD.md` (three slot lines, so never more than 3 active; `tools/board.py`); "usage is very low": the coordinator works alone until 03:41, then the 3-worker pool starts.

## Tracks (state / cards done / cards partial)
| track | state | done | partial | notes |
|---|---|---|---|---|
| POOL3K (HCE leads + speed-spec fixes) | RUNNING since 06:24 (wf_e583e970-4e2, 2 workers) | - | - | T06E: the HCE leads T06D left unread (queen threats SF 6d8f583 / 1093047 + Berserk PR 219, Sirius PR 185 / 258, Perseus PR 100), max 3 cards + Fable verify; SPECFIX2: the 10 SPEC_SPEED_REVIEW fix items into SPEC_SPEED (round 7) |
| POOL3J (last card run) | DONE 06:06-06:24 (2 agents, 299,582 agent tokens; T04U-01 check extension moved into LMR (Clockwork #281 STC +5.82 / LTC +3.35, [0,5], UHO; 0 to +3 UNPROVEN, ~2 crew h); verify 26 of 26 confirmed); started (wf_9c238198-477, 1 worker) | - | - | T04U: Clockwork #281 (check extension moved into LMR; T04T's best uncarded candidate), then the unread PR pages (Clockwork 4+, Tarnished 2+, motor 3+); max 3 cards; research 30 min + Fable verify 10 min |
| POOL3I (report critic) | DONE 05:42-05:56 (1 agent, 222,633 agent tokens; notes/CRITIC4.md: 13 findings, 3 wrong / 2 misleading / 8 wording; finding 3 rejected after a check: T02-01 names the 37 train files at lines 19 and 22); started (wf_eb0e5f99-576, 1 worker; total 3 with POOL3H) | - | - | CRITIC4: Fable check of FINAL_REPORT.md INTERIM 4 (numbers vs cards / notes, five greps, brief coverage vs notes/CRITIC.md Part A, rule checks, section 2 arithmetic) -> notes/CRITIC4.md |
| POOL3H (last research run) | DONE 05:39-06:05 (4 agents, 695,899 agent tokens; T04T 3 cards (Clockwork, pawnocchio PR bodies; 3 confirmed), T06D 3 cards (king flank attacks, pin-aware eval one-liner, endgame winnability; 3 confirmed, 1 correction)); started (wf_11a93894-6db, 2 workers; total 2 + the coordinator's report critic later = 3) | - | - | T04T: logs of engines never read (pawnocchio, Clockwork search PRs, Seer, Carp, Willow, Horsie; max 3 cards) + Fable verify; T06D: hand-crafted eval terms with logged Elo that the lock's HCE lacks (new angle: the lock is HCE + a residual net; fit with the residual frozen; max 3 cards) + Fable verify |
| POOL3G (POOL3E's slot) | DONE 05:26-05:34 (1 agent, 150,775 agent tokens; FIXER4 round 6 on T04R-01, T04N-03, T04E-01, T04G-05; anchor :1153 corrected to :1154-1156); started (wf_ac834933-860, 1 worker; the hook refused two launches at 05:22 and 05:24 while finished workers were still inside its 3-minute window) | - | - | FIXER4: VOTE3 KEEP-WITH-FIX items on T04R-01, T04N-03, T04E-01, T04G-05 (round 6) |
| POOL3F (POOL3B's slot) | DONE 05:03-05:34 (2 agents, 389,429 agent tokens; T04S logs-only from Sirius, motor, Tarnished PR bodies: T04S-01 continuation-history update with the summed continuation score as gravity base (Sirius STC +5.86 / LTC +14.38, Tarnished STC +2.23 / LTC +2.53, Clockwork STC +14.67), T04S-02 upcoming-repetition test in search (Sirius STC +5.29, Viridithas LTC +2.27); Fable verify: 2 confirmed, 1 correction (the Sirius STC was a blend form; pure sum vs blend +3.23 at 29k games)); started (wf_7f411aab-ab9, 1 worker) | - | - | T04S: logs-only mining (titles, messages, PR text, test logs; no source) of the five engines T04O skipped for licence (Sirius, Motor, Starzix, Pawnocchio, Tarnished; CRITIC3 item 10 coverage gap), max 3 cards, + Fable verifier |
| POOL3E (POOL3C's slot) | DONE 04:57-05:19 (2 agents, 325,548 agent tokens; SPECFIX round 5 = every SPEC_REVIEW fix, pseudo-legality anchor corrected to search.cpp:326; VOTE3 = notes/TOP_SECOND_VOTE3.md: 2 KEEP, 4 KEEP-WITH-FIX, 0 DOWNGRADE / DROP); started (wf_e78d3813-13f, 1 worker) | - | - | SPECFIX (the SPEC_REVIEW FIX items into SPEC_SEARCH2 / SPEC_SEARCH3, log round 5), then VOTE3 (Fable second vote on T04P-01, T04R-01, T04N-03, T05F-01, T04E-01, T04G-05 -> notes/TOP_SECOND_VOTE3.md) |
| POOL3D (POOL3's slot) | DONE 04:53-05:36 (3 agents, 596,161 agent tokens; FIXER3 round 4 (14 cards), SPEC4 = notes/SPEC_SPEED.md, SPECREV2 = notes/SPEC_SPEED_REVIEW.md); started (wf_a094ef98-2de, 1 worker) | - | - | FIXER3 (CRITIC3 items 4-6 of RANKING_FINAL, second vote 2 fixes, counter-evidence lines from notes/T12C/COUNTER.md on the cards it lowers), SPEC4 (specs for the speed rows S1-S4 -> notes/SPEC_SPEED.md), SPECREV2 (Fable review -> notes/SPEC_SPEED_REVIEW.md) |
| POOL3C (free slot again) | DONE 04:25-04:53 (2 agents, 334,288 agent tokens; SPEC3 -> notes/SPEC_SEARCH3.md 04:39, SPECREV -> notes/SPEC_REVIEW.md 04:53: no blocker, one code fix for T04E-02, three wording fixes); started (wf_3aad16a2-a30, same script, 1 worker; the hook refused the first launch at 04:23 because a finished worker's transcript was still inside its 3-minute window) | - | - | SPEC2 ended at 04:21, so POOL3 runs one task at a time from then on (T04O, its verifier, RANK3) and POOL3B one (T12C, T04R, verifier): total <= 3 with this run. SPEC3 (specs for T04C-02, T04F-01, T04N-01, T04N-02, T04P-01 -> notes/SPEC_SEARCH3.md), then SPECREV (Fable review of SPEC_SEARCH2 + SPEC_SEARCH3 against the lock -> notes/SPEC_REVIEW.md) |
| POOL3B (free slot) | DONE 04:22-05:01 (3 agents, 514,776 agent tokens; T12C COUNTER.md 04:35, T04R 3 cards (Renegade MIT; Clover, Simbelmyne logs) + Fable verify: 3 confirmed, 0 violations, 0 duplicates); started (wf_04149913-550, same script, 1 worker) | - | - | POOL3 had only 2 tasks left that can run at once (SPEC2, T04O, then its verifier, then RANK3 alone), so its third slot sat idle from 04:17; this run uses it, total stays <= 3: T12C counter-evidence for the top 10 (failed / neutral tests of the same ideas elsewhere), then T04R (engines whose logs were never read; max 3 cards) + Fable verifier. tools/board.py now takes another idle slot when the named one is busy and releases by worker + task (tested on a copy of the board: busy slot -> free one, full board -> waits 10 min then exit 3, done releases the right slot) |
| POOL3 (after the reset) | DONE 03:42-04:51: 10 agents, 1,690,105 agent tokens, 3,873 s; 5 "failed" in the journal = spawns with agent type opus-max, which is not in this session's agent registry (its file came after the session start): no agent started, each of those tasks then ran as Opus 5.5 at effort max through the fallback; the fable agent type worked. Results: T04P (1 card) + verify, FIXER2 (round 3 fixes), T04Q (lock audit: 3 minor HITs, all < 1 Elo or already carded, 0 cards; verifier agrees) + verify, VOTE2, SPEC2 (04:21), T04O (0 cards; evidence rows, e.g. akimbo for T01B-02 and T04N-01) + verify, RANK3 = notes/RANKING_FINAL.md (04:48, corrected 04:51) (wf_8ee06337-6bc, tools/workflows/deepres_pool3.js; 3 workers = owner cap, agent types opus-max / fable, board slots S1-S3) | - | - | queue: T04Q lock-source audit against notes/T04/BUG_CHECKLIST.md, T04P deeper-entry TT cutoff (1 card), FIXER2 (open CRITIC2 fixes), VOTE2 (Fable second vote on 10 round-2 top cards), SPEC2 (specs for T04E-03, T04E-02, T04B-01, T04D-01, T04D-02), T04O (permissive engines not mined yet), RANK3 (Fable, final ranking + CRITIC3, only after all others, not after 06:50); a Fable verifier after each research task; nothing new after 07:20 |
| T2-card-1 overlap to 0 | DONE | T02-01 | - | coordinator; drop key board+stm (7,700 train rows), block rule measured |
| T1 v2 features + recipe | VERIFIED (research 22:48-23:09, verify -23:2x) | T01-01..06 | - | 54 checks, 47 confirmed, 5 corrected |
| T2 data quality | VERIFIED (research -23:20, verify 23:20-23:32) | T02-01 (coordinator), T02-02..06 | - | 68 checks, 54 confirmed, 6 corrected, 7 unverifiable, 1 violation (MIX.md constant; fixed by the coordinator 23:34) |
| T4 search features | VERIFIED (research 22:48-23:14, verify 23:15-23:25) | T04-01..06 | - | 55 checks, 46 confirmed, 7 corrected, 0 violations |
| T5 NNUE speed Zen 5 | VERIFIED (research -23:16, verify 23:20-23:33 per notes/T05/VERIFY.md) | T05-01..04 | - | 58 checks, 54 confirmed, 1 corrected, 3 unverifiable, 0 violations |
| T6 eval post-processing | VERIFIED (research 22:45-23:11, verify 23:11-23:22) | T06-01..05 | - | 48 checks, 44 confirmed, 2 corrected |
| T7 time management | VERIFIED (verify 23:09-23:17) | T07-01..02 | - | 40 checks, 31 confirmed, 5 corrected, 1 process note |
| T12 testing / proofs | VERIFIED (research 22:45-23:29, verify 23:30-23:40) | T12-01..05 | - | 51 checks, 44 confirmed, 4 corrected, 3 unverifiable, 0 violations |
| Phase 2 cross-track checks | DONE (wf_576c2a36-f48, 23:43-00:01; 541,874 agent tokens) | notes/CRITIC.md (82-row coverage matrix, report check), notes/TOP_SECOND_VOTE.md (12 cards: 4 KEEP, 6 KEEP-WITH-FIX, 3 DOWNGRADE incl. one counted twice, 0 DROP) | - | main finding: T04-02 and T06-05 already exist in own packb code (ReSearchAdjust / FiftyDamp), gated only as a bundle on old bases |
| Round 2A (8 sub-tracks) | STOPPED 00:20 (wf_3b675c3a-16b, script 23:57:02) | - | files on disk, continued in the pool | owner suggestion: one dynamic workflow |
| Round 2B | STOPPED 00:20 (wf_d0a63a18-8e5, script 00:04:06) | - | files on disk (fixer log 59 lines), continued in the pool | |
| OWNER (received before 01:35) | "make sure no research ais studie the same thing ... usage limit of 5h is running out so please make a few less agents" | - | - | treated as the brief's explicit low-usage warning: pool2 STOPPED at 01:35, everything pushed (44a4e6f9, 01:36); the topic sub-tracks T04I-T04M (LMR inputs, extensions, null move, futility, qsearch) were DROPPED as overlapping the per-engine mining of T04B-T04G (they had written no card); T04O (more permissive engines) dropped to save usage; no planner from now on |
| LIGHT POOL | DONE (wf_e14384be-3bb, 01:38 to ~02:31; 3 workers, no planner; 10 agents, 0 errors, 1,667,660 agent tokens, 3,203 s) | 4 verifier continuations, CRITIC2, RANKING_DRAFT, T04N (3 cards) + verify, T05F (1 card) + verify | - | owner, after 01:37: "make a workflow that consumes a bit less tokens then resume so the 5h window resets in time it resets in about 2h" -> light mode until the usage window resets (~03:40 by the owner's estimate), then a larger pool again for new, non-overlapping research; queue order: 4 verifier continuations (15 min each), CRITIC2 (Fable, duplicates over ALL cards), RANKING draft, then T04N and T05F with 15-min verifiers | only non-overlapping work: the 4 unfinished verifiers (T05D, T05E, T01B, T12B), T04N (Koivisto, Ethereal, Halogen, RubiChess: never mined), T05F (lock eval-path redundancy, own code), then CRITIC2 (cross-track duplicates over ALL cards) and the ranking draft |
| POOL2 (fresh run) | STOPPED 01:35 (wf_1e5bb366-e31, script 01:31:19; ran ~4 min, 0 results) | - | - | 10 workers: the 4 verifiers stopped at 01:24 (T05D, T05E, T01B, T12B, as continuations of their partial VERIFY.md) + new sub-tracks T04I LMR inputs, T04J extensions, T04K null move, T04L futility / RFP / razoring / LMP, T04M qsearch, T04N Koivisto / Ethereal / Halogen / RubiChess logs, T04O more permissive engines, T05F lock eval-path redundancy; the planner refills when fewer than 3 research tasks wait (up to 8 per call, 12 calls, none after 06:30); late critic + ranking at 06:00; 5 workers from 04:55; nothing new after 07:20 |
| POOL resume attempts | 01:25-01:29, both STOPPED within ~2 min | - | - | the run's resume cache is call-order based: in a pool the order changes, so finished verifiers / research / specs started again live; stopped at once; only ~5 files touched (all kept); lesson in the skill: never resume a pool, start a fresh run with only the remaining tasks |
| POOL (one dynamic workflow) | DONE / STOPPED 01:24 (wf_ea481fcc-434, script 00:22:08): 30 agents finished (10 continuations, 10 verifiers, fixer, T01B, T04H, T05D, T05E, T12B, T06C research, T04H and T06C verifiers, SPEC-SEARCH, SPEC-EVAL); gap found: when the queue emptied only the planner ran | - | - | 10 workers on one queue: the 10 stopped sub-tracks as continuations + fixer + T01B, T04H, T05D, T05E, T12B, T06C + specs (SEARCH, EVAL); a Fable verifier goes to the queue front after each research task; a planner adds up to 5 sub-tracks per call (max 6 calls) when the queue is empty; at 06:00 a late critic (Fable) + ranking draft; 5 workers from 04:55, nothing new after 07:20 (times taken from the clock lines the agents hand back) |
(Card states are the workers' until their verifier has run; "done" = verified. Verify times as the verifiers wrote
them in notes/T<nn>/VERIFY.md.)

## Observations outside this job
- `C:\o13` was restructured by something outside this job between about 22:50 and 23:00 PC clock: at ~22:44 a grep
  found `C:\o13\p7\fit_e3.json` (a T06 source); at 23:15 `C:\o13` held only `p1` and `p4` (both created 23:00), and
  C: free space had risen from 84.6 GB (22:23) to 98.8 GB (23:04). A scan of every tool call of this job's workers
  (`F:\odr\work\scan_o13.py` over the workflow transcripts) shows only reads there (ls, grep, git show). The E3 fit's
  durable copy is `opus_r13/p7/logs/fit_e3.json` on branch opus-r13-p7-e3fit (the T06 verifier's correction).
- Process notes from workers (self-reported): the T07 worker and the T05 worker put temporary helper files into this
  session's scratchpad folder on C: (a pentanomial helper; objdump listings, a PDF copy and its text) instead of
  F:\odr; no job output is there and nothing was deleted.

## Pushes
- 72c0de40 (22:27) start files; 69deca20 (22:36) tools + worker rules; d97bee72 (22:46) T02-01; 8a505482 (22:50)
  workflow scripts + prompts + redaction filter; 223ad8c4 (22:53) skills; 298a09b0 (22:55) licence fix + resume;
  next: this checkpoint (23:06).

## Blockers / stopping reason
- none
