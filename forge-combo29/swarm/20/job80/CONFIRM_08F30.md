# seat 20 — job 80: seat 08's 08-F30 confirmed in direction — sparse endgames are the volatile-score class

Seat 08's 08-F30: on PC r15 + PC20, Threads 1, 6 s + 0.06, comparing the **clocked stop** to a **completed
`go depth D+4`**, the sparse class shows **mates appearing** where full-material middlegames do not — and it
explicitly refuses to quote a combined ratio because mapping mate to 30000 cp "gives a meaningless 106×".

## My reproduction — same shape, smaller sample
PC r15 sha256 `068f0927768d30be…`, **PC20 = S14 (17 opts) + 6 extras, `assert_regime` passed**, Threads 1,
`go wtime 6000 btime 6000 winc 60 binc 60` then `go depth <clocked depth + 4>`. Four boards per class from the G set
(sparse = material ≤ 14; full = material ≥ 24).

| class | depth reached | clocked score | completed d+4 | mate appeared? |
|---|---|---|---|---|
| **sparse** | 19 | **cp 4302** | **mate 9** | **YES** |
| sparse | 18 | cp −1915 | cp −2233 | – |
| sparse | 27 | cp −55 | cp −53 | – |
| sparse | 22 | cp 34 | cp 30 | – |
| full | 18 | cp −294 | cp −300 | – |
| full | 18 | cp −256 | cp −312 | – |
| full | 17 | cp 274 | cp 275 | – |
| full | 18 | cp 33 | cp 37 | – |

**Sparse: 1 of 4 boards had a mate appear. Full: 0 of 4.** And the movement magnitudes separate the classes sharply:

| class | \|movement\| from clocked to completed |
|---|---|
| **sparse** | 4302→mate (a categorical change), **318**, 2, 4 |
| **full** | **6, 56, 1, 4** |

So the full-material boards moved **1–56 cp** while one sparse board turned a +4302 cp evaluation into a **mate 9** —
a change of kind, not degree.

## What this confirms and what it does not
1. **CONFIRMED in direction:** the sparse class is where the clocked score is *volatile*, and specifically where a
   **mate can appear** that the shallow search had not found. Seat 08's mechanism (expensive iterations mean the clock
   buys a shallow depth exactly where depth matters most) is consistent with everything here.
2. **The refusal to over-quantify is right, and I will not improve on it.** I could report "1 of 4 vs 0 of 4", but with
   n=4 that is a count, not a rate — and converting the mate to centipawns to average it is exactly the mistake they
   declined to make. **Report events as counts**, as they say.
3. **NOT confirmed:** their specific `cp -4161 → mate -5` and `cp 627 → mate 12` pairs are on their boards, not mine;
   I reproduced the *phenomenon*, not their instances.

## Why it matters for the owner
His training data and his matches both see the clocked stop. If the sparse class is where the clocked evaluation is
categorically wrong (a mate missed, reported as a huge centipawn score), then **positions from that class carry noisier
labels** — a data-quality point, not a playing-strength one, and consistent with what seat 08 says about linking the
clock tail to the training-data concern.

## Limits
- 4 + 4 boards, one clock, one depth offset (+4), built-in net, Threads 1.
- "Sparse" = material ≤ 14 by my own threshold; seat 08 used its own class definitions.
