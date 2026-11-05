# Forge deep research - FINAL REPORT

**State: IN PROGRESS** (not INTERIM, not FINAL). Sections marked PENDING are not done yet.

Started 2026-11-04 22:23:27 PC clock; deadline 2026-11-05 08:23:27. Branch `opus-deepres-20261104`.
No Elo claim for Forge anywhere: every source number is quoted with its link and conditions, every Forge-side
estimate is labelled UNPROVEN; the crew gates. Cards: `cards/T<nn>/`; per-track notes, tables and the verifiers'
findings: `notes/T<nn>/` (`VERIFY.md`); licences at the exact commits read: `LICENCES.md`.

## 0. First: the data blocker (T2-card-1, card T02-01, COMPLETE)
The J1 npt train binpack is written from FPOS rows, which carry no castling, no en passant and no clocks, so the net
sees board + side to move only: that is the leak key, and it subsumes the 4,088 EP-normalised keys. Drop the 7,700
train rows already listed (path + line) in `D:\a14\sep\BOARDSTM_TRIAGE_ROWS.tsv` (0.0025 % of 304,999,573; the
minimum for "4,088 -> 0" is 4,118), rebuild the 37 train shards with the same converter, prove count / dropped keys /
0 shared keys on all three keys / seals. Game level: no authentic game IDs exist; a cheap block rule (new block when
the result changes or the ply does not increase) reproduces the R14 scan's break classes within 16 of 189k pairs and
shows both train/holdout seams are breaks, so the 013/014 split is block-aligned already. Cost: under 30 CPU-minutes
on one core (measured logs), 10.4 GB on C:, crew ~2 h. Direct Elo: none expected (enabler).

## 1. Top 10 by expected Elo per crew-hour (suggested gate order)
PENDING (after the core tracks' verifiers)

## 2. All cards ranked
PENDING

## 3. Ideas already in Forge
PENDING

## 4. Dead ends
PENDING

## 5. Skills, scripts and tools created or improved
- Skill `skills/forge-deep-research/SKILL.md` (new; also installed as a user-scope skill on grok-pc): setup, tools,
  worker rules, the custom workflow, checkpoints, the low-usage stop, pitfalls.
- Skill `skills/forge-pc-rules/SKILL.md` (branch copy of the project skill with this job's section; the commit-trailer
  line made brief-dependent; the D: project copy could not be updated - this job writes nothing to D:).
- Tools in `opus_deepres/tools/` (one-line usage in each file's docstring): `mine_commits.py` (commit titles + parsed
  SPRT blocks), `licence_at.py` (LICENSE at an exact commit; GPL/AGPL guess fixed during the job), `forge_has.sh`
  (lock-source grep), `card_lint.py`, `tried_gates.py` (FORGE_RESULTS.csv), `block_rule_check.py` (game blocks),
  `merge_licences.py`, `workflow_prompts.py`, `novendor_filter.py` (git clean filter).
- Workflows `opus_deepres/tools/workflows/` (`deepres_tracks.js` generic research + verify per track; the exact worker
  prompts in `prompts_core2/`, `prompts_extra/`).

## 6. Incomplete or blocked work
Everything except T02-01 is still running (see STATUS.md).
