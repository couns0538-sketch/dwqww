# swarm-73 — STATUS

**Seat:** report assembly for the owner. Synthesising; not measuring.
**Branch:** `for-fable-and-opus/swarm-73` — `forge-combo29/swarm/73/`
**Window:** opened 03:48Z, audit closes 2026-11-17T10:20Z.
**Provenance audited against the 34 branch tips listed in `OWNER_SUMMARY.md`'s header** (fetch 04:31Z).

## State: DONE — summary current as of the 04:31Z fetch

`OWNER_SUMMARY.md` — 2,137 lines, **56 rules**. Revised through thirteen rounds.

## Numbers the coordinator asked for

> **Unsourced figures: 9.**
> **Findings synthesised: 2,353** (2,332 table rows + 9 prose in `swarm-75`, 7 in `swarm-64`, 7 in `swarm-74`).
> **Branches read: 34.**

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
