# NOTES FOR THE FINAL BLOCK (seat 29, area 9 SPEED)
Draft material for the required `## <time> FINAL` STATUS.md block at the end of the 12-hour window
(2026-11-17T10:18Z). Kept separate so the FINAL block itself can be written quickly and completely.

## The one number the owner most needs
Replacement-scan age/depth rate on the PC's real configuration — **PC r15 build, PC20, Threads 1, Hash 16,
depth 12, 200 real-game positions: 11.1 %.** Set-size scoping: 13.6 % at 20 positions, settling by ~40 positions;
under DEFAULT options the same set gives 19.5 % (26.5 % at 20 positions). Seat 19's 19-F18 reports 54.7 % on their
R_1911 set: that is a DIFFERENT POSITION DISTRIBUTION, not an error on their part — their bench figure of 50
reproduces to the digit on my counters, so their instrumentation is sound and the two sets simply differ.
Bench 13 reference: 861,904 probes, 576,467 scans entered, 576,417 find an empty slot, so only 50 (0.006 %) do an
age/depth comparison.

## Headline results to list
- 29-F35 rule: bench is not a representative workload for ANY slot-sensitive or TT-cost optimisation
  (96.0 % slot-0 hits vs 26/25/25/24 %; 0 vs 16,811 generation writes; 50 vs 11.1 % age/depth).
- 29-F36 recommendation: picker scoring 2.91 % vs selection 0.77 % → reduce history reads per move, not the sort.
- 29-F16: PC r15 patch reproduces exactly; all eight known numbers match in all three regimes.
- 29-F19/F28/N16: my TT patch REVERSES on the PC build (+0.320 %) and is non-additive (−0.872 % interaction);
  it is code cleanliness, not a speed win.
- 29-N19 / FIRST RULE: a zero must always be a measurement, never a default.
- 29-F22/F23/F24/F29/F30: softnodes and `go nodes` contracts and determinism.
- 29-C7/C8: confirmations of 19-F19 and 19-F18 (bench half to the digit).
- 29-C6: confirmation of seat 05's S-F23 on the PC build under PC20.
