# Independent applied-source17 SEE review

Decision: no material source-integration or correctness blocker found in the
reviewed change. The applied Board implementation is byte-identical to the
reviewed, bounded-tested prototype. This review adds no full-engine, speed,
strength, or release-acceptance claim.

Scope: read-only source/artifact review of source17
47f0560221d986e41a309853e1295c557fcf5bf6 against source16
553caef144ae2e1b696ba35d7a0eb1a50a03fde9. No engine, compiler, match, Git
mutation, or production-file edit was performed. A pure python-chess legality
check independently validated the single optional full-search fixture below.
The only written artifact is this review.

## Applied implementation matches the frozen prototype

The committed source17 src/board.cpp, current Board source, and
validation/see-recapture-promotion-20261020/prototype/candidate-board.cpp all
have SHA-256:

    ad3290611e5f88d95b8fd0f674370eadc17e0c529902fba3e92ac48ac46ed239

The source16-to17 code diff adds the anonymous-namespace helper and one guarded
dispatch. Board headers/class definitions and search.cpp are unchanged.
Remaining production-file changes are version labels; permanent tests add five
positions mirrored for both colors to the existing table. There is no
prototype/application mismatch in the reviewed Board code.

The dispatch is at src/board.cpp:938, before both original material bounds at
:955 and :957. Castle handling remains first; initial kings are excluded from
the new branch. Target rank selects the only pawn color that can promote there,
independently of which exchange side moves first. Reverse pawn attacks identify
potential origins, and initial moving/captured origins are excluded. A pinned
potential pawn still activates the guard so a later exchange can release it.

Every ordinary source16 swap-loop statement and threshold remains unchanged.
The helper uses public const Board getters inside the existing anonymous
namespace, with no new class definition, shared scratch state, or header/ODR
dependency.

## Material, gain stack, legality, and shortcut bypass

Board's SeeValue at src/board.cpp:17 matches search's SeePieceValue in
include/forge/eval.hpp:29 exactly:

    Pawn100, Knight300, Bishop300, Rook500, Queen900, King0

The queen-promotion increment is 800. Initial promotions use the caller's
selected resulting type. Recapture promotions add the increment to that
capture and carry Queen900 as the next victim value. Both operations are
necessary: a promoted queen taken on the next ply cancels the added material
appropriately.

The phase-dependent evaluation values are intentionally different
(middle-game Pawn82/Knight337/Bishop365/Rook477/Queen1025, and separate endgame
values). The new helper does not mix those tables with SEE. Search capture
ordering/futility capture_value uses SeePieceValue and the same initial
promotion increment. Existing margins remain heuristics expressed in search
score units; this patch changes no evaluator, network, scale, or margin.

The helper's full gain recurrence and backward minimum fold are consistent
with optional stopping. The 64-entry array is explicitly bounded; every accepted
recapture consumes a distinct origin and a king terminates the exchange.
Even a conservative 63-capture accumulation of 1700-point terms fits int.

The source16 pin mask, live-origin/target-ghost masking, LVA piece order,
least-square tie choice, occupancy deletion, and x-ray updates are retained.
The target stays occupied. The terminal king test retains geometric enemy
defenders, including pinned pieces; a defended king capture is not appended.

Both legacy shortcut classes are bypassed on the rare path. This is required,
not incidental:

- An enemy promotion can lose more material than the initial attacker's value,
  invalidating the old initial lower bound.
- A later friendly promotion can rescue an exchange, invalidating an earlier
  inner threshold cutoff before that promotion is reached.

The helper has no threshold parameter or inner threshold pruning. Its completed
score is compared once with the caller's threshold. The original fast
threshold logic remains in place when the guard is false.

## Search callers and their practical effect

These call sites are unchanged in source17. Defaults below are tunable values
at the reviewed revision, not assumptions about every configured run.

| Caller | Threshold | Precondition and effect |
| --- | --- | --- |
| MovePicker good captures, search.cpp:353 | 0; move_score_threshold currently returns0 | Generated pseudo-legal captures are split into good/bad ordering stages. A failed SEE does not itself delete the capture from main search. |
| Qsearch, :814 | -QsSeeMargin, default -40 | After initial legality; outside check and mate-floor safeguards. A failed SEE skips the capture. Earlier stand-pat/futility decisions can prevent reaching this gate. |
| ProbCut, :985 | beta +180 -50*improving -static_eval | After legality; controls eligibility for the reduced verification search. |
| Quiet main-search pruning, :1048 | -24*lmr_depth squared | After legality and the caller's earlier pruning checks. The rare guard can cover quiet last-rank moves too. |
| Noisy main-search pruning, :1058 | -150*depth | After legality and earlier checks. At default positive depths, the reproduced -100 false negative is not removed by this particular margin. |
| Check extension, :1085 | 0 | After legality; also requires a checking nonroot move and default depth at least2. |

The important distinction is ordering versus pruning. The known +500/original
-100 case is wrongly relegated at MovePicker's zero threshold, and can be
removed at qsearch's -40 threshold. Its zero-threshold failure alone does not
prove main noisy pruning removed it. The +200/oracle -600 case can pass margins
that the corrected result rejects. Neither observation proves a changed
whole-search result without an actual caller-level witness.

Initial legality remains the caller's responsibility. MovePicker invokes SEE
before the main legality filter, so valid-field pseudo-legal inputs must remain
tolerated. The two frozen illegal-initial controls remain excluded from oracle
claims and included in ordinary-path parity. The helper is not an initial-move
legality validator.

## Finite bug-fix scope and existing evidence

The frozen prototype checked 326 rows: 324 legal oracle cases and two
initial-illegal controls. All 6,480 legal fixed-grid answers and thirty adjacent
answers pass. All 314 non-guard complete rows are byte-identical to source16.
Twelve guard rows include eight corrected reference mismatch rows; both
mirrored threshold-zero false negatives and false positives are corrected.
The applied Board hash matches that exact tested implementation.

This supports the specific promotion-material and premature-cutoff repair.
It does not make SEE universal chess minimax. LVA/lsb choice remains rather
than branching across all attackers, stopping is optional even where actual
check obligations could require a move, and only captures on one target are
modeled. Queen promotion is sufficient for the material cancellation/retention
model; off-target underpromotion tactics are outside it. Full-search signatures
may intentionally change. The rare full-stack work and dispatch cost remain
unmeasured.

## One optional targeted full-search evidence check

One finite source16-versus17 branch trace is materially useful to connect the
API repair to a real qsearch pruning decision. Use the existing UCI lifecycle
harness, one cold search per build, Threads1, OwnBook=false, cleared TT/history,
the same network/options, default tuning, and:

    position fen 1br3k1/2P5/2K5/8/8/8/8/1Q6 b - - 0 1
    go depth 1 searchmoves g8h8

Pure python-chess validation confirms the parent is valid, g8h8 is legal and
nonchecking, and the resulting White position is not in check. Its only legal
noisy move is b1b8. The c7 pawn cannot capture/promote initially because Rc8
pins it to Kc6. After Qxb8, the target recapture c8b8 releases the pawn's four
promotion captures. The target-only oracle is +300; source16 arithmetic is
-100 and the new gain-stack arithmetic is +300.

The forced first quiet move takes the depth-one root to wide-window qsearch.
Root extensions/LMR do not interfere. Qsearch's MovePicker has no earlier SEE
prefilter. With this sole legal noisy move, default QsFutilityMargin160 plus
captured Bishop300 gives stand-pat+460 above alpha, so capture futility does not
hide the intended SEE gate.

Capture an outside-production diagnostic trace of the actual qsearch
see_ge(b1b8,-40) decision and whether that move is made, alongside the finite
search output. Source-level expectations are reject in16 and accept in17.
Do not assert a score/PV difference before observing it; the forced root best
move is identical by construction. This check has not been run in this review
and would demonstrate caller behavior, not Elo or general playing strength.
