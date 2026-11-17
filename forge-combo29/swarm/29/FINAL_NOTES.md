# NOTES FOR THE FINAL BLOCK (seat 29, area 9 SPEED)
Draft material for the required `## <time> FINAL` STATUS.md block at the end of the 12-hour window
(2026-11-17T10:18Z). Kept separate so the FINAL block itself can be written quickly and completely.

## CORRECTION APPLIED TO THIS NOTE (29-F39 / 29-N20)
An earlier draft of these notes put "11.1 %" forward as *the* PC figure. **That was wrong to present as a single
number.** A 2x2 sweep on the same instrumented build shows the replacement-scan age/depth rate depends on DEPTH and
HASH together:

| Hash | depth | probes | scans entered | found empty | age/depth rate |
|---|---|---|---|---|---|
| 16 | 10 | 1,372,713 | 888,124 | 831,845 | **6.3 %** |
| 16 | 12 | 4,087,859 | 2,633,613 | 1,453,333 | **44.8 %** |
| 64 | 10 | 1,372,713 | 888,124 | 887,481 | **0.1 %** |
| 64 | 12 | 4,087,859 | 2,633,611 | 2,570,388 | **2.4 %** |

Probe counts are identical across Hash sizes at a given depth, so table size does not change the search at all — it
only changes how often a scan finds an EMPTY slot, i.e. whether the table is saturated.

## The two robust statements the FINAL should carry instead
1. **bench 13 reaches the age/depth replacement comparison 50 times in 861,904 probes (0.006 %)** — reproduced to the
   digit on my own counters, matching seat 19's 19-F18 bench figure.
2. **In real play at a saturated table it is reached far more often, and the exact share must be quoted with its
   depth and hash** (0.1 % to 44.8 % across the four cells above). Seat 19's 19-F18 54.7 % sits within that range:
   it is a different position set and a different saturation, NOT an error — their bench figure matches mine exactly.

## NAMED RULE FOR THE FINAL, to carry forward (29-N23)
**Sweep the second variable before any number reaches a summary.** Twice in one hour a single-cell percentage of mine
was wrong for the same reason, **four times in one hour**:
- replacement-scan rate: 11.1 % was one cell of a 0.1-44.8 % range across depth x hash (29-F38 -> F39);
- PC20 tree size: -19.5 % at depth 12, but **+2.3 % MORE at depth 10** (29-F40 -> F41);
- and that flip is itself **position-set-specific**: on the G set PC20 saves 15.9 % at the same depth 10 (29-F41 -> F42);
- move quality: "4 of 6 favouring PC20" became a **7-7-3 dead heat** at 100 positions (29-F43 -> F44).
Every one was caught by varying one more axis before believing the first measurement. Before a figure goes
into a finding, a rule or a summary: measure it at another value of whatever it most plausibly depends on, and if the
answer moves, report the TABLE rather than the number. A single figure may stand only when the sweep shows it is
flat — and then the flatness is the finding. The depth-10 comparison is the sharpest example: at n=30 it read
+2.3 % and looked like a cost, at n=100 it reads +0.3 % and is neutral — so the sweep found the axis, and the sample
size then fixed the magnitude.

## MUST APPEAR IN THE FINAL BLOCK: the open work and its recipe (29-N29)
The PC20 move-quality findings (29-F42, 29-F44, 29-F45) stay **OPEN — no second seat has checked them.** That label
is deliberate even though they are my strongest work. If no seat picks them up before the window closes, the FINAL
block must say so in these terms, so the next swarm can close them rather than rediscovering them:

> 29-F42 and 29-F44 (PC20 tree size, move quality) are **open and unconfirmed by any second seat.** **29-F45 is no
> longer in this group:** seat 07 (07-C56) CONFIRMED it on my own position set **to the digit** (87.5 / 87.5 / 85.0 /
> 92.5 %) and at the same time bounded it — their G set shows a **+15-point upward trend**, so the flatness is
> set-dependent, not an engine property (29-F48 / 29-N31). State it as "confirmed on its set, set-dependent". A self-contained reproduction recipe with a falsification condition per claim is committed at
> `forge-combo29/swarm/29/REPRODUCE_pc20_quality.md` (it still covers all three claims; F45's is now answered).
> The recipe lowers the cost of checking, not the uncertainty:
> treat these as unverified until a seat with its own harness and binary confirms or refutes them.

Also record the state summary from 29-N28: confirmed by another seat — 29-F3 (seats 19 and 27, independent methods,
one of them on the PC build under PC20) and 29-F9 (seat 19). Withdrawn or refuted by me — 29-C2 and the ordering half
of 29-F7, 29-F40's and 29-F41's generalisations, 29-F43's "4 of 6", and the mechanism inside my own named rule
(29-F31/N17).

**The arc worth telling about 29-C6**, in the words the coordinator endorsed: *two anecdotal boards, honestly scoped
down when a wider set failed to show it, then restored on a set built for the purpose — and the middle step is what
makes the last one trustworthy.* If only one sentence about method survives from this seat, keep that one.

## THE FRAME FOR EVERY SET-DEPENDENCE IN THIS REPORT (from seat 07's 07-C56, preserved in their words)
*"A number can be right on its own sample and wrong as a generalisation, and those are different faults needing
different reports."* Seat 07 found my 29-F45 30 points away on the last 40 of G, ran my ORIGINAL R_2911 sample
anyway, reproduced my four figures to the digit, and filed **"confirmed on its set, rate is set-dependent"** rather
than a bare REFUTES — noting that a bare REFUTES would have been procedurally correct and wrong.

Why it belongs in the FINAL: every set-dependence in this seat's hour is the same shape — 29-F38/39 (scan rate),
29-F40/41 (tree size vs depth), 29-F41/42 (the flip is set-specific), 29-F43/44 (move quality sample size), and now
29-F45/48 (agreement flatness vs distribution). In each case the measurement was right on its own sample and the
GENERALISATION was the fault. Report the table and the scope, not just the number.


### The error class to name in the FINAL (29-N33)
**Writing the caveat and then contradicting it in the same row.** A row saying "2-2-1 over five disagreements" and
"dead heat on both sets" in one sentence has already disarmed itself: the caveat is there, so it reads as careful,
while the claim stays the strong one. Three instances tonight, each caught only by re-reading for the WORD rather
than the number — 29-F31 (the refuted inlining mechanism), 29-F44 ("4 of 6" read as PC20 choosing better moves), and
29-F49 ("dead heat" on a five-sample). Underlying cause: a MEASUREMENT and a GENERALISATION welded into one sentence.
The mechanical fix, worth carrying forward: **let the weak sample keep the weaker word** ("no sign of X", never "X"),
and put any generalisation in its own sentence that names its scope.

### The sample-size rule and its worked example (29-F51 / 29-N35)
**Any tally under about twenty outcomes is a hint at most.** Four samples of the same measurement gave four directions:
17 outcomes -> 7-7-3 (dead heat); 5 -> 2-2-1 (dead heat); **3 -> 0-3 against PC20 (published as 29-F50, withdrawn
twenty minutes later)**; 13 -> 8-4 mildly pro-PC20. The three-outcome sample produced a confident-looking 3-0 the wrong
way and the 13-outcome sample of the same configuration reversed it.

### STATED AS A FINDING, not an anecdote (29-N36): direction with confidence, magnitude only with its n
Five separate measurements this hour produced the same pattern — the DIRECTION was always stable and every NUMBER
moved toward a smaller effect as the sample grew:

| finding | first measured | after widening | positions (then -> now) |
|---|---|---|---|
| scan rate (29-F38 -> F39) | 11.1 % at depth 12, Hash 16 | 0.1-44.8 % across depth x hash | 20 -> 200 (and 60 in the 2x2 sweep) |
| tree size vs depth (29-F40 -> F41) | -19.5 % at depth 12 | +2.3 % at depth 10 (same 30 positions) | 30 -> 30 (axis, not n) |
| the flip is set-specific (F41 -> F42) | +2.3 % on R_2911 d10 | -15.9 % on G, same depth | 30 -> 25 |
| move quality (29-F43 -> F44) | "4 of 6 for PC20" | 7-7-3 dead heat | 40 -> 100 |
| tree size magnitudes (29-F52) | -19.5 % / -12.7 % / +2.3 % | -11.9 % / -10.7 % / +0.3 % | 30/25 -> 100 |

**So: quote the direction with confidence, and quote a magnitude only with the n it came from.** The old numbers are
kept in FINDINGS beside the new ones rather than deleted, so the shrinkage is visible rather than tidied away.

## Headline results to list
- FIRST RULE (29-N19): a zero must always be a measurement, never a default; NOT FOUND + INCONCLUSIVE, never 0.
- 29-F42/29-F52 (tree size, RE-VERIFIED at n=100): **PC20 searches a smaller tree at match depths on both sets —
  -11.9 % on R_2911 and -10.7 % on G at depth 12 — and depth 10 is approximately NEUTRAL (+0.3 %), not a clear
  cost.** Use these magnitudes, not the n=25-30 ones (which read -19.5 % and +2.3 %): the direction was always stable,
  the magnitudes were inflated by small samples.
- 29-F35 rule: bench is not a representative workload for any slot-sensitive or TT-cost optimisation
  (96.0 % slot-0 hits vs 26/25/25/24 %; 0 vs 16,811 generation writes; 50 of 861,904 vs a high real-play rate).
- 29-F36 recommendation: picker scoring 2.91 % vs selection 0.77 % → reduce history reads per move, not the sort.
- 29-F16: PC r15 patch reproduces exactly; all eight known numbers match in all three regimes.
- 29-F19/F28/N16: my own TT patch REVERSES on the PC build (+0.320 %) and is non-additive (−0.872 % interaction);
  it is code cleanliness, not a speed win. Bench also flatters it ~3.7x (29-N18).
- 29-F42/F44/F45 — what the PC20 switches actually do, in one sentence: **they reach a different move of
  comparable value on about one position in eight, at every depth.** Backed by: smaller tree at match depths on both
  position sets (F42); a 7-7-3 dead heat on quality under a neutral judge (F44); and agreement flat across depth,
  85-92.5 % (F45). **Caveat to keep with it: "the flatness is the claim, not the individual percentages"** — 40
  positions per depth is about ±5 points, and that sentence is what stops the numbers being over-read.
- 29-F22/F23/F24/F29/F30: `go softnodes` and `go nodes` contracts, determinism, overshoot.
- 29-F32: 6s+0.06 clock on the PC build — median 203 ms of a 6000 ms clock, 0 of 60 past soft or hard.
- 29-C6 (with 29-F46) — the S-F23 mate-PV truncation finding, now on a purposeful denominator: seat 05's two
  boards reproduce exactly, AND on a purpose-built set of **40 mate-reporting positions** S14 truncates **2 of 40**
  while PC20 truncates **0 of 40**. Both runs reconcile rather than compete: random games show no truncation because
  they are not mate-heavy; the mate-heavy set shows the effect. **Keep the interval with it — 2 of 40 spans roughly
  1.5–12 %, so the DIRECTION is what is established, not the rate.**
- 29-C7/C8: confirmations of 19-F19 (bench 96 % slot-0 vs real games flat) and of 19-F18 (bench half to the digit).
