# PREDICTION — deepseek6, long 5c (kimi5's LmrFine, its job 11 patch)

Written before the first measuring command of long 5c. Never edited after this commit.

Patch: `forge-combo29/tests_kimi5_job11/LmrFine.patch.txt`, copied verbatim here.
Clean copy: `/agent/repos/p13` at 6b98f2170a3210e71beed04bbd2553972c253ed7.
Build `/agent/repos/work/build-l5c/forge`, sha256 `04bcba3ddcc97501bdd524a686f785041f7b8ec22dd131be319f69bcabb05720`,
Release g++ 13.3.0, 0 errors, 0 warnings.

## The nine new options, read off the binary's `uci` output

| option | type | default | min | max |
|---|---|---|---|---|
| `LmrFine` | spin | **0** | 0 | 1 |
| `LmrFineHistory` | spin | **0** | 0 | 1 |
| `LmrRoundF` | spin | **512** | 0 | 1023 |
| `LmrTtPvF` | spin | **1024** | 0 | 4096 |
| `LmrNotImprovingF` | spin | **1024** | 0 | 4096 |
| `LmrCutNodeF` | spin | **2048** | 0 | 4096 |
| `LmrTtCaptureF` | spin | **1024** | 0 | 4096 |
| `LmrGiveCheckF` | spin | **1024** | 0 | 4096 |
| `LmrInCheckF` | spin | **1024** | 0 | 4096 |
| `LmrCutoffAddF` | spin | **1024** | 0 | 4096 |

(That is ten rows because `LmrFineHistory` is easy to miss; the patch declares **ten** new options, not nine.
I say so here so the count is right from the start, and the report will use ten.)

## What the patch does (read from the code it inserts)

`LmrFine == 0` (the default) takes the ORIGINAL integer block verbatim — the patch keeps it in an `if` branch
line for line. `LmrFine == 1` takes a fixed-point variant: the integer reduction is multiplied by 1024 and each
of the eight bonuses/penalties becomes a tunable in 1/1024ths, with `LmrFineHistory` selecting a finer history
term. So the eight `*F` options are **only read when `LmrFine == 1`**, and `LmrFineHistory` only when
`LmrFine == 1` too.

## Identity at the defaults

| comparison | predicted | killed by |
|---|---|---|
| O under S14 vs long 1 | **200 of 200 equal** (sum 9,500,069) | any row differs |
| G under S14 vs long 1 | **353 of 353 equal** (sum 18,466,239) | any row differs |
| O no options vs long 1 | **200 of 200 equal** (sum 12,573,318) | any row differs |

Honesty at the defaults already run: all four met (`honesty_*.txt`).

## The second identity — and the one I most expect to FAIL

`LmrFine=1` with every `*F` at its default should reproduce the same arithmetic as the integer path:
`LmrTtPvF=1024` is 1.0, `LmrCutNodeF=2048` is 2.0, `LmrCutoffAddF=1024` is 1.0, and the history term
`clamp(history/divisor,-2,2)` times 1024 equals `clamp(history*1024/divisor, -2048, 2048)` rounded down. So the
patch's design intent is that `LmrFine=1` at the defaults is ALSO the identity.

**I predict `LmrFine=1` alone is 200 of 200 equal on O — and I expect to be wrong about at least one row**,
because the fixed-point form rounds where the integer form clamps, and `LmrRoundF=512` adds a half-unit before
shifting. A single row differing would be the precise place where the two forms disagree, which is a result
worth having. The killed-by condition for "the two forms agree exactly" is any differing row; the killed-by
condition for "the rounding really does differ somewhere" is 200 of 200 equal.

## Wiring, in the order the code allows it

The eight `*F` options cannot be wired unless `LmrFine=1`, so I test:

| check | predicted | killed by |
|---|---|---|
| `LmrFine=1` (all F at default), O/S14 | as above | as above |
| `LmrFine=1;LmrCutNodeF=0` | differs from the `LmrFine=1` run | identical (option not wired) |
| `LmrFine=1;LmrTtPvF=0` | differs | identical |
| `LmrFine=1;LmrCutoffAddF=0` | differs | identical |
| `LmrFine=1;LmrFineHistory=1` | differs from `LmrFine=1` alone | identical |
| `LmrRoundF=0` with `LmrFine=1` | differs when rounding matters, identical if it never does | — (either is a result; I will report which) |
| **`LmrCutNodeF=0` with `LmrFine=0`** | **identical to the default** — the F options are unread when `LmrFine=0`, so this is a NEGATIVE control: if it differs, an F option reaches the integer path and that is a defect | any difference |

That last row is the control that distinguishes "wired" from "wired only inside the branch it belongs to", and I
expect it to be identical.

## Out-of-range stop checks

`LmrFine=2` (max 1) and `LmrRoundF=1024` (max 1023) must each stop the run with `invalid value`.
