# Of the 11 equal-depth disagreements, whose move is better? MIXED, leaning BASE

Answer to the question in S-F28. **Mixed: base's move better in 6, PC20's better in 2, equal within 20 cp
in 3.** The median gap is 33 cp, the largest 221 cp.

## Design and the control that validates it
- **One judge for both sides**: every re-search uses the BASE build, so neither build gets a judge advantage.
- **Same depth for both moves** in a pair: `go depth 18`.
- **Scores converted to White's point of view.** The engine reports relative to the side to move; after the
  move the opponent is to move, so the sign must flip for White. Mate scores map to ±100000.

**A control caught two real bugs before any result was used.** Scoring a mate-in-1 move against a quiet
move on the same board must favour the mate. The first version reported the mate as WORSE because
(a) my terminal branch reported a checkmated side as `mate 1`, i.e. as if the mated side were mating, and
(b) `white_cp` mapped `mate 0` to a score of 0 instead of a loss. After the fix the control passes: mate =
+100000, quiet move = +1006. Both fixes are commented in `who_wins.py`.

## The table — pasted output of `who_wins.py` (`who_wins.log`)

| # | position | base move | PC20 move | base raw | PC20 raw | base (White cp) | PC20 (White cp) | gap | better |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w | e4f5 | f4f5 | cp -4249 | cp -4335 | 4249 | 4335 | +86 | PC20 |
| 2 | 2r4r/pp4k1/3q2p1/3ppn2/1P4QP/P2P1N2/R4P2/4RK2 b | f5h6 | d6e6 | cp 0 | cp -31 | 0 | -31 | -31 | base |
| 3 | 8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w | g5h5 | g5h6 | cp 1795 | cp 1574 | -1795 | -1574 | +221 | PC20 |
| 4 | 4r1k1/2pn1pp1/1p5p/p3p3/PP2P3/2PB2P1/5P1P/R5K1 b | c7c6 | e8d8 | cp 18 | cp -18 | 18 | -18 | -36 | base |
| 5 | rn2r1k1/pp3pp1/1q3n2/2bpp3/6bR/1BPP1N2/PP1NQP2/R1B1K3 b | b6c6 | b6d6 | cp -326 | cp -354 | -326 | -354 | -28 | base |
| 6 | 8/7p/6k1/1p1r1p2/pb3P2/3BK1BP/P7/8 w | g3h4 | d3c2 | cp 686 | cp 902 | -686 | -902 | -216 | base |
| 7 | r2q1knr/1bp1b1Np/pp1p2p1/2n1p3/2B1P3/2N5/PPP2PPP/R1BQ1RK1 w | g7h5 | g7e6 | cp -175 | cp -120 | 175 | 120 | -55 | base |
| 8 | 8/p7/5pk1/7p/r2NKP2/4P1P1/PR5P/8 b | a4a3 | a4a5 | cp 1065 | cp 1032 | 1065 | 1032 | -33 | base |
| 9 | 8/8/8/4kPK1/4B2P/2R5/8/8 w | e4b1 | c3c4 | mate -15 | mate -8 | 100000 | 100000 | +0 | equal |
| 10 | 8/8/4r3/7K/3k4/8/8/8 b | d4e4 | d4e3 | mate -10 | mate -10 | -100000 | -100000 | +0 | equal |
| 11 | 7r/2k2p2/2p3P1/2Ppn3/PP2p1b1/4P3/4BK2/R6R b | h8b8 | h8h1 | cp 647 | cp 657 | 647 | 657 | +10 | equal |

PC20 move better: 2, base move better: 6, equal (<20 cp): 3, of 11 judged
median |gap|: 33 cp; largest |gap|: 221 cp

## Reading it honestly
**This is a mixed result, and it leans BASE.** Six of eleven to base against two to PC20 is not a clean
pattern (my prediction X5 said no clean pattern and that held; X1 predicted 3-6 for PC20 and got 2, so X1
is killed). Two of the three "equal" rows are decided positions where both sides are mated or mating
(`±100000`), which carry no information about move choice — excluding them, the informative split is
**base 6, PC20 2, equal 1**.

I am NOT going to summarise this as "the switch set is weaker". Eleven positions, one depth, one judge is
far too little to estimate strength, and three of the eleven are decided positions. What it does say
precisely: **on the positions where the two builds disagreed at fixed depth 20, a deeper look on a neutral
judge found base's move better more often than PC20's** — 6 to 2 — which is the opposite of what would make
the switch set look like a strength gain, and is a reason for the owner to run the match rather than assume
the switches are free.

## The 20 cp threshold
I chose 20 cp as "effectively equal" in the prediction and kept it. With gaps of 31, 33 and 28 cp sitting
just above it, the split is sensitive to that constant: at a 40 cp threshold the count becomes base 4,
PC20 2, equal 5. I report the raw gaps above so a reader can re-threshold without re-running anything.

## Reproduce
```
cd forge-combo29/swarm/28/pc20
python3 who_wins.py ~/build/base-release/forge /tmp/who 18
```
Raw: `out_who/who_wins.tsv`, `who_wins.log`.
