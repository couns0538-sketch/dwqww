# Native fastchess recovery check

**PASS.** The pinned fastchess runner completed two A/A rounds naturally, then loaded the saved native config with `stats=true` and continued to four cumulative rounds. A separate uninterrupted four-round control produced exactly the same opening, colors, moves, result and normal termination for every game identified by `(Round, White, Black)`.

The first checkpoint counted four games and rounds 1–2. The continued checkpoint counted eight games and rounds 1–4, with no repeated or missing opening pairs. Both final runs scored W4 D0 L4, with paired histogram `[0, 0, 4, 0, 0]`. Every A/A color pair was deterministic. All 16 games actually played across the continued run and control ended normally.

`verification.json` records the assertions. `check_resume.py` is the exact checker/driver used. The script requires a fresh output directory because it intentionally refuses to overwrite prior evidence. `protocol.json` records the executable and opening hashes. `sha256-manifest.json` covers the saved files.

## Conditions

- Both players used the frozen unchanged Forge 6.4 baseline executable.
- 5,000 nodes per move, 10+0.1 clock, Hash 64, Threads 1, OwnBook false, Ponder false, UseNNUE true, Move Overhead 10 and a fresh engine process each game.
- Four fixed unique openings, sequential order, seed 20261019.
- Two game lanes, explicit CPUs 6–7 in this cloud environment.
- No resignation, score-draw, max-move or tablebase adjudication.
- Strict runner warnings and full engine communication trace logging.
- SPRT disabled so this infrastructure check reaches its natural fixed round caps. This is not playing-strength evidence.

## Evidence layout

`resumed/` contains the initial and continued commands, per-tranche stdout and trace logs, native checkpoints, a frozen initial PGN and the cumulative final PGN. `control/` contains the corresponding uninterrupted control evidence. The driver verified that the first checkpoint, its command, initial PGN snapshot and all earlier logs retained their SHA-256 hashes after continuation.

The continuation puts `-rounds 4` after `-config ... stats=true` and reapplies `-use-affinity 6,7` and `-strict`. The native runner appends to its existing PGN. Distinct per-tranche trace filenames prevent an old log from being truncated.

The A/A pair totals have zero measured variance. The runner therefore displays some `nan`/`inf` rating diagnostics. They are retained in the raw logs and are not an Elo claim or a failed outcome check.

This test verifies a naturally completed checkpoint. It does not validate recovery after an arbitrary interruption or an SPRT terminal boundary. See `../../forge-fastchess-resume-review.md` for the source review explaining that limitation.
