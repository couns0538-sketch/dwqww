# RETRACTIONS.md — every claim of mine that I withdrew, and what withdrew it

Seat 27, area 7. Branch `for-fable-and-opus/swarm-27`.

`FINDINGS.md` carries the corrections inline, which is right for a reader following the work but useless to
anyone asking the simpler question: **which of this seat's claims are not true?** This file is that list. It
is ordered by severity of consequence, not by date, because the claims that mattered are the ones that could
have changed a decision.

Rule for this file: an entry is only here if I withdrew a claim I had actually published. A claim that was
merely never confirmed does not appear. Each entry names the evidence that killed it.

---

## 1. Claims that would have changed a decision — all withdrawn

### S-C18, S-C18a, S-C18b — a node ladder labelled "PC20" that never had PC20 applied
**Claimed:** deep-search node counts on the PC build under PC20, including a "cross-machine reproduction to
the node" with seat 11.
**Why it fell:** the harnesses built a 22-option list but applied only Hash/Threads/OwnBook. With PC20
actually sent, d14 is **23,174,968** (matching seat 10 to the digit); my published figure was
**599,407,784**.
**Withdrawn:** the ladder, and S-C18a's counter inference.
**Lesson:** a settings name in a finding is not evidence the settings were sent. Two seats agreeing on the
same misconfiguration is not independent evidence.

### S-C11, S-C11a, S-C11c, S-C11d, S-C11e — all clock-drain and forfeit figures
**Claimed:** 78.6/81.7 ms drain against seat 15's 105 ms; a 32.9 % overspend; forfeits at ply 78 and ply 106.
**Why it fell:** my harness's wall time carried ~1300 ms of *my own* per-move overhead, so the figures
described the apparatus. Separately, "overspend" was compared against the increment instead of the soft/hard
plan.
**Withdrawn:** every drain figure, the overspend percentages, and both forfeits.
**Note:** S-W4's own *diagnosis* was then corrected by S-W5 — see entry 3.

### S-F12 — "the engine swaps white and black clocks"
**Claimed:** a decisive clock-swap defect.
**Why it fell:** the opening book was left ON (`OwnBook` defaults true), so a 2-move position was answered
instantly from book and paired clock rows looked inverted. Each side is timed by its own clock.
**Withdrawn entirely.**

### S-W1 — a `mate -25` score on a KRvK board
**Claimed:** an impossible mate score.
**Why it fell:** KRvK has a maximum DTM of 16 moves = 31 plies; `mate -25` is 49 plies. The score cannot
exist. Settled on the material bound, independently of any harness question.
**Withdrawn.**

### S-C37 — "the z = 3.18 is a depth-stratum artefact"
**Claimed:** PC20's win share reverses by the depth S14 reached (100 % at depth 6, 6 % at depth 8), so
seat 19's lower figure was a harder position slice.
**Why it fell:** the stratification was on **S14's realized depth**, an *outcome of the comparison itself*.
The tell is one number — in the depth-8 stratum PC20 spends 2,938 nodes where S14 spends 3,677 **on the same
position**, so the "reversal" restates "PC20 lost". A pre-treatment test (S14 depth at `softnodes 20000`,
measured without reference to the contested budget) shows **no reversal anywhere**: PC20 positive in every
stratum, pooled 0.800, p = 0.0041.
**Withdrawn within the hour**, before the seat whose objection prompted it saw it.

### S-C43's "CIs do not overlap" — a Wilson interval computed from the wrong count
**Claimed:** my same-move interval `[0.586, 0.767]` and seat 19's `[0.278, 0.566]` do not overlap, so a real
disagreement existed.
**Why it fell:** `[0.586, 0.767]` is the correct Wilson interval for **67/98**, not for the 67/109 I paired it
with. Correct intervals are 67/109 → `[0.521, 0.701]` and 67/98 → `[0.586, 0.767]`. Seat 19's 12/29 interval
is `[0.2551, 0.5926]` — **not** the `[0.278, 0.566]` I had used for it, which is 17/41's. With the correct
numbers my interval and theirs **overlap by 0.007**.
**Withdrawn:** the non-overlap claim, and with it the argument that a genuine disagreement had been
demonstrated. The two runs simply could not separate the hypotheses at these sample sizes.
**Note:** seat 19's own phrasing of this correction ("the midpoint 0.676 is what 67/99 gives") was also
wrong; the interval is 67/98's, midpoint 0.684. I corrected the number as well as the pairing.

### S-W7's framing and S-C38's "before/after" — a filter reported as one change when it was two
**Claimed:** "excluding mate cells moves the aggregate from −11 to +38".
**Why it fell:** −11 is the **same-move 406** sum and +38 is the **clean same-move 387** sum — a filter *and*
a subset switch, described as one change. The all-600 sum is **also** +38 by coincidence, which is what made
the false before/after reading look confirmed.
**Withdrawn:** the framing. **The mate-cell finding itself stands** and is entry 6 below.
**Correct statement:** the 20 mate cells contribute −49 plies of summed difference, all 20 favouring S14,
dragging the all-600 sum from +87 down to +38.

---

## 2. Claims refuted by my own control suite, caught before publication

### S-C49 — a DTM solver whose tables were empty and whose controls all passed
**Claimed (briefly, and never pushed):** DRAW for both of seat 23's boards.
**Why it fell:** the retrograde tables came back **empty**; control 1 (checkmate reads as 0) and control 5
(`max()` within the material bound) both pass vacuously on an empty table, and the lookup fell through to its
DRAW default. Both boards are winning mates — one is mate in 6.
**Caught by:** asking why a K+Q v K board with an obvious mate returned DRAW. **Not** caught by any
assertion.
**Fix:** a non-vacuity control — at least one probe must return a finite DTM.
**Never published as a result.** Recorded because the near-miss is the instructive part.

### S-W5 — my own diagnosis of S-W4 was wrong
**Claimed:** S-W4 blamed ~1300 ms of harness overhead for the clock figures.
**Why it fell:** my in-process timer is accurate (agrees with the engine's own `time` field within 1 ms). The
overhead was in an *outer shell loop*, not the timer.
**Withdrawn:** the diagnosis. The underlying withdrawal of the clock figures (entry 1) still stands.

---

## 3. Claims narrowed rather than withdrawn

### S-F6 — duplicate of seat 01's S-F5/S-F8
Withdrawn as *new*; my run adds only independent confirmation on the release build plus a patch. The finding
is seat 01's.

### S-V1 — verdict change on the fifty-move "score band"
Under `FABLE_TO_swarm_6` rule 1, the band is **not** a defect on either board I tested. Verdict changed, not
the measurements.

### S-C13 — refuted the *premise*, not a claim of mine
"Base reports centipawns where PC reports mate" is false on verified lone-king mate boards. Recorded so the
premise is not reused.

### S-C14 / S-N2 / S-C26 — other seats' findings that did not reproduce
Their claims, my non-reproduction. Listed here so a reader does not mistake my re-run for endorsement:
24-F3's 348 s warm stall and 23-F68's partial-clock hang both failed to reproduce; the mechanisms I found in
their place (warm repeats get *faster*; an absent `btime` gives NO clock rather than a hang) are in
`FINDINGS.md`.

---

## 4. Method failures behind the withdrawals

Seven of the substantive retractions above cluster into two causes, and both are now guarded:

| cause | retractions | guard |
|---|---|---|
| a settings label that was not the settings sent | S-C18 group, S-C11 group, S-F12 | `pc/check_settings.py` (count = 22, all advertised) and `pc/check_settings_values.py` (values vs the canonical list; proven to catch a digit transposition) |
| a number computed in prose, not regenerated from the data file | S-C43 CI, S-C38 framing, and a material counter that valued N and B at zero | every interval/share/sum printed by a script that reads the JSON; `pc/strata_19c46.py` is the first converted file |

The overlap is not accidental: **a value without its provenance is not evidence**, whether the missing
provenance is *which settings produced it* or *which cell set produced it*.

---

## 5. What this file does not contain

- Claims I never published (there are several abandoned probes; they are not retractions).
- Findings confirmed and still standing — those are in `FINDINGS.md`, marked with the seat that confirmed
  them.
- Open questions. S-F8 (`searchmoves` changes the score) and S-F2 (`go nodes` below one iteration answers
  silently) remain **open**, not withdrawn.
