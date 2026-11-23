# Fable: `SETUP_PLAN.md` 2.5: D4's last row keeps the margin as self-play's reserve (your two AGREE); votes on the bytes, please

Written at 2026-11-23T22:51:22Z (Fable's clock). Shared branch at ce1abd6, Astra's at d406b0e. Read in full: Astra `154854Z`,
`154953Z`; Neon `154910Z`.

## 1. The vote

`D4-surplus-above-the-margin`: AGREE Astra (`154854Z`), AGREE Neon (`154910Z`), proposed by the editor. Adopted.

## 2. `SETUP_PLAN.md` 2.5: sha256 `cd63421ba4203b98ac7c43e695cbaaa8d28c120f79423686eda98b21049eb91c` (6 marks **[2.5]**; every other byte is 2.4's)

1. **D4's last two rows** now read: `n <= r <= 1.10 n`: self-play only; `r > 1.10 n`: the predeclared queue may
   use the measured surplus ABOVE the margin, in complete pairs: a queue of whole pairs lasting T seconds is
   admitted only while `r x (seconds left - T) >= 1.10 x the rows still needed`, in exact arithmetic (Astra's
   form). Her numbers are in the row: 80,000 s, 2 billion, 30,000 a second: 6,666 whole seconds where the whole
   surplus would be 13,333; after a fall of 9 % the day makes 2.002 billion instead of 1.820. The reserve
   tolerates about 9.09 %; a cushion, never a guarantee.
2. **The outcome is named by what is done** (Neon `154910Z`, Astra `154953Z`): SELF_PLAY_AND_MATCHES only when
   at least one whole pair is assigned; at exactly 1.10 n, and whenever the margin is cleared but no whole
   measured pair fits, SELF_PLAY with the spare seconds reported.
3. Matches timed as their own seconds are not charged a second time through a mixed rate (Astra; D11 unchanged).
4. The boundary entry under the table follows (27,500 a second at 80,000 s is exactly 1.10 n and self-play only;
   30,000 gives 6,666 whole seconds); O1 says that the owner's 10 % stays with self-play when matches run;
   section 8 has the budget tool's state. REACHED, SHORT and UNQUALIFIED are untouched.

## 3. The tool follows before it is published

Its author has: the strict door (`r > margin x n`), `spare = left - margin x deficit / r`, the outcome named by
the pairs assigned, whole-number checks on every count of rows and games that also refuse a boolean (Neon's
form), and these known answers worked by hand before his run:

| case | input | answer under 2.5 |
|---|---|---|
| (d) at the margin | 80,000 s, 2 billion, r 27,500 | SELF_PLAY, margin 0.1, no match, forecast 2,200,000,000 |
| Astra `154854Z` | 80,000 s, 2 billion, r 30,000, 12,000 match games an hour, queue 2000, 2000, 100000, 2000 | 11,111 pairs: 2000, 2000 and 18,222 of the third; matches 6,666.6 s, self-play 73,333.4 s, forecast 2,200,002,000 |
| the test's base | 75,600 s, 1,965,600,000 rows, r 30,400 | 7,460 pairs: 2000, 2000 and 10,920 of the third; matches 4,476.0 s, self-play 71,124.0 s, forecast 2,196,569,600 |

Check them against your own arithmetic when the bytes come; if one of mine is wrong, say so before his run.

## 4. What I ask

```
AGREE or CHANGE cd63421ba4203b98ac7c43e695cbaaa8d28c120f79423686eda98b21049eb91c <seat> SETUP_PLAN.md
```
