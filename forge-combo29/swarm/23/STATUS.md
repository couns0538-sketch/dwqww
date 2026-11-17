# SEAT 23 — STATUS

**Block: cold read of the FINAL's first page, then the fix, then the record. `date -u` at time of writing: 2026-11-17T03:41:47Z.**
Window closes `2026-11-17T10:18:41Z`; **6h37m remaining**. Area 3, move generation vs python-chess. Seed 2301.
Tip: `for-fable-and-opus/swarm-23`.

## This block

The coordinator set the rotation: read cold, fix, then record what was read. I did that on the FINAL's first page.

**One real defect, and it is in the prose the checks cannot reach.** Section 1 and section 3 both said the bail's move
"hangs a piece" and F61 called -805 "roughly a minor piece". The board says otherwise on both counts: the piece is the
**QUEEN on b6**, and **the queen was already en prise before Black moved** — White's knight on a4 attacks b6 at the root.
The repaired build's `b6b4` walks the queen away; the bail's `e6e5` does not. So the defect is a **failure to answer an
existing threat**, not a newly created hang.

**Why no check caught it, and why that is the point:** -805 reproduces to the digit at depths 8/12/16/20
(`-751/-832/-805/-853`). Every number was right. The error is a relation between a number and a verb, which is not
equality and so was outside the mechanised class — until this block extended it (below).

**The shape does not generalise uniformly — measured on all five F72 fixtures, not assumed.** After the bail's move, the
opponent's depth-16 PV: **g1 captures the queen and g2 captures a bishop into `mate 5` — in both the piece was already
attacked at the root (failures-to-answer); g6's `b3b7` captures a pawn that was NOT attacked, so that one DOES create a
new threat; g3 and g5 capture nothing.** "Hangs a piece" is right about at most one of five.

**A bug of mine, caught by my own correction.** My first swing measurement reported +8 against the report's +6, and I
briefly thought the FINAL carried another error. My script had maximised WHITE's advantage and labelled it BLACK's best
move — Black's worst. Ordered correctly, Black's recaptures give +6/+6/+8, so **the report's +6 is correct and my
contradiction was the bug** (23-F220). The tell was in my own output: a "knight recapture" that took a pawn.

## The class, extended

The coordinator's rule: a claim relating two texts is mechanisable when the relation is equality, but what actually holds
is "does this number agree with that measurement". Acting on the generalisation found a **third member** the rule did not
name: **a prose verb can also be a decidable predicate over a fixture.** `is_attacked_by(WHITE, B6)` is True at the
root — no engine needed. `job70/verb_check.py` now asserts it: **13 assertions, 8 on the fixture and 5 on two
known-answer controls that must come out the opposite way, all agreeing, exit 0, and verified able to fail (a planted
"queen is a knight" gives FAIL, exit 1).**

The boundary in three parts, each with a different answer, now stated in the FINAL §5:

1. **Within a sentence** — meaning is not mechanisable by pattern.
2. **Between this report and an independent source** — mechanisable when the claim reduces to a predicate: byte
   equality, number equality, or a board query; and the check must be shown able to fail.
3. **Between this report and itself — nothing is mechanisable.** The defect is whichever two of its own sentences
   disagree, and there is no third thing to hold them against. This is measured: six defects in six blocks that every
   check passed, each internally consistent, visible only to a reader who did not yet believe the document.

## Numbers

**247 distinct rows at 2026-11-17T03:41:47Z — 219 F (this seat's findings) and 28 C (confirmations of other seats').**

Stated as the count script printed it, not carried in my head. `sync_counts.py` rewrites the FINAL from `FINDINGS.md`.

## Checks, all three, this block

- `audit_findings.py` → 0
- `doc_check.py` → 0 (counts agree 219/28/247; GUI table and rules verbatim; VERDICT: PASS)
- `rule_check.py` → 0
- `job70/verb_check.py` → 0 (new; 13/13; planted fault → 1)
- `job69/frontpage_check.py` → PASS, `job68/final_recheck.py` → 11/11

## Next

Continue cold-reading the FINAL's first page against the board, one claim per pass; each pass ends with the fix and the
row that records what was read.
