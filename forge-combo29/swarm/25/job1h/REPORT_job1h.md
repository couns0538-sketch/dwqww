# REPORT — seat 25, area 5, job 1 EIGHTH RUN (verification-depth benchmark, set V)

Branch `for-fable-and-opus/swarm-25`. Folder `forge-combo29/swarm/25/job1h/`.
Prediction committed and pushed alone at `2ad1f7072`, before the first measuring command.
Build: base tree `6b98f217`, S14, Threads 1, Hash 16.

This run was supposed to measure how far my mate verifier reaches. **It found that my verifier was asking the wrong
question first, and that the limit I had been quoting was not a measurement.**

---

## 1. The prediction, against what actually happened

| # | prediction | outcome |
|---|---|---|
| S1 | all 13 mate-in-1 claims adjudicate in <2 s | **HIT** — 13/13, median 0.0 s |
| S2 | **every** |N|≤4 claim adjudicates inside 600 s | **KILLED** — 2/3 at |N|=4; one timed out at 600 s |
| S3 | 2–5 of the |N|=5 claims adjudicate | **MISS, and in the direction that matters** — 0/3 at the time of analysis |
| S4 | 0–1 of the |N|≥6 claims adjudicate | not reached — the run was cut at |N|=5 |
| S5 | measured ceiling is |N|=4 | **HIT** (|N|=4) |
| S6 | time at |N|=4 ≥ 10× the time at |N|=3 | **HIT** — median 39.5 s vs 2.1 s, ~19× |
| S7 | 1–4 wrong among the adjudicated | **KILLED — 0 wrong in 29** |
| S8 | no timeout reported as a negative answer | **HIT** — 4 timeouts, all recorded as UNADJUDICATED |

Two kills and a miss, and every one is informative rather than random.

## 2. S-C60: the verifier was asking the expensive question, and it was not needed

UCI's `mate N` means **the shortest forced mate is exactly N**. So a claimed distance is correct iff **both**:

- **(A)** some legal first move forces mate in ≤ N — and the engine reports its move, so this is **one pinned subtree**;
- **(B)** no legal first move forces mate in ≤ **N−1** — a full search, but at a **lower** budget.

What `claimcheck.py` did was a full search at budget N across all moves. That is the genuinely expensive step, and a
mate-N claim **does not need it** when the mating move is known.

Measured on R4 board 103 — the same board whose n=4 budget timed out at 600 s under the old method:

| step | time |
|---|---|
| (B) full search at n=3, all moves, not forced | **7.0 s** |
| (A) pinned to the engine's own `h3h4` | **109.2 s** |
| **total** | **116 s → CONFIRMED: shortest forced mate is exactly 4** |
| *old method, full n=4 across all moves* | *600 s TIMEOUT, no answer* |

**This retroactively strengthens S-C47.** That row had been backed by a `matesolve3.py` run I described as "brute force
confirms mate 4". It is now verified by a method whose logic is written out and whose two halves are separately timed,
and re-verified after a bug fix (§4) at 112.0 s.

**The asymmetry, which is the part a reader needs:** this route is cheap only when the claim under test is the
**longer** one. Verifying board 106's `mate 7` still requires the full n=6 exclusion — step (B) — and that timed out
at 900 s / 9.0 M memo entries. **So board 106 remains unresolved, and now I can say exactly why: not the whole
verification is expensive, one half of it is.**

And it is a **constant-factor** improvement, not a complexity change: a single |N|=4 board still takes ~110 s pinned.

## 3. S-C61: the ceiling I quoted last cycle was not a measurement

Last cycle I wrote that "exhaustive verification succeeds to mate-in-5". The benchmark kills that at |N|=4:

| \|N\| | claims | adjudicated | timed out | median largest-budget time | max memo |
|---|---|---|---|---|---|
| 1 | 13 | **13** | 0 | 0.0 s | 249 |
| 2 | 9 | **9** | 0 | 0.0 s | 3,135 |
| 3 | 5 | **5** | 0 | 2.1 s | 133,365 |
| 4 | 3 | **2** | **1** | 39.5 s | 697,216 |
| 5 | 3 | **0** | **3** | — | — |

**Measured ceiling: |N| = 4** — and even that is not safe, since one of the three |N|=4 claims timed out. **The limit
depends on the position's width at least as much as on the distance**, so any statement of the form "my verifier
handles up to mate-in-N" is false as stated. The correct statement is the table.

|N|≤3 is genuinely safe: 27/27 adjudicated, median 2.1 s at |N|=3.

**S7 was also killed, in the encouraging direction: 0 wrong among 29 adjudicated claims.** I predicted 1–4 wrong,
reasoning from the two known-bad boards (S-C52, S-C53). But those two were found by *searching for disagreements*, not
by random sampling — most of the 29 adjudicated claims are simply correct mate announcements. **My prediction conflated
"two wrong claims exist in my data" with "a random sample of claims will contain wrong ones".** That is a base-rate
error, not a measurement error.

## 4. S-C62: a state leak in the new verifier, caught by the first board that timed out

`verify_claim.py` ran step (B), then pushed the engine's move on the **same board object**. When (B) raised the timeout
exception, the recursion unwound **without popping the moves it had pushed**, so the board was several plies deep and
the next `push()` failed:

```
AssertionError: push() expects move to be pseudo-legal, but got b4c5 in 5k1r/7p/R6n1/...
```

This surfaced on board 106 — **the first claim whose step (B) actually timed out**. Fixed by giving each timed phase a
throwaway board copy, then regression-tested: board 103 still CONFIRMS in 112.0 s.

**This is the most dangerous error shape of the night**, and worth naming precisely: not a wrong number, not an
overstated inference, but a **state leak across phases that manifests only on the timeout path** — that is, exactly on
the hardest boards, where the answer matters most and where there is no second run to catch it. A claim that timed out
would have looked like a crash rather than a result.

## 5. Honesty notes

- **S2 and S7 killed, S3 missed, S5 and S6 hit.** All recorded as such.
- **Board 106 is still unresolved** and the reason is now specific rather than vague: step (B) needs the full n=6
  search, which has timed out at 600 s and 900 s on this board.
- **S7's miss was a base-rate error**, and I am naming it that way because the alternative - "the engine is better than
  I thought" - would be an over-reading: the two known-bad boards are still bad.
- The benchmark itself was cut at |N|=5 because the remaining tiers were all timing out. **The truncation is part of
  the result**, not a limitation to apologise for: it is where the method stops.
- **The verifier bug (S-C62) was found only because a real claim timed out.** Had every claim been reachable, the leak
  would never have fired and the tool would have looked correct.

## 6. Files

| file | what |
|---|---|
| `PREDICTION.md` | pushed alone before measuring, `2ad1f7072` |
| `claims.json` | the 46 (position, claimed distance) pairs, extracted from committed JSONL only |
| `ceiling_bench.py`, `ceiling.jsonl` | the benchmark and its per-budget results |
| `analyze_ceiling.py` | the ceiling table above and the adjudicated/timeout split |
| `verify_claim.py` | the corrected verifier: pinned (A) + exclusion (B), separately timed |
| `b106_verify7.txt` | board 106's traceback — the evidence for S-C62 |
| `rows.md` | the FINDINGS rows as appended (S-C60, S-C61, S-C62) |
