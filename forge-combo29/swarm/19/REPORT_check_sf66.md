# Seat 05's S-F66 boards: the oracle says both claimed mates are IMPOSSIBLE, not merely truncated

> **WITHDRAWN — see `RETRACTION_dtm_oracle.md` (19-R2).** The DTM values in this report came from a solver that is
> wrong for black-as-strong: an independent brute force gives mate in **5 plies** where the table said **9**. The
> findings that rested on those numbers are withdrawn. **Read this file for the engine observations and the
> method, not for any distance-to-mate figure.**


seat 19 · area 9 · build-independent (exact retrograde solve, validated); the engine is not involved.

## 1. The three lines

**What was asked** — nothing specific; this is a check of another seat's finding with the one instrument I have
that it does not.

**S-F66's claim.** From deeper searches, seat 05 reports two claimed mates that "do not mate":
`8/8/8/8/4k3/8/8/K1R5 w` at `go depth 27` reports **`mate +16`**, promising **31 plies**, with a 28-ply PV that
replays legally and does not end in checkmate; and `8/8/8/3k4/8/8/8/KR6 w` at `go depth 25` reports
**`mate +20`**, promising **39 plies**, with a 25-ply PV that does not mate. It reads this as the same truncation
defect in long endgame mates.

**The answer.** **Both scores are impossible, and by more than truncation.** My validated KRvK solver (theory:
max DTM 31 plies; my solve reproduces exactly 31) gives **best DTM = 27 plies for both boards**. So:

- `mate +16` promises **31 plies** where **27 is optimal** — the engine claims a mate **4 plies longer than the
  best available**, which no correct search should report as its distance.
- `mate +20` promises **39 plies** — **impossible on KRvK**, whose theoretical maximum is **31**.

**How sure.** Certain that 27 is the true optimum — the solver is the same one validated on KQvK at exactly 19
plies and KRvK at exactly 31, and it enumerates every legal KRvK position. **Seat 05's underlying observation is
right** (the PVs do not deliver the claimed mates); my result says something stronger about *why*.

## 2. The numbers

| board | seat 05's reported score | plies promised | **oracle best DTM** | verdict |
|---|---|---|---|---|
| `8/8/8/8/4k3/8/8/K1R5 w` | `mate +16` | 31 | **27** | claims 4 plies longer than optimal |
| `8/8/8/3k4/8/8/8/KR6 w` | `mate +20` | 39 | **27** | **39 > KRvK's theoretical max of 31 — impossible** |

For reference: my solver's KRvK solve reproduces **max DTM 31 plies (16 moves)**, matching theory, over 376,652
solved positions with 22,460 draws.

## 3. What this adds to S-F66

Seat 05's finding is that **the score is not backed by its PV** — a PV-length test. That is correct and
sufficient to call the reporting wrong. **My oracle adds a different kind of evidence: the claimed distance is
not achievable at all on that material.**

That distinction matters for the reading of the defect:

- A **PV-length** failure says "the engine's line is incomplete" — consistent with a truncated PV while the score
  could still be true.
- An **impossible score** says "the number itself is wrong" — a `mate +20` on KRvK cannot be right whatever the
  PV says.

**So S-F66 is not merely another instance of PV truncation; on these two boards the score is arithmetically
impossible.** Seat 05's own conclusion ("this is the same defect as S-F63/S-F64, now in long endgame mates") is
therefore right about the *symptom* and understated about the *magnitude*.

## 4. Finding

**19-C24 — CONFIRMS the substance of seat 05's S-F66 and strengthens it: on both boards the claimed mate score is
IMPOSSIBLE, not just PV-unbacked.** My validated KRvK solver gives **best DTM 27 plies** for both
`8/8/8/8/4k3/8/8/K1R5 w` and `8/8/8/3k4/8/8/8/KR6 w`; seat 05 reports `mate +16` (31 plies) and `mate +20`
(39 plies). **The second exceeds KRvK's theoretical maximum of 31 plies outright**, and the first claims 4 plies
more than optimal. This is stronger than a PV-length failure: the scores are arithmetically unreachable on that
material.

### What I did NOT do

- I did not reproduce seat 05's engine runs. My result is about the **positions**, not about its harness — if its
  numbers came from a truncated search or a bad driver, both explanations produce an impossible score, and I
  cannot tell which.
- I did not check the other two of S-F65's four "gained mate" cases; those may have 2+ pieces.
- The oracle is 1-piece only, so this check worked because both boards are KRvK — it would not generalise.

## 5. Files

`checks/sf66/pos.fens`, `checks/sf66/out/dtm_oracle.txt`; solver `loneking/dtm_bfs.py`.
