# Forge deep research - RESUME (handoff)

Read first: `STATUS.md` (track table, workflows, pushes), then `cards/` and `notes/` of the track you continue.
Method and tools: `skills/forge-deep-research/SKILL.md` (also installed as a user-scope skill on grok-pc).

## Finished
- Setup: branch `opus-deepres-20261104` from main 5176ddf7 in the partial + sparse clone `F:\odr\wt`
  (`git clone --filter=blob:none --depth 1 --branch main --no-checkout`, `MSYS_NO_PATHCONV=1 git sparse-checkout set
  --no-cone /opus_deepres/ /skills/`, `core.autocrlf false`, clean filter `novendor` = `tools/novendor_filter.py`).
- Tools (`tools/`): mine_commits.py, licence_at.py (GPL/AGPL guess fixed 22:53-22:54), forge_has.sh, card_lint.py,
  tried_gates.py, block_rule_check.py, merge_licences.py, workflow_prompts.py, novendor_filter.py; workflow scripts
  and the exact worker prompts in `tools/workflows/`.
- T2-card-1 = `cards/T02/T02-01-overlap-to-zero.md` (COMPLETE): drop key board+stm (the J1 binpack has no castling /
  EP), 7,700 train rows from `D:\a14\sep\BOARDSTM_TRIAGE_ROWS.tsv` (minimum 4,118 for the EP-normalised key), rebuild
  + 5 proofs, block rule measured (`notes/T02/block_rule_012_015.json`), costs from measured logs.

## Running (as of the last STATUS update)
- `wf_b823f43e-496` core2: T1, T2 (both continuing the stopped first run's files), T4, T5; then one verifier each.
- `wf_dcef6221-e3c` extra: T6, T7, T12; then one verifier each.
- If this session ended: the workflows end with it. Every worker saves as it goes, so `cards/T<nn>/` and
  `notes/T<nn>/sources.md` show exactly how far each track got; restart a track with `tools/workflows/deepres_tracks.js`
  and a `continue_note` pointing at those files (see `tools/workflows/README.md`).

## Next steps (coordinator)
1. At each ~10-minute checkpoint: `python -I -B tools/merge_licences.py`, `python -I -B tools/card_lint.py`, update
   STATUS (track table + latest pushed commit), commit through the filter, push, `git ls-remote` check.
2. When a workflow finishes: read its hand-backs (journal.jsonl in the workflow transcript folder), rank every card by
   expected Elo per crew-hour, write the INTERIM report (due ~02:23) and then the core report.
3. With agents still allowed (up to 12): a second adversarial check of the top-10 cards and one completeness critic
   over all tracks before the final report.
4. 07:53: no new questions; 08:23: hard stop (report FINAL or STOPPED - TIME LIMIT).

## Blockers / open checks
- USAGE UNKNOWN (no meter readable). Low-usage warning -> TaskStop both workflows, commit, push, verify, then mark the
  report STOPPED EARLY - LOW USAGE.
