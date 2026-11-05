# Forge deep research - RESUME (handoff)

Read first: `STATUS.md` (track table, workflows, owner instructions, usage readings), then `FINAL_REPORT.md` (state line:
INTERIM 2 at 02:29), `notes/RANKING_DRAFT.md` (all cards ranked) and `notes/CRITIC2.md` (duplicates, corrections). Method
and tools: `skills/forge-deep-research/SKILL.md` (also installed as a user-scope skill on grok-pc).

## Finished
- Round 1: T02-01 (coordinator) + T01, T02, T04, T05, T06, T07, T12 (34 cards), each verified; phase 2 critic + second
  vote; card fixer (`notes/FIXES_APPLIED.md`).
- Round 2: T04B-T04H, T05B-T05E, T06B, T06C, T02B, T01B, T12B, T04N, T05F (92 card files incl. 5 merge markers), each
  with a Fable verifier except T05F (verifier running at 02:29); specs `notes/SPEC_SEARCH.md`, `notes/SPEC_EVAL.md`;
  CRITIC2 and RANKING_DRAFT.
- INTERIM 2 report pushed at 02:29 (59f107e0).

## Not finished / dropped
- Dropped as overlapping (owner 01:35, "no two agents on the same thing"): T04I-T04M topic sub-tracks; dropped for
  usage: T04O (more permissive engines). Not carded yet: "a fail-high TT cutoff needs a deeper entry" (CRITIC2 section 1).
- CRITIC2's card-level fixes are NOT applied yet (T04H-02 downgrade, T04-04 estimate 0 to +2, T04F-02 fold into a
  one-liner for R15 C5, notes/T04/TABLE.md rows 33 and 46, notes/T05/SPEED_LIST.md R7TtExclusive wording, T04C-02 cite
  the larger-n Stockfish pair, T04E-03 own start values check, "768 KiB (786 KB)").

## Plan after the usage-window reset (owner: reset ~03:40)
A fresh pool (never resume a pool) of 3 workers (owner cap; board D:/grok-pc-data/dwqww/WORKER_BOARD.md), only non-overlapping tasks: (1) card for the deeper-entry TT-cutoff
rule from the existing TABLE rows; (2) T04O permissive engines; (3) Fable second vote on the round-2 top cards (T04D-01,
T04D-02, T04C-02, T04E-02, T04F-01, T04B-01, T04E-04, T04E-03, T04N-01, T04N-02); (4) own-words specs for T04E-03,
T04E-02, T04B-01, T04D-01, T04D-02; (5) fixer for the CRITIC2 items above; (6) at ~06:30 a refreshed ranking + a short
critic; then FINAL report by ~07:50, push, verify; 07:53 no new questions; 08:23 hard stop.

## Blockers / open checks
- Usage: owner reading 77 % of the 5-hour window at ~02:26 (reset ~03:40). Low-usage rule (<= 10 % left or a warning):
  TaskStop the running workflow, commit, push, verify, mark the report STOPPED EARLY - LOW USAGE.
