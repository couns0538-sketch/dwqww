# 19-C64 — the material-key cache is ~0.7 % faster, not 1.5-3.5 %. My prediction failed; 19-F9's null was right.

## Result
CTRL (unpatched `6b98f217`) vs PF (+ `job2/optimize_material_key.patch.txt`), **both passing all four honesty pins
with IDENTICAL node counts** — so this is a pure per-node-cost comparison, same control structure as 19-C58.
Real positions, fixed `go nodes 50000`, ABBA, n = 130 pairs:

| quantity | value |
|---|---|
| pooled per-node ratio | **0.9934 → 0.66 % faster** |
| geometric mean | 0.9916 → 0.84 % faster |
| **bootstrap 95 % CI** | **[0.9845, 1.0023] — INCLUDES 1.0** |
| median | 1.000 |
| node ratio achieved | 1.00000 (budget held) |

### The two sign-shares I first reported were from DIFFERENT SAMPLES and are not comparable
I originally wrote "sign-share 27.7 % at 50k and 52.5 % at 500k" as if they were the same measurement. **They were
not: 36/130 at 50k, but 21/40 at 500k.** The comparison was invalid, and the apparent disagreement was my error.

**Re-measured on the SAME 130 positions at BOTH budgets (19-C65), decomposing wins / exact ties / losses:**

| budget | median search | PF faster | **exact tie** | PF slower | strict share (wins/all) | **wins/decided** | geometric ratio |
|---|---|---|---|---|---|---|---|
| `nodes 50000` | 19 ms | 30 | **84 (64.6 %)** | 16 | 23.1 % | **65.2 %** | 0.9931 |
| `nodes 500000` | 218 ms | 71 | **9 (6.9 %)** | 50 | 54.6 % | **58.7 %** | 0.9977 |

**So it is a DEFINITION effect, not a budget effect — exactly as the coordinator hypothesised.** At 50k the median
search is **19 ms**, which the engine reports at **1 ms resolution**, so **two thirds of pairs are ties** and any
"strict" win count is measuring the timer's granularity, not the cache. At 500k (218 ms) ties fall to 6.9 %.

**Once ties are excluded the two budgets agree: 65.2 % vs 58.7 %, both "a weak lean toward faster" — and neither is
a coin flip, but neither is a large effect either.** The honest single figure is
**wins/decided ≈ 60 %, at `go nodes 500000` where ties are 6.9 %.**

## Both my predictions failed
1. I predicted **1.5–3.5 % faster**; measured **0.66–0.84 %**. Off by a factor of 3-4.
2. I predicted a **high sign-share (≥ 80 %)** because removing redundant arithmetic should be uniform. **Measured
   wins/decided 65.2 % at 50k and 58.7 % at 500k — a weak lean, far from 80 %.** **My kill condition
   ("if the share is near 50 %, 19-F6 is wrong") is therefore only partly triggered:** the share is not 80 %, but
   it is also not a coin flip. **The decisive evidence against 2.71 % is the pooled magnitude (0.66 %, CI including
   1.0), not the share** — and the share is what I first mis-reported by comparing two different samples.

## What this means for 19-F6
**19-F6 said the material key is 2.71 % of total self time on `bench 13`.** On real positions the whole patch buys
**0.7 %, with a CI that includes zero and a sign-share near a coin flip.** So **19-F6's 2.71 % is a bench-specific
cost share** — the same lesson as 19-C55/C58, now applied to a *profile share* rather than to a speed or node
figure. **A self-time percentage is not a transferable cost unless someone removes the code and measures.**

**Note this is a third distinct failure mode for bench:**
| bench measure | transfers to real positions? |
|---|---|
| per-node cost (19-C35) | **no** — 6× optimistic |
| aggregate node sign (19-C55) | **no** — sign flips across benches |
| **profile self-time share (19-F6 → 19-C64)** | **no** — 2.71 % of bench is 0.7 % of real |

## So 19-F9 stands, and now for a better reason
**19-F9 said "not measurably faster: ratio 1.0059, CI [0.9680, 1.0454]" on bench 13, n=10.** I criticised that as
an underpowered null. **The null was right and its CI was wide enough after all** — the true effect (~0.7 %) sits
inside [0.9680, 1.0454], and my n=130 real-position run with a tighter CI still cannot exclude 1.0.
**An underpowered null that happens to be correct is still correct.** I was right that it could not *detect* 2.71 %;
I was wrong that there was 2.71 % to detect.

## For the owner
**Do not ship the material-key cache as a speed optimisation.** It is correct (4,736 positions, 0 mismatches) and
costs nothing, so it is harmless — but it buys **under 1 %**, and the 2.71 % figure that motivated it came from a
bench profile that does not represent real search.
