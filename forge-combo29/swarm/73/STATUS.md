# swarm-73 — STATUS

**Seat:** report assembly for the owner. Synthesising; not measuring.
**Branch:** `for-fable-and-opus/swarm-73` — `forge-combo29/swarm/73/`
**Window:** opened 03:48Z, audit closes 2026-11-17T10:20Z.
**`git fetch` time for all counts below:** **04:07Z.**

## State: DONE — summary current as of the last fetch

`OWNER_SUMMARY.md` written and revised through seven rounds of coordinator corrections.

## Numbers the coordinator asked for

> **Unsourced figures: 7.**
> **Findings synthesised: 2,328** (2,312 table rows + 9 prose findings in `swarm-75` + 7 in `swarm-64`; 2,333 rows
> total, 21 re-runs under an existing id).
> **Branches read: 29.**

**The seven, by cause:**

| cause | figures |
|---|---|
| no committed output (script ships, evidence does not) | `0.024`, `0.44`, `442` — book latency percentiles |
| no committed occurrence | `929` (SEE false flags), `13.2%` (move-change stable-board rate) |
| **contradicted by evidence** | `42` (noise floor; `noise_floor.txt` gives **66 cp**) |
| budget not in the committed sweep | `40 of 40` at 2M nodes (`swarm-69` stops at 1M, where it is already 24/24) |

**`0.0712` is verified by arithmetic** (I recomputed Fisher from the counts: 0.071172) **and excluded from the count**,
because an independent recomputation is a stronger guarantee than a citation but not the one §5 measures.

## New this round (determinism seat, `swarm-69`)

- **Hash 16 vs 64 is a budget condition, not a Hash fact:** 0/24 at 50k, 2/24 at 200k, 17/24 at 500k, 24/24 at 1M.
  **Of 178 differing cells, 15 changed the best move** — I recomputed both totals from `job4/hash_sensitivity.json`
  and they match. The 2M row is the unsourced one.
- **`ucinewgame` 0 of 25 / `Clear Hash` 24 of 25**, with the source reasons, and **the drift reproducible on 3 of 3
  processes** — so a reused harness gets a stable-looking wrong number, not noise. Placed in §7c.
- **Piped harness measures nothing** (EOF aborts the search, fabricates `bestmove a2a3`, perfectly reproducible).
- **Fullmove-0 FEN is python-chess VALID and engine-REFUSED** — validation and acceptance are different gates.
- **Cross-build at population scale:** 0 of 200 and 0 of 341 non-lone-king positions differ in **both node counts and
  best moves**; lone-king control 12 of 12.
- **Nine machine-environment inputs change nothing** (0/40 at two budgets, both builds) — so the environment is not
  the problem, the TT state is.

## Corrections applied (seven rounds)

1. Illegal-FEN diagnostic always emitted → **emitted EXACTLY ONCE; scan both, assert one.**
2. "No duplicate signature" is 2 of 5 → 40 % / 60 %.
3. `softnodes` floor **plus** the 60-position scope run.
4. **MultiPV/Hash, corrected twice** → conservative cap, now stated as the **invariant**, not the count.
5. Two fallbacks → **"the last valid board."**
6. Opening book: own-clock gate, pre-empts draw adjudication, fullmove-derived `Book Depth`.
7. **Score-change criterion WITHDRAWN** (p = 0.0712, underpowered; replication p = 0.726 pointing the other way).
   Select on **move** change; score change is **unestablished in either direction**. I had been recommending it —
   that is corrected in §1.7 and rule 33.
8. **MultiPV residual: ratio not subtraction.** "1.72× predicted, 1.94× observed, ~0.22× is search" replaces
   "135.4 = 104.5 + 31". The subtraction came from two different samples and the per-position excess ranges
   135.0–195.6 ms.
9. **v3 loaded-net symmetry added:** 0 of 353 on the v3 path with a loaded net, beside 0 of 420 on the built-in.

## Deliverable

`OWNER_SUMMARY.md` — 1,588 lines, **47 measurement rules**, 20 recommendations:
1. What to change · 2. What is broken (9) · 3. What is not established · 4. **47 rules** ·
5. Unsourced (7) · 6. Mis-paired · 7. Book soundness · **7b. The four ways of answering a question not asked** ·
**7c. The reuse trap** · 8. Method.

## Constraints honoured

- No engine run, no script executed, no re-measurement.
- No other seat's branch modified. `swarm-27` S-C88 deferred to its owner.

## Open items

1. **`42` should be corrected in the report** — it is contradicted, not merely unsourced, and it sits in the book
   soundness block. `929` likewise has no committed occurrence.
2. **Three latency percentiles** need `q2b_latency.py` output committed, or the report should quote the single-shot
   times (0.1–0.4 ms vs 91–346 ms) that I use instead.
3. **The 2M Hash row** is unsourced; the 1M row already carries the recommendation.
4. Counts are snapshots at the 04:07Z fetch — re-derive, do not edit.
