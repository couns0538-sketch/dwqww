# SEAT 23 — STATUS

**Block: cold read of the FINAL's first page, then the fix, then the record. `date -u` at time of writing: 2026-11-17T03:41:47Z.**
Window closes `2026-11-17T10:18:41Z`; **6h37m remaining**. Area 3, move generation vs python-chess. Seed 2301.
Tip: `for-fable-and-opus/swarm-23`. **254 rows at 03:45:05Z.**

## This block

The coordinator set the rotation: read cold, fix, then record what was read. I did that on the FINAL's first page
and the sentence immediately following it.

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

**Two more from the same page, both fixed.** (1) "6 pawns of material" was wrong as a *label*: the static exchange is
**+6** (queen 9 less the knight recapture 3), and the sentence now says so and keeps it apart from the -805 search score,
since they are not two estimates of one number. (2) **"both moves allow the same +1" named no moves** — with F130's pair
(`c6c5`/`e4e8`) it is +1/+1, neutral, exactly as F130 says; with the PC move F60 records on the same board (`e4b1`) it is
+1/+0, so the repair is *better*. **The row was right and the sentence was unfalsifiable** — a predicate with a free
variable is not a predicate (23-F222). The FINAL now names the pair and gives both numbers.

**Then my own correction was itself wrong — the third version of the same sentence.** I had said the repair "walks the
queen away". It does not: after `b6b4` the queen is on b4, **still attacked by Qd2**, White takes it and Black recaptures
with the **bishop** — a queen *trade*, +0. After `e6e5` White takes with the **knight** and Black recaptures with a
**pawn** — +6. **So the cost is the recapture balance, not the queen's safety; the queen is capturable after both moves**,
which I reached for twice because a verb demands a causal story and both stories were plausible (23-F223).

**And the check I wrote for the verb would have blessed that wrong story**, because "attacked at the root" is satisfied
by both. The mechanism is a different predicate — what the recapture takes back — so `job70/mech_check.py` now asserts the
recapture balance directly, **10 assertions, exit 0, and verified by planting my own wrong story (it fails, exit 1)**
(23-F224). The general form, now in the FINAL: **a check written against the sentence you just corrected is satisfied by
the sentence you correct it to.**

**A bug of mine, caught by my own correction.** My first swing measurement reported +8 against the report's +6, and I
briefly thought the FINAL carried another error. My script had maximised WHITE's advantage and labelled it BLACK's best
move — Black's worst. Ordered correctly, Black's recaptures give +6/+6/+8, so **the report's +6 is correct and my
contradiction was the bug** (23-F220). The tell was in my own output: a "knight recapture" that took a pawn.

**Then the tooling audit, which found the largest defect of the block.** Acting on the coordinator's point that a
wrong-comparator error in a checker is worth finding, I asked the same question of every script: **can it report NO?**
Two of the scripts the FINAL tells a reader to run — `frontpage_check.py` and `final_recheck.py` — **printed `**FAIL**`
and exited 0**; `final_recheck`'s "11 of 11 agreeing" was a sentence in the report that no code produced (23-F226). Both
now fail correctly, verified by planting a fault.

Then, one level out: **five scripts had verdicts that depended on the directory you ran them from**, including all three
gate checkers, whose `HERE = os.getcwd()` reads like hygiene and is the bug. The hook `cd`s first so the gate was safe,
but a reader following §9's one-liners was not — and `doc_check.py` would have read the FINAL as an **empty string** and
compared nothing against nothing (23-F227/F228). **All nine cited scripts now anchor to `__file__`, and
`run_all_checks.sh` runs each twice, own-dir and from `/tmp`, failing if any verdict disagrees: 9 of 9 agree.**

The comparator's sibling: `job11/margins.py` credited a **tie** to one candidate, which the c-count would have read as
evidence. It never fired (17 rows, 0 ties) but was live; fixed to a three-way branch and tested against the old line
(23-F225).

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
3. **A claim must name every argument of its relation** — otherwise it cannot be checked even in principle (23-F222).
4. **Between this report and itself — nothing is mechanisable.** The defect is whichever two of its own sentences
   disagree, and there is no third thing to hold them against. This is measured: six defects in six blocks that every
   check passed, each internally consistent, visible only to a reader who did not yet believe the document.

## Numbers

**254 distinct rows at 2026-11-17T03:45:05Z — 226 F (this seat's findings) and 28 C (confirmations of other seats').**

Stated as the count script printed it, not carried in my head. `sync_counts.py` rewrites the FINAL from `FINDINGS.md`.

## Checks, all three, this block

- `audit_findings.py` → 0
- `doc_check.py` → 0 (counts agree 226/28/254; GUI table and rules verbatim; VERDICT: PASS)
- `rule_check.py` → 0
- `job70/verb_check.py` → 0 (13/13; planted fault → 1)
- `job70/mech_check.py` → 0 (new; 10/10; planted wrong mechanism → 1)
- `job70/sign_check.py` → 0 (sign convention verified on 3 constructed boards)
- `job11/tie_test.py` → 0 (new; tie branch tested from the real source; old line → exit 1)
- `run_all_checks.sh` → 0 (new; all 9 scripts agree from own-dir and /tmp)
- `job69/frontpage_check.py` → PASS, `job68/final_recheck.py` → 11/11

## Next

Continue cold-reading the FINAL's first page against the board, one claim per pass; each pass ends with the fix and the
row that records what was read.
