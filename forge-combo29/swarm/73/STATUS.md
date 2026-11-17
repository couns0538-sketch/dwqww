# swarm-73 — STATUS

**Seat:** report assembly for the owner. Synthesising; not measuring.
**Branch:** `for-fable-and-opus/swarm-73` — `forge-combo29/swarm/73/`
**Window:** opened 03:48Z, audit closes 2026-11-17T10:20Z.
**Provenance audited against the 31 branch tips listed in `OWNER_SUMMARY.md`'s header** (fetch 04:36Z).

## State: DONE — summary current as of the 04:36Z fetch

`OWNER_SUMMARY.md` — **2,357 lines, 61 rules, 22 recommendations** (14 ship / 5 do-not-ship / 4 needs-more-evidence — 23 markers over 22 items; §1.7 carries two). Sixteen rounds.

## Numbers the coordinator asked for

> **Unsourced figures: 9** (of 284 tokens).
> **Findings synthesised: 2,380** = 2,371 distinct table-row ids + 9 prose findings in `swarm-75`; 2,392 raw rows, 21 re-runs under an existing id.
> **Branches read: 31** carrying a `FINDINGS.md`, of 63 `swarm-NN` branches on the remote.

| cause | figures |
|---|---|
| no committed output (script ships, evidence does not) | `0.024`, `0.44`, `442` |
| no committed occurrence | `929` |
| **contradicted by evidence** | `42` (noise floor; evidence gives **66 cp**) |
| budget absent from the sweep | `40 of 40` at 2M |
| **THE SHIPPABILITY COUNT** | **`0 of 125`, `13 of 13`, `220-280 ns`, `13,707`** — the numbers licensing the headline SHIP |
| *(verified by arithmetic, excluded)* | `0.0712` |

**Two figures came OFF the list in later rounds:** `13.2 %` (now in `swarm-27` `S-C108`) and `54,379` (now in
`swarm-71`). **That is three timing artefacts in total**, which is why the header names commits.

**The shippability count is the serious one** and I have flagged it in §1.2's own text, not only in §5: the
adversarial-family and depth-contract results are sourced, but the claim "the scan fires on drawn roots only" is
report-only. Re-measuring it on the owner's build is the conversion check.

## Sixteenth round — the pointer check's FULL form, applied to my own document

**The coordinator's form is stronger than mine and it found three more defects immediately.** I had been checking that
pointers *resolve*; the form extracts each pointer, resolves it, and **prints what it now points at**. A renumber
leaves resolution true while breaking subject-match — exactly the trap-14→15 case the report now records.

**Found and fixed, all of the "resolves but names the wrong subject" class:**

| pointer | cited for | actually pointed at | correct target |
|---|---|---|---|
| §1.18 | "ships one and holds the other" | §1.18 holds **both** at needs-more-evidence | sentence rewritten |
| §4 rule 24 | "a control that fires on correct usage" | the median/geometric-mean rule | **rule did not exist** — written as rule 35 |
| §4 rule 30 | "a cap test without a rising series" | the p-value-recomputability rule | rule 36 |

**Two of the three were stale SUBJECTS from earlier renumbering**; the third cited a rule I had never written, which
is the more interesting failure — **a pointer to a plausible-sounding rule that no one had authored**, and the sentence
around it read fine because the rule *should* have existed.

**And five more pointers broke after this round's own renumber**, caught by re-running the form: rule numbers for the
estimator, identity-trap, decomposition, digit-match and derived-claim rules all shifted by up to +3. **All 20 rule
pointers and all 22 section pointers now machine-verified to name their intended subject**, printed with context.

**The lesson in the form is that "all references resolve" passes in BOTH the good and the broken case** — so the check
must print targets, not verdicts.

## Fifteenth round — totals re-derived from artefacts, and one false pointer found

**Acting on the closing seat's prediction, I stopped trusting carried figures and re-derived every total from the files.**
It found drift, which is the point.

| quantity | carried | re-derived | verdict |
|---|---|---|---|
| findings | 2,353 | **2,380** (2,371 distinct table-row ids + 9 prose in `swarm-75`) | **drifted** |
| branches read | 34 | **31** with a `FINDINGS.md`, of 63 `swarm-NN` | **wrong both ways** |
| rules | 58 | **58** | correct |
| recommendations | 21 | **22** | **drifted** |
| line count | 2,197 | **2,344** | **drifted** |

**And one false cross-reference — exactly the class the seat named.** A sentence said "the check is trivial and it is
the same one **§45** needs", pointing at the decomposition/label rule. §45 had become the "correction adds without
removing" rule after a renumber; the decomposition rule is §47. **A pointer is a claim and this one was false**, and
no content check compares a pointer against its target. Repaired, and all 31 section refs and 20 rule refs were then
machine-verified to resolve.

**The entry-count trap was live in my own document too.** `swarm-64/65/74` record findings as prose *sections*, and I
had earlier counted section headings as findings. They are not: those files carry context sections and summaries, so
an entry count overstates a fault count. Only the **9 explicitly-id'd** findings in `swarm-75` are counted; the other
three prose seats contribute **0** to the total by the definition now stated in the header.

**A second self-inflicted inconsistency, caught by the same pass:** two stale count paragraphs had accumulated in the
header from successive edits, so the document asserted 2,353 and 2,328 in different places. Removed.

## Fourteenth round — the mechanism reverses, and a resolution rule

**I had the mechanism backwards, and the correction makes it stronger.** I wrote that "only the per-node factor moves
with game phase", following thirds. **Six slices of 4,135 pairs separate what thirds could not: per-node spread
0.29 %, node 1.36 %, wall 4.76 %.** So **per-node cost is nearly a constant of the engine and the phase dependence
lives in the NODE ratio.**

**The corrected version is the better claim:** per-node is a property of the **code**, stable to 0.3 % in every phase;
the node ratio is the **search interacting with the position**. **That is why three samples across two builds agree at
1.0640 / 1.0693 / 1.0709** — it is the one term that does not depend on what you sampled. A mechanism that predicts its
own replication beats one that merely fits.

Added **rule 26** — a slice count is a **resolution**, and too few slices invert a conclusion. The thirds were a
reasonable partition that produced a confident, coherent, backwards mechanism; the factors differed ~4× and a 3-way
split could not resolve that. Added **rule 27** — a median of a product is not the product of medians; slice 2 gives
0.9618 × 1.0719 = 1.0310 against a wall median of 1.0476, a 1.6 % gap on data whose aggregate closes to 0.5 %. The
table now carries that caution so a reader multiplying slice medians does not conclude the identity fails.

**Security gate: nothing to remove.** I checked — I carry no line about that gate having resolved, so the recheck
seat's correction needs no action here.

## Thirteenth round — the wall-time headline flips sign

**This reverses a recommendation's primary line, and it is the largest single change since the summary was written.**

- **§1.11 rewritten from "net speed NOT ESTABLISHED" to "a small LOSS on the full population."** Population run over
  the game set: **node median 0.9618, wall median 1.0351 — about 3.5 % SLOWER.** The earlier 116-pair stride sample
  gave wall 0.9698 (~3 % faster), so **the sign flips.**
- **I verified the identity independently: 0.9618 × 1.0709 = 1.0300 against observed 1.0353** — a 0.5 % gap. So it is
  the two components composing as the decomposition predicts, not two estimates disagreeing.
- **Consistent with the n=464 arm's "not established"** rather than contradicting it: that interval included 1.0, and
  the population puts the point on the slower side.
- Carries the reason the sample misled (node median identical to four decimals across thirds; wall median drifts
  1.0215 / 1.0352 / 1.0441) and the mean rule (**median 0.9618 vs mean 1.0941; the mean's error was 4× the median's**).

**§6.7 added — the PC r15 columns have a provenance gap.** I verified myself that **`FORGE_FIX_ROOT_DRAWN` appears in
no `src/` or `include/` path on any of the 63 `swarm-NN` branches** — only in prose and check scripts. It is a gap, not
a doubt (the numbers are mutually consistent; `swarm/23` records the sha256 prefix), but **the repair cannot be rebuilt
from the record**, which is what the shipped patches close. Also recorded: **`-DFORGE_MATE_ALPHA_GUARD=1` is NOT the
repair** — it gates `MateAlphaGuard`, a pruning switch.

**Three corrections to things I was told, all applied:** the piped-harness fabrication is **not** detectable by its
move (**13 distinct fabricated moves, all 60 legal, 0 of 60 correct** — only a zero `info`-depth count finds it); the
per-node row **named its estimator** after a cold recheck found the pooled estimate sat **outside its own interval**;
and the two new control/parser rules (**a parameter that cannot bind cannot be tested**; **a parser fault is silent
unless the row count is asserted** — 1 and 8 rows instead of 180 and 464).

## New this round

- **§7d: v3 accumulator, 54,379 distinct positions, 0 mismatches**, with 5,012 king-key transitions and the union
  method note (nested fixtures, `47,418 ∪ 6,961`; the earlier `57,720` was a sum, not a union).
- **§2.9: neural-arch hang** — `NNUEArch` with no usable net prints an error then **exits status 2 without answering
  `isready` or sending `bestmove`**. Sourced from `swarm-71`'s STATUS with the exit status. My first search missed it
  because it lives in STATUS, not FINDINGS.
- **§4 rules 9b and 10: parser surfaces.** Unparseable `go` value → default silently (seven forms all land on depth 5,
  1,001 nodes, indistinguishable from `go depth 5`); surfaces are **not uniform — two of five refuse safely, three
  improvise silently**; a corrupted move list **splices** rather than truncates.
- **§6.6: the identity baseline is an acceptance gate this branch cannot meet.** `27,944,084` is unreachable here
  because four PC20 options are **absent from the source** (`CuckooRep`, `HistRework`, `TtPruneV2`, `CorrHistV2`),
  giving `29,791,805` — a 6.6 % gap. §1.10 carries the caveat with the number.
- **§7b promoted from four ways to five**, with the parser-uniformity point added.

## Cold read (04:16Z) — 5 arrangement defects, all fixed

Found by reading; invisible to the 271-token provenance pass. The `0000`/`mate 0` contradiction was in **three** of my
sections, and the coordinator found the same defect in the report's own table.

## Deliverable structure

1. What to change (20 recommendations, 22 verdict markers) · 2. What is broken (9, plus 5 withdrawals) ·
3. What is not established · 4. **49 measurement rules** · 5. Unsourced (8) · 6. Mis-paired (6) ·
7. Book soundness · 7b. Five ways of answering a question not asked · 7c. The reuse trap · 7d. Accumulator
correctness · 8. Method.

## Constraints honoured

- No engine run, no script executed, no re-measurement.
- No other seat's branch modified.

## Open items

1. **`42` is contradicted, not just unsourced**, and sits in the report's book-soundness block.
2. **`27,944,084` still reads as an unconditional gate** in the report's §5b — §6.6 documents why it cannot be met.
3. **Accumulator aggregates** (`54,379` / `47,418` / `6,961`) are report-only; `swarm-71` commits fixtures and
   commands but not the union arithmetic.
4. **Three latency percentiles** need `q2b_latency.py` output committed.
5. Counts are snapshots at the tips named in the header — re-derive, do not edit.
