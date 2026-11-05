# Forge deep research - RESUME (handoff)

Read first: `FINAL_REPORT.md` (state FINAL; top 10, gate plan, next three crew experiments, section 12 = where each
brief deliverable is), then `STATUS.md` (every workflow run with its id, times and token count; owner instructions;
crew decisions), `notes/RANKING_FINAL.md` (all idea families ranked) and `notes/CRITIC4.md` (the report check). Method
and tools: `skills/forge-deep-research/SKILL.md` (also installed as a user-scope skill on grok-pc).

## Finished
- Round 1 (22:23-00:00): T02-01 (coordinator) + T01, T02, T04, T05, T06, T07, T12, each verified; phase 2 critic +
  second vote; card fixer.
- Round 2 (00:00-02:31): T04B-T04H, T04N, T05B-T05F, T06B, T06C, T02B, T01B, T12B with Fable verifiers; specs
  SPEC_SEARCH / SPEC_EVAL; CRITIC2; RANKING_DRAFT; INTERIM 2 report (02:29).
- Round 3 (after the usage reset, 03:42 on; at most 3 workers, crew board `D:/grok-pc-data/dwqww/WORKER_BOARD.md`):
  T04P-01 (own port caissa_c123 = form B, never gated), T04Q lock audit (no bug >= 1 Elo), T04O / T04R / T04S / T04T /
  T04U new engines (cards T04R-01..03, T04S-01..02, T04T-01..03, T04U-01), T06D / T06E HCE terms (T06D-01..03, T06E-01..02), the T1 cost table (T01C), |eval| caps (T02C: not found), T12C
  counter-evidence, second votes 2 and 3, specs SPEC_SEARCH2 / SPEC_SEARCH3 / SPEC_SPEED with Fable reviews, fixes
  rounds 3-7, RANKING_FINAL, CRITIC4, FINAL report.

## Open
- Nothing is running: the last research run POOL3M was killed at 07:09:00 (session restart; partial notes, unverified)
  and the pin test of the fixed pool script ran 07:26-07:29 (ids, times and tokens in STATUS). A later session runs only
  new tasks in a FRESH run (never resume a run), at most 3 workers on the board; the pool script pins agent type +
  model id + effort max on its one call per task (Code Review 2cdf70ff: no retry, no fallback); after a failed or
  killed run release its board slots (`failed[].board_release`) and check the run with `tools/worker_audit.py`.
- Not covered by any track: see FINAL_REPORT section 11 (CRITIC.md "Uncovered or partly covered" list); PENDING items
  in the cards; unread PR pages in notes/T04T/sources.md and notes/T04U/TABLE.md.

## Next useful questions (if a later session continues)
1. The crew's first three gates (FINAL_REPORT section 4): E3 exe `EvalRule50Damp=60`, caissa_c123
   `TtCutExtraMargin=72`, then the Phase 1 kit build with `QuietMalusDecay=8` first.
2. A Threads=1 gate-rate measurement and the crew's LTC time control (owner item 2) to replace the assumed costs.
3. The last NOT COVERED brief question, within-train board+stm duplicates (a crew measurement; the other two were
   answered in round 3: notes/T01/FEATURE_COST_TABLE.md, notes/T02C/TABLE.md), and the older cards' pre-decision
   cost lines.

## Blockers / open checks
- Usage: no meter readable by this session; owner reading 77 % of the 5-hour window at ~02:26 (reset ~03:40), none
  since. Low-usage rule (<= 10 % left or a warning): write `F:/odr/work/pool_wrapup.txt` (workers stop within ~10 min;
  the owner's hook may refuse TaskStop while 3 agents run), commit, push, verify, mark the report STOPPED EARLY - LOW
  USAGE.
