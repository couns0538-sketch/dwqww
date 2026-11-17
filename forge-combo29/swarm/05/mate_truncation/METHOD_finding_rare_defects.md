# METHOD NOTE: to find a defect like the mate-PV truncation, follow a known violation — do not sample

Seat 05, area 5. This is the most transferable thing I learned tonight, and it applies to any rare defect in any seat's
area. It is written plainly because it cost me two wrong findings before I understood it.

## Say it plainly

**Every real instance of the mate-PV truncation I found came from taking a position that already violated the rule and
varying ONE thing. None came from sampling positions at random.**

The five instances, and how each was found:

| instance | how it was found |
|---|---|
| G/192 (`8/8/1p6/8/p3p3/8/2Kpk3/8 w`) | scanning a fixed 353-position G set at depth 12 — the one violation in 553 positions |
| R/120 | the same scan on a fresh 200-position random set — 1 in 200 |
| G/59 at softnodes 2000 | re-searching a position that already carried a mate score, at the self-play budget |
| the S-F58 board (`r2r4/pB2kpp1/…`) | screening 400 positions *for long mates only*, then varying the budget |
| seat 15's 15-F9 | given to me as a position that violates, then varying build and settings |

Not one of them came from "run 500 positions and count violations". The counting version is what produced my two
sampling errors (S-F57's false zero, S-W8's inconclusive rate).

## The sampling numbers, beside it

Why counting does not work — measured on PC r15 + PC20, Threads 1, Hash 16, OwnBook false:

| what was sampled | size | positions that could even show the defect |
|---|---|---|
| random-play positions at depth 12, looking for \|N\| ≥ 6 | 600 | **6** (and all 6 were consistent) |
| random-play positions at depth 14, looking for \|N\| ≥ 8 | 400 | **2** |
| G-set positions at depths 12 / 14 / 16 | 60 each | **1 / 1 / 2** mate scores |

The defect needs a position that (a) carries a mate score at the depth searched and (b) has a *long* mate, so that 2N−1
exceeds what that depth can carry. Both conditions are rare, and the numbers say how rare:

- **a mate score at all:** 1–2 of 60 G positions at depths 12/14/16, i.e. roughly **1 in 30 to 1 in 60**;
- **a long mate (|N| ≥ 8)**: **2 of 400** random-play positions at depth 14, i.e. about **1 in 200**.

So a sample of a few hundred gives a handful of mate scores and almost no long ones. A "0 violations" from such a sample
is a statement about the sample, not about the engine — which is exactly how S-F57's false zero and S-W8's inconclusive
rate arose.

## What to do instead

1. **Find one violation.** Scan a fixed set once (that is how G/192 surfaced), or take one from another seat.
2. **Vary one variable at a time** and watch whether the violation persists:
   - depth (this produced S-F27: only long mates, |N| ≥ 10)
   - the budget type (this produced S-F62: `go nodes 50000` truncates where `go movetime 50` at the *same depth* does not)
   - the settings (this produced S-F29 and S-C21: PC20 shrinks the window and closes 15-F9 entirely)
   - the build (S-F17: the truncation appears on base and PC builds alike under S14)
3. **Re-check the same position at a bigger budget** to see whether the score was merely unstable (S-F28: G/192's `mate
   −12` becomes `−4` by depth 24).
4. **Only then** say something about rates — and say what the sample could and could not contain.

## The general form

This is not specific to mates. Any defect that needs a *rare precondition* (a long mate, a specific FEN shape, a
particular option combination, a terminal root) is found by constructing the precondition first and varying one thing
after. Sampling tests the prevalence of the precondition, not the behaviour behind it — and a zero from a sample that
never met the precondition is the vacuity trap wearing different clothes: it is a verdict about an empty set.

Seat 16's `CHECKER_RULE.md`-adjacent lesson is the same one: a zero counts only when the harness could have produced a
non-zero. Here the equivalent is **a rate counts only when the sample contained the precondition.**
