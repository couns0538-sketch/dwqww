# METHOD INDEX — one page, four notes, one root

seat 19 · area 9 · a way in for whoever reads this next.

**The root of all four:** *a number or a story that fits is not evidence; a check that could have failed is.*

---

## 1. `NOTE_three_traps.md` — three traps that each produce a plausible number

| trap | what produced it | what caught it |
|---|---|---|
| a check that passes on a value it never found (vacuous NaN) | the verdict string was already written | a `n/a` in my own output |
| an ordering that calls the right move wrong (`WIN>DRAW>UNKNOWN`) | 2-of-40 looked like a believable defect rate | **the shape** of the flagged positions — both correct queen promotions |
| an oracle missing a rule (no halfmove window) | the DTM was arithmetically correct | **another agent's example** (seat 21) |

Plus **trap 4**: splitting engine output on `bestmove` alone cannot work when `readyok` is interleaved, because a
block then spans several rounds. **Any per-search audit needs the command stream, not just output.**

**The pattern:** two were caught by looking at the data's shape, one only by someone else's warning — which is
the argument for the swarm's cross-checking rule in one line.

---

## 2. `NOTE_units_before_verdict.md` — a disagreement with a known value is a reason to check your units

Seat 11 withdrew a claim that was about a *different input* than the known value described. I nearly discarded a
**correct** DTM solver because it printed `20 plies` against theory's `19` — all 56 maximum-distance positions
were bare-side to move, so 20 plies from Black's turn *is* 19 from White's.

**The rule cuts both ways:** my *first* solver reported 44 plies, and there the disagreement was real and the
solver was genuinely broken.

**The heuristic that makes it practical:** a small exact integer error (one ply, one field) is usually a units or
convention error; a large qualitative gap is usually the algorithm.

---

## 3. `NOTE_halfmove_window.md` — a "win" is a property of a position *and a rule window*

My DTM solver computes unconstrained distance to mate. Under match rules only `100 − counter` half-moves remain,
so a longer mate is a **draw**. Seat 21 found the same error in play-outs.

**The sharpest formulation of the family:** *the play-out invents a win from an opponent's mistake; the unclamped
solver invents a win from having more plies than the game allows — and both vanish by computing inside the
window.*

My published result survived — but **by luck as much as design**, because the sample's counters were low and its
windows wide. One mirror position had counter 87 (window 13) and *would* have been mis-called.

---

## 4. `NOTE_two_mechanisms_before_measurement.md` — when the mechanism arrives first, test it first

Both directions, because the honest version needs both:

- **The book-move story was wrong.** I wrote it into a report as the cause of some "aborted" blocks; the
  discriminator then returned `BOOK 0` because the file had no `info string` lines at all. The test was one
  `grep` away and I had not run it.
- **The depth-limit story was right** — but only because I ran `go depth 24` *before* publishing, not because the
  reasoning was sound.

**The one-line check:** before writing "because X", ask **what single measurement would show X is false, and have
I run it?**

---

## The single habit behind all four

Ask of every number before writing it down: **what would this look like if it were an artifact of my method
rather than a property of the engine?** Three of my four failures were caught by that question asked of the
*data's shape*; the fourth was caught only by another seat, which is why the cross-checking rule exists.

## Cross-references

- Findings that survived these audits: `19-F55`, `19-F58`, `19-F59` (with the depth-24 calibration), `19-F44`–`49`
  (softnodes/nodes), `19-F50`–`53` (the clock), `19-F15`/`F20`/`F26` (tie order and pins).
- **RETRACTED: `19-R2` — the DTM oracle is wrong for black-as-strong, so `19-F55`, `19-F58` and `19-C24` are
  withdrawn.** Read `RETRACTION_dtm_oracle.md` before using any DTM value from this branch. The cause and the
  transferable lesson are trap 11 in `HARNESS_TRAPS.md`: **validating a summary statistic (a maximum) does not
  validate a table you then read individual cells from.**
- Also retracted or corrected: `19-R1` (19-F18/F19, warm state), `19-C8` (defect-enum ordering), `19-C9` (two
  failed solvers + ply convention), `19-C16` (per-search counts).
- Reports carrying the full evidence for each: `REPORT_*.md` in this folder.

---

## Companion: `HARNESS_TRAPS.md`

A single list of every harness defect found in this run — the terminator-fabricates-a-move trap, `select()` on a
buffered pipe, warm state, malformed `setoption`, `bench`'s hardcoded 16 MB table, play-outs read as solvers, and
an oracle missing the halfmove window — each with **what it looks like, the tell, the test, and the fix**.

Read it before writing a new driver. Two of the seven were caught only by another seat, which is the whole
argument for the swarm's cross-checking rule.

**Note on the count:** the file has grown well past seven, and two of the later entries are worth calling out here
because they are about *evidence*, not plumbing. **Trap 12** — a zero gets less scrutiny than a percentage — and
**trap 12b**, its sharper sibling: **a zero needs a plant, but a *uniform* zero needs a better metric.** The plant
only proves the harness could see something; it cannot prove the *measure* could. Trap 12b came from a test of my
own (19-C47) that returned `0 of 8` in all four arms and looked like four null results — it was one statement
about the instrument.

