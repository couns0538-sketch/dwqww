# S02 check of seat 20's S-F20 (`LmpBase=8` loses a mate score) — CONFIRMS, with one correction

Their claim: "`LmpBase=8` **delays mate discovery** … at depths where the default already proves mate, it
reports a big negative cp … The same setting finds the mate two plies deeper."

## what I measured (my own harness, `check_lmpbase.py`, every search COLD in a fresh process)

```
deep_mate    default    d8:cp -2665  d10:mate -7  d12:mate -7  d14:mate -6
deep_mate    LmpBase=8  d8:cp -2667  d10:cp -2884  d12:cp -3114  d14:mate -9
mate_in_1    default    d8:mate 1  d10:mate 1  d12:mate 1  d14:mate 1
mate_in_1    LmpBase=8  d8:mate 1  d10:mate 1  d12:mate 1  d14:mate 1
```

Every number matches seat 20's table exactly, including the `-2665 / -2884 / -3114 / mate -9` ladder and the
untouched mate-in-1.

### verdict checks (printed by the script that measured them)

```
- default reports `mate` at d10 on the deep board                              PASS
- default reports `mate` at d12 on the deep board                              PASS
- LmpBase=8 reports cp (not mate) at d10 on the deep board                     PASS
- LmpBase=8 reports cp (not mate) at d12 on the deep board                     PASS
- LmpBase=8 DOES find a mate at some depth <= 14 (so: delay, not breakage)     PASS
- mate-in-1 is untouched by LmpBase=8 at every depth                           PASS
- no mate PV replays to a WRONG position                                       PASS
```

## beyond the finding: the "longer distance" is a TRANSIENT, not a lasting defect

Seat 20 records that at d14 the tuned setting claims `mate -9` where the default claims `mate -6` — a LONGER
distance, which reads like worse mating. I pushed past d14:

```
default    d16  score mate -4   nodes 28123
default    d18  score mate -4   nodes 32389
LmpBase=8  d16  score mate -5   nodes 60586
LmpBase=8  d18  score mate -4   nodes 68037
```

At d16 and d18 the two settings converge to the SAME `mate -4`. So `mate -9` at d14 is not a wrong distance and
not a permanent handicap: it is an unconverged bound that converges to the true value two plies later. The cost
of `LmpBase=8` on this board is therefore the two-ply delay plus a higher node count at equal depth
(68,037 vs 32,389 at d18, about 2.1x) — not a worse answer in the end. Raw: `out/deep_ladder.txt`.

## a PV-replay caveat that changes how to read the mate scores

I replayed every `mate N` PV in python-chess and required checkmate after 2N-1 (N>0) or 2|N| (N<0) plies.
Result: **11 verified as real checkmates, 5 TRUNCATED short of the claimed distance, 0 wrong**. The
`mate -9` PV, for instance, carries only 17 of the 18 plies it claims (the engine truncates the PV at its
search depth). That is why I report truncation as its own verdict instead of counting it as a pass or a fail:
a truncated PV neither proves nor disproves the score, and calling it either would be the vacuity seat 19
warned about.

## verdict: CONFIRMS S-F20
The delay is real at the depths they named, mate-in-1 is untouched, and the tuned setting does recover a mate
rather than losing it. My addition is that the recovered distance converges to the default's at d16-d18, so
"a longer claimed distance" describes d14 only and should not be read as a lasting defect.

## what I did NOT do
- Did not test boards other than the two they named; their "narrow" claim is a statement about a wider sample
  than I measured, and I neither confirm nor refute its narrowness.
- Did not use the node counts for any comparison across settings: per seat 10's rule, node counts are only
  comparable cold, and these ARE cold (one search per process), but the two settings search different trees by
  construction so the ratio is descriptive only.

## the two harness faults this check hit first (recorded, because they are the point of today's warnings)
1. My first version PIPED the session and closed stdin; the engine answered `bestmove c2b1` with NO info line.
   My assertion aborted the check rather than recording a number — 19-F12 caught by construction.
2. My first PV replay treated a TRUNCATED pv as a failure, which would have turned a correct mate score into a
   refutation. That is the same class of error as reading a missing line as agreement, in the other direction.

## times
see the `date -u` line in the commits; `out/meta.json` holds the exe and its sha256.
