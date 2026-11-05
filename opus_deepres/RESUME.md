# Forge deep research - RESUME (handoff)

Read first: `STATUS.md` (track table, workflows, pushes, observations), then `FINAL_REPORT.md` (state line says
INTERIM / FINAL / STOPPED), then `cards/` and `notes/` of the part you continue. Method and tools:
`skills/forge-deep-research/SKILL.md` (also installed as a user-scope skill on grok-pc).

## Finished (verified)
- Setup: branch `opus-deepres-20261104` from main 5176ddf7 in the partial + sparse clone `F:\odr\wt`
  (`git clone --filter=blob:none --depth 1 --branch main --no-checkout`, `MSYS_NO_PATHCONV=1 git sparse-checkout set
  --no-cone /opus_deepres/ /skills/`, `core.autocrlf false`, clean filter `novendor` = `tools/novendor_filter.py`).
- 34 cards, all lint-clean: T01 (6), T02 (6, incl. the coordinator's T02-01), T04 (6), T05 (4), T06 (5), T07 (2),
  T12 (5); each track's verifier result in `notes/T<nn>/VERIFY.md`. Track deliverables: `notes/T01/recipes.md`,
  `notes/T02/TABLE.md` + `MIX.md`, `notes/T04/TABLE.md` + `BUG_CHECKLIST.md`, `notes/T05/SPEED_LIST.md` +
  `V2P4_GAP.md`, `notes/T06/FORMS.md` + `FIT_RECIPE.md`, `notes/T07/UCI_EDGE_CASES.md`, `notes/T12/PROTOCOLS.md`.
- INTERIM report pushed at 23:42 (commit 22481219).

## Running (as of the last STATUS update)
- Phase 2 `wf_576c2a36-f48` (launched 23:43): critic -> `notes/CRITIC.md` (coverage matrix of every brief question,
  report-vs-cards check); second vote on 12 top cards -> `notes/TOP_SECOND_VOTE.md`. Neither edits cards or reports.
- If this session ended: the workflow ends with it; both agents write their file as they go, so the files show how
  far they got. Re-run with `tools/workflows/deepres_phase2_checks.js` if they are empty.

## Next steps (coordinator)
1. Apply the phase-2 findings: fix cards (with "(corrected by coordinator: ...)") and the report numbers; record
   KEEP / DOWNGRADE / DROP verdicts in the ranking.
2. Decide whether uncovered brief questions are worth one more small round (card caps: T05 has 2 card slots left,
   T06 1, T12 1; T01 / T02 / T04 are at 6).
3. Write the FINAL report (state FINAL), final STATUS / RESUME / LICENCES, commit, push, verify, then the final
   message (strongest proposals, dead ends, unfinished, next three crew experiments, links, elapsed time, spend).
4. Hard times: 07:53 no new questions; 08:23 stop.

## Blockers / open checks
- USAGE UNKNOWN (no meter readable); measured agent spend is in STATUS.md. Low-usage warning -> TaskStop the running
  workflow, commit, push, verify, then mark the report STOPPED EARLY - LOW USAGE.
