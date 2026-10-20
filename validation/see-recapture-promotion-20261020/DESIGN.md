# Bounded source17 proposal: promotion-aware rare SEE path

Status: research and design only. No source17 implementation, Board compilation,
production/Git/docs/ledger edit, match, timing comparison, or acceptance decision
was made. The next implementation should be a small isolated correctness
candidate against frozen source16.

## Reproduced priority and exact identities

Source16 is 553caef144ae2e1b696ba35d7a0eb1a50a03fde9.
Its Board source SHA-256 is
239f1475fd48e9dba3babefe2399b22de5962f42e7a90a775271dbe49f6f6f31.
The actual Release16 core is
a7718ec0555715e45b3aa96789754047e03db3104748a0fe8e03404e8695c267.
The existing driver object
751b503bf7ec38b7011b38cc304e41a14a9147a296d40dff9d85b7b17185f1ef
was linked without recompilation. Its Board/bitboard headers match source16.
The actual linked API executable is
6c61a80cb87a79546509d824b6f188e3d03db50656fb017cde86fb843924a643.

Every row below has a mirrored opposite-color control. All ten FENs and initial
moves are valid/legal. Python-chess 1.11.2 complete legal same-target capture
trees, including all four promotions, optional stopping, and promotion material
gain, were frozen before linking or executing the actual API.

| Control | Oracle exchange | Source16 exchange | At threshold 0 |
| --- | ---: | ---: | --- |
| Later own promotion saves rook capture | +500 | -100 | False negative |
| First enemy promotion poisons rook capture | -600 | +200 | False positive |
| Promoting recapturer is absolutely pinned | +500 | +500 | Agrees |
| Promoted recapturer is captured by king | +300 | +300 | Agrees |
| Original inherited queen/rook control | -1200 | -400 | Both reject |

The false negative is the higher-priority opportunity: at
1r6/P1Q5/2n4k/8/8/8/8/7K w - - 0 1, move c7b8, source16's see_ge(0)
returns false. The only first recapture is c6b8, but White then has a7b8q:
Black's knight recapture gains 900 and permits White to gain 300+800=1100.
Black can decline that losing exchange, so the target-only oracle gives +500.
The ordinary SEE incorrectly cuts off the sequence at a negative bound before
considering the saving promotion. The mirrored position reproduces the same
false negative.

At 7k/8/8/8/8/7K/p2N4/1r6 w - - 0 1, d2b1, source16 actually returns
+200, not the proposed +500 hypothesis. Black a2b1q gains 300+800=1100,
so the oracle is 500-1100=-600. Source16 returns true at threshold zero.
Both this false positive and its mirror are confirmed.

The ten actual API rows have six exchange-value disagreements and 44 wrong
answers among the frozen 200 threshold queries. There are no API legality or
first-recapture-set disagreements. Eight cases are new; the original two
limitations remain controls. No invalid fixture was encountered; the empty
invalid-fixtures-attempt1.json records that explicitly. The only actual API run
used 0.213885 seconds of the 30-second operational budget.

## One narrowly guarded fallback

Keep the source16 SEE implementation unchanged when the guard is false.
After the existing castle handling and initial from/to/captured-square metadata,
but before either original threshold bound, dispatch to a private promotion
exchange helper only if:

1. The initial mover is not a king.
2. The target is on rank 8 or rank 1.
3. A live original pawn of the corresponding promoting color geometrically
   attacks that target after excluding the initial origin and captured square
   (including the EP victim square).

For rank 8 inspect White pawns using reverse Black pawn attacks from the
target; for rank 1 inspect Black pawns using reverse White pawn attacks. This
checks whichever exchange side can promote, not merely the first recapturer.
The confirmed false-negative fixture needs a pawn belonging to the initial
mover on a later ply.

Do not require that potential pawn to be an immediately legal or currently
selected recapturer. An earlier exchange can consume a pinner or change which
LVA is selected. The actual helper must still filter it legally on its turn.
This broad potential-pawn guard safely overtriggers the pinned-pawn control.

The guard is sufficient for the fixed-target exchange model: other origins
only disappear; no new pawn can arrive at an attacking origin. A pawn that
cannot already attack a last-rank target cannot later promote onto it during a
sequence consisting solely of captures onto that target. Excluding the initial
pawn origin avoids mistaking the initial promotion for a future recapture.

Explicitly retain initial king/castle handling. Legal king moves terminate
without recapture, and the old king-valued-zero threshold result should remain
unchanged even for pseudo-legal inputs. A friendly potential promoting pawn
must not route an initial king move through a helper that might model a king
being captured.

## Rare helper: full gain stack with the same LVA choices

Use a fixed 64-entry stack to bound even parser-accepted nonstandard material
counts. Initialize virtual occupancy and target attackers exactly as source16,
including EP and target ghosts. Preserve its dynamic pin mask, original
Pawn/Knight/Bishop/Rook/Queen/King ordering, and lsb tie choice.

Initialize:

    gain[0] = initial_captured_value + initial_promotion_bonus
    victim = initial_resulting_piece_value

For each selected legal non-king recapture:

    bonus = 800 if this pawn promotes on the target, otherwise 0
    next = depth + 1
    gain[next] = victim + bonus - gain[depth]
    depth = next
    victim = Queen_value if promotion, otherwise selected_origin_piece_value

Remove only the selected origin, leave the target occupied, and update rays
exactly as source16. Selection still
treats a promoting pawn as the original least-valued pawn; only its resulting
target value becomes a queen.

After reaching the end of the exchange, fold backward:

    for d from depth down to 1:
        gain[d - 1] = min(gain[d - 1], -gain[d])

Return gain[0] >= threshold. The fold implements optional stopping for each
side. Do not branch across every legal attacker: this remains LVA SEE.

The king branch stays terminal. Only append a king capture when the existing
raw geometric defender test permits it; otherwise end without that capture.
Use the current target victim value for the king's gain, then stop. Preserve
geometric pinned defenders and never continue after a king capture. The
promotion-then-king-recapture control proves why both promotion bonus and the
new victim value are necessary: the extra 800 cancels when the queen is taken,
and the correct result remains +300.

For recapture promotions, queen suffices inside this limited target-only
material model: if immediately recaptured, extra promotion value cancels with
the larger captured victim value; if retained, it benefits the promoting side.
All four promotion choices have the same own-king safety after moving the pawn.
A subsequent capture removes the promoted target before testing its mover's
king safety, so that capture's legality does not depend on the captured
promotion type. Off-target underpromotion tactics and forced check evasions
are outside the optional-stop target-only model. Initial underpromotion moves
must still use the promotion type actually selected by the caller.

## Threshold and caller constraints

The original lower material bound assumes the mover cannot lose more than the
initial attacker value. An opponent promotion adds material and invalidates it:
the confirmed d2b1 false positive can return before inspecting recapturers.
The original inner threshold exit can also discard a later saving promotion:
the confirmed c7b8 false negative demonstrates that separately.

Dispatch before the old bounds and initially omit all threshold/material
shortcuts inside the rare helper. Although the initial capture-gain upper bound
can be justified under optional stopping, retaining selected shortcuts adds
proof obligations without being necessary for this first bounded repair.
Compare the completed stack result with threshold once. Do not change the old
ordinary path's threshold logic.

Initial move legality remains the caller's responsibility: MovePicker uses SEE
on pseudo-legal captures before the main search legality check. The helper must
tolerate those valid-field inputs, not become an initial-move legality API.
Static_exchange's existing binary-search/clamping interface should remain;
avoid a wider redesign merely to skip repeated rare-helper work.

## Minimal implementation and validation recommendation

Proceed as an isolated source17 correctness candidate with one guard and one
private rare helper. Do not change search pruning, evaluation, LVA selection,
the source16 ordinary filter, king-defense semantics, or public UCI options.
The independent source reviewer agreed with the guard, gain arithmetic,
queen-choice argument, and need to avoid the legacy rare-path threshold exits.

First make the ten frozen cases agree with their actual oracle values and all
saved thresholds, explicitly verifying the two corrected threshold-zero false
negatives and two corrected false positives. Retain the four already-correct
pin/king controls.

Then classify the existing immutable 316-case corpus by guard outcome. Require
byte-identical source16 output when the guard is false. For guard-true cases,
create separate new expectations from the preserved oracle; do not rewrite old
raw artifacts. Update the two previously expected promotion limitations to
correct -1200 values only in the new candidate's assertions. Add bounded
implementation checks for initial kings, quiet last-rank targets, initial
underpromotions, and a potential pawn released only on a later exchange.

Run the relevant full correctness/sanitizer/UCI gates on the frozen candidate.
Search signatures can intentionally change, so compare legal behavior and
explained SEE outcomes rather than demanding whole-search parity. LVA and
optional-stop approximations remain disclosed. No universal minimax, speed,
playing-strength, or Elo claim is supported by this research.
