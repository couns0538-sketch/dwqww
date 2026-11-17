# swarm-73 — STATUS

**Seat:** report assembly for the owner. Synthesising; not measuring.
**Branch:** `for-fable-and-opus/swarm-73` — `forge-combo29/swarm/73/`
**Window:** opened 03:48Z, audit closes 2026-11-17T10:20Z.

## State: DONE

`OWNER_SUMMARY.md` written. Two commits: `STATUS.md`, then the summary.

## Deliverable

`forge-combo29/swarm/73/OWNER_SUMMARY.md` — 760 lines, in the required order:
1. **What to change** — 16 recommendations, each with the measurement that licenses it and a verdict:
   **11 ship, 3 do-not-ship, 3 needs-more-evidence** (17 verdict markers over 16 items, because §1.7 ships the
   throughput half and holds the answer half at needs-more-evidence).
2. **What is broken** — 8 items, plus 5 named withdrawals so no retracted claim is inherited as fact.
3. **What is not established** — open mechanisms, structurally untestable items, and scope limits.
4. **The measurement rules** — 37 rules in before / during / after phases.
5. **Unsourced in the consolidated report** — **0 figures**.
6. **Sourced but mis-paired** — 3 sourcing defects, 1 readability defect.
7. **How this was assembled** — counts as literals, provenance of the method.

## Numbers the coordinator asked for

> **Unsourced figures: 0.**
> **Findings synthesised: 2,283** (2,304 rows across 25 branches; 21 rows are re-runs recorded under an existing id).
> **Branches read: 25.**

## Method

- Read `docs/forge-findings.md` (1,429 lines) and `internal/swarm/tally.md` (637 lines) in full.
- Dumped all 25 branches' `FINDINGS.md`, then later **all** tracked `.md` under `forge-combo29/swarm/NN/` (8.4 MB),
  because several load-bearing figures live in `STATUS.md` / `HARNESS_TRAPS.md` rather than `FINDINGS.md`.
- Wrote a provenance audit (`/tmp/audit.py`, working copy only) that normalises commas, minus signs and whitespace,
  extracts every numeric token from the consolidated report, and checks it against the branch corpus. Result: 226
  distinct forms, **0 without a home**.
- Counted findings by table-row id, per branch, with a literal printed beside the total.

## Corrections received and applied

Three arrived mid-run. **All three were already in `docs/forge-findings.md`; none were in the branch record.**

1. Illegal-FEN diagnostic is **always emitted**; only its location moves. Encoded in §1.4. **The withdrawn absolute
   is still live in `swarm-27` S-C88 and in the tally's S-C87 bullet** — and **no branch row carries the
   four-combination result at all.** Flagged in §6.3.
2. "No duplicate signature" is **2 of 5**, not absolute. Encoded in §2.3 as 40 % caught / 60 % missed. **The tally's
   S-C87 bullet still says "no duplicate signature at all"** four lines below its own correction. Flagged in §6.3.
3. `softnodes`: floor at the depth-64 clamp, plus the 60-position scope run. Encoded in §1.15 **using the measuring
   seat's own sentence verbatim**, plus the settings for both halves.

## Discrepancies found during assembly

- **`0.07×` is not in the 80-cell sweep.** The sweep (`swarm-27` S-C96) spans `1.008×`–`3.503×` at budgets 500/2,000;
  `0.07` is `1,344 / 20,000` from the separate floor probe. A later branch row (S-C100) splices them, and the
  consolidated report inherits the splice. `1,344 / 2,000 = 0.672`, so the low bound cannot come from the sweep.
  **Resolved by using the seat's own wording, which says "across the populations measured"** — §6.1.
- **`3 of 5` counts the complement.** The tally's "3 of 5, NOT absolute" reads as a duplicate count but counts the
  *no-signature* rows; the table gives 2 duplicates. Not an error, but it inverted my own first pass — §6.2.

## Constraints honoured

- No engine run, no script executed, no re-measurement.
- No other seat's branch modified, even where the content is stale.

## Notes for the coordinator

- The three stale source statements (§6.3) are worth a decision: the withdrawn forms are what a reader of the branch
  history meets **first**, and the corrected form currently exists only in the consolidated report. If you want them
  fixed in place, that needs the owning seats or an explicit assignment — I left them alone per the no-cross-branch
  rule.
- `swarm-27` moved twice during this run (S-C99…S-C102 landed after my first fetch). Any later seat quoting softnodes
  should re-fetch before quoting.
