# Promotion-recapture SEE research

Confirmed a source16 SEE false negative at threshold zero for both colors.
No source17 fix has been implemented. DESIGN.md recommends one rare guarded
promotion-aware LVA gain-stack helper, leaving ordinary SEE unchanged.

| Mirrored control pair | Oracle | Actual source16 | Threshold zero |
| --- | ---: | ---: | --- |
| Own later promotion saves capture | +500 | -100 | False negative |
| Enemy first promotion poisons capture | -600 | +200 | False positive |
| Promoting pawn is pinned | +500 | +500 | Agrees |
| Promotion then king recapture | +300 | +300 | Agrees |
| Original inherited limitation | -1200 | -400 | Both reject |

All ten fixtures are valid/legal. The eight new cases are four mirrored
pairs; the original two limitations remain controls. Complete python-chess
legal same-target capture minimax trees and 20 thresholds were frozen before
the link and only actual API run. Cases, trees, and expectations were not
filtered or changed after observing source16 results.

The proposed second hypothesis did not return +500: its actual source16 SEE
is +200 against oracle -600. The false-positive conclusion still holds.
The first hypothesis is a confirmed +500 versus -100 false negative, so the
opportunity affects zero-threshold capture classification, not just ordering.

There are six exchange-value disagreements and 44 wrong answers among 200
fixed-threshold queries. All actual initial legality and complete first
recapture sets agree with the independent oracle. Source16 outputs are red
research evidence; the four already-correct pin/king cases are controls.

Only the existing diagnostic object was linked to a copied frozen Release16
core. No Board or driver source was compiled. The one actual API run used
0.213885 seconds of a 30-second operational budget.
No matches, timing/NPS comparison, source edits, Git actions, or strength
claim occurred. All previous inputs and the original source16 core remained
unchanged. There were no invalid fixture or link/API failures.

PRE-RUN-FREEZE.json, oracle-corpus.json, cases.tsv, thresholds.json,
source16-api.stdout, comparisons.json, and record.json preserve the exact
inputs, complete trees, outputs, command, exit statuses, hashes, and scope.
The copied core, driver source/object, actual executable, source16 Board,
complete source TAR, design, and independent source-only design review are
included in complete-evidence.zip.

The archive manifest covers every payload. Its byte-verification receipt
is kept outside the ZIP to avoid self-referential hashing. This bounded
research is not an implementation or candidate-acceptance result.
