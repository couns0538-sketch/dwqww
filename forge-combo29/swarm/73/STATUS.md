# swarm-73 — STATUS

**Seat:** report assembly for the owner. Synthesising; not measuring.
**Branch:** `for-fable-and-opus/swarm-73` — `forge-combo29/swarm/73/`
**Window:** opened 03:48Z, audit closes 2026-11-17T10:20Z.

## State: DONE — summary current as of the last fetch

`OWNER_SUMMARY.md` written and revised through four rounds of coordinator corrections.

## Numbers the coordinator asked for

> **Unsourced figures: 4.**
> **Findings synthesised: 2,302** (2,293 table rows + 9 prose findings in `swarm-75`; 2,314 rows total, 21 re-runs
> recorded under an existing id).
> **Branches read: 26.**

**The four unsourced figures are a publishing gap, not fabrications:** `52,472`, `199,619`, `4/48`, `14/13`. All four
belong to the MultiPV/Hash boundary work attributed to **`swarm-64`**, which **does not exist on the remote**. The
rest of the same paragraph's figures are sourced, so the block came from real measurement.

**Naive literal pass, published beside it: 38 of 252 tokens flagged — 34 formatting, 4 unsourced.** §5 carries the
per-token breakdown and the four-count history (226/52 → 228/34 → 231/32 → 252/38).

## Deliverable

`forge-combo29/swarm/73/OWNER_SUMMARY.md` — 1,207 lines, in the required order:
1. **What to change** — 20 recommendations, each with the measurement licensing it and a verdict. **22 verdict markers
   over 20 items** (two items, §1.7 and §1.17, split a ship verdict from a needs-more-evidence one):
   **14 ship, 3 do-not-ship, 5 needs-more-evidence.**
2. **What is broken** — 9 items, plus 5 named withdrawals so no retracted claim is inherited as fact.
3. **What is not established** — open mechanisms, structurally untestable items, scope limits.
4. **The measurement rules** — 40 rules in before / during / after phases.
5. **Unsourced in the consolidated report** — **4 figures**, with the four-count history.
6. **Sourced but mis-paired** — 3 sourcing defects (2 fixed upstream, 1 deferred), 1 readability hazard.
7. **What the book gets right** — the soundness result, placed last because it is a clean bill.
8. **How this was assembled** — counts as literals, provenance of the method.

## Corrections applied (four rounds, all from the coordinator)

1. Illegal-FEN diagnostic is **always emitted**; only its location moves. **Later refined: it is emitted EXACTLY
   ONCE — scan both streams, assert one occurrence.**
2. "No duplicate signature" is **2 of 5**, not absolute → 40 % caught / 60 % missed.
3. `softnodes`: floor at the depth-64 clamp **plus** the 60-position scope run that bounds it. Used the measuring
   seat's own sentence verbatim.
4. **MultiPV/Hash advice, twice corrected.** First the coarse "Hash 16 with multiple lines"; then the `Hmax` fitted
   form; finally the **conservative cap — 48 MB at 2 lines, 24 MB at 3–6 — which has zero false-safe cells of 48.**
   The 16 MB form was refuted by the very measurements that replaced it.
5. **Two fallbacks, not one** — the engine searches **the last valid board**, which in a fresh session is startpos.
6. Opening book: fires on the **side-to-move's own clock** or `movetime`; **pre-empts drawn-root detection**;
   **`Book Depth` derives from the FEN fullmove counter**.

## Discrepancies found during assembly

- **`0.07×` was not in the 80-cell sweep** — separate floor probe at a different budget. **FIXED upstream** in the
  report (three-population table) **and on the branch** (the seat now carries the arithmetic).
- **`3 of 5` counts the complement** — a readability hazard, not an error.
- **Book soundness (`2520/2520`, `2429/2429`, `0/135`) is in the tally but NOT in the consolidated report.** I added
  it as §7 and cite the tally. **The report omits a clean bill it should carry.**
- **A near-miss of my own, recorded because it is the same class:** I first wrote that the `11` in `14/13/11` was
  sourced. It is not — the whole triple is unsourced. A *different* sourced ladder (Hash-16 control `16/15/13/11`)
  contains a `13` and an `11`, which is exactly how a presence match imitates a provenance check.

## Constraints honoured

- No engine run, no script executed, no re-measurement.
- No other seat's branch modified. `swarm-27` S-C88 remains stale **by the coordinator's direction**, deferred to the
  owning seat.

## Open items for the coordinator

1. **`swarm-64` is unpushed** — four figures in the report are unverifiable until it lands, and §1.7's recommendation
   should be re-checked then. **This is the only item that affects a recommendation.**
2. **`swarm-27` S-C88** still asserts the withdrawn absolute; corrected in place by the owning seat.
3. **The report does not carry the book soundness result** (§7 here quotes the tally instead).
4. **Two counts in this file are snapshots** (252 tokens, 38 naive misses). If the report changes again they need
   re-deriving, not editing — the rule §4 carries.
