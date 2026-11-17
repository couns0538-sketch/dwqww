# swarm-73 — STATUS

**Seat:** report assembly for the owner. Synthesising; not measuring.
**Branch:** `for-fable-and-opus/swarm-73` — `forge-combo29/swarm/73/`
**Window:** opened 03:48Z, audit closes 2026-11-17T10:20Z.
**`git fetch` time for all counts below:** **04:07Z.**

## State: DONE — summary current as of the last fetch

`OWNER_SUMMARY.md` written and revised through five rounds of coordinator corrections.

## Numbers the coordinator asked for

> **Unsourced figures: 5.**
> **Findings synthesised: 2,309** (2,293 table rows + 9 prose findings in `swarm-75` + 7 in `swarm-64`; 2,314 rows
> total, 21 re-runs recorded under an existing id).
> **Branches read: 28.**

**The five, split by cause:**

1. **Three book-latency percentiles** — `0.024`, `0.44`, `442`. `swarm-65` ships `scripts/q2b_latency.py`, which
   would produce exactly these, **and commits no latency output file.** Committed evidence gives single-shot times of
   0.1–0.4 ms (book) vs 91–346 ms (off-book), which supports the same conclusion without the percentiles.
2. **Two book-soundness figures** — `929` has **no committed occurrence**; `42` is **contradicted** (`noise_floor.txt`
   gives **max |delta| 66 cp**). Both flatter the finding; in the `42` case the honest number *strengthens* it.

**My instrument can see only the first three.** `929` and `42` are bare integers outside its four token patterns, so
it reported no opinion and its silence read as a pass. **The other two came from cold-reading the new book section
against `swarm-65`'s evidence files.** Reported as 5 with the split, not 3 with a clean sheet.

## The four I reported last round were all sourced — my error, recorded

`52,472`, `199,619`, `4/48`, `14/13` are all in `swarm-64` at `5e8a8fa99`, the tip its seat reported. I audited
between that seat's message and its push. **The method limit, now rule 41's companion: a provenance check against the
remote cannot see a branch that has not landed.** The two misses: `14/13` is written as prose in `FINDINGS.md:66` and
my query searched the slash form; `52,472`/`199,619` needed a `.txt` corpus.

## Deliverable

`forge-combo29/swarm/73/OWNER_SUMMARY.md` — 1,373 lines:
1. **What to change** — 20 recommendations with verdicts (22 markers over 20 items: **14 ship, 3 do-not-ship,
   5 needs-more-evidence**).
2. **What is broken** — 9 items, plus 5 named withdrawals.
3. **What is not established.**
4. **The measurement rules** — **41 rules**, including the new rule 41 on provenance false matches.
5. **Unsourced** — 5 figures, two causes, with the count history.
6. **Sourced but mis-paired** — 3 sourcing defects (2 fixed upstream) + 2 book contradictions (§6.5).
7. **What the book gets right** — soundness, each row citing its evidence file.
8. **How this was assembled.**

## Corrections applied (five rounds)

1. Illegal-FEN diagnostic always emitted → **refined again: emitted EXACTLY ONCE; scan both streams, assert one.**
2. "No duplicate signature" is 2 of 5 → 40 % / 60 %.
3. `softnodes` floor **plus** the 60-position scope run. Uses the seat's own sentence verbatim.
4. **MultiPV/Hash, corrected twice.** Final: MultiPV 1 at any Hash; else **48 MB at 2 lines, 24 MB at 3–6**. Now
   expressed as the **invariant** ("never more permissive than the fitted one") because a count is a snapshot a
   re-fit invalidates.
5. Two fallbacks → **"the last valid board"**, which in a fresh session is startpos.
6. Opening book: own-clock gate, pre-empts draw adjudication, fullmove-derived `Book Depth`.
7. v3 pair-count patch at needs-more-evidence (g++ vs clang+znver5+PGO).
8. Evaluation defects: KNN-vs-K reaches search; bare-minor inversion does not.

## Constraints honoured

- No engine run, no script executed, no re-measurement.
- No other seat's branch modified. `swarm-27` S-C88 deferred to its owner at the coordinator's direction.

## Open items

1. **`929` and `42`** — the report should be corrected in place; I have flagged both and carried neither as fact
   (§6.5). `42` in particular is a contradicted figure sitting in the report.
2. **`swarm-27` S-C88** still asserts the withdrawn absolute; deferred to its owner.
3. **Three latency percentiles** need the `q2b_latency.py` output committed, or the report should quote the
   single-shot times I use instead.
4. Counts here are snapshots at the 04:07Z fetch — re-derive, do not edit.
