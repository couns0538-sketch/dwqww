import io

p = 'FINDINGS.md'
s = io.open(p, encoding='utf-8').read()

old = ("LIMIT: one board of this shape; the mate is in 1, so it needs no search to see. "
       "| `cd forge-combo29/swarm/23/job68 && python3 cp0_correct.py` -> `cp0_correct.out`; `mate_vs_claim.out` | NEW |")
new = ("**AND IT IS GENERAL, NOT ONE BOARD (23-F172): across FOUR validated threefold roots where the mover has a mate in "
       "1, the base forfeited it on 4 of 4 \u2014 playing `f2f3` every time, regardless of which piece delivered the mate "
       "(`b1b8` for Q and R, `a1a8`, `c1c8`) \u2014 and the PC mated on 4 of 4.** So the sharpest-case claim survives four "
       "fixtures rather than resting on one. LIMIT: the mate is in 1 in every case, so it needs no search to see. "
       "| `cd forge-combo29/swarm/23/job68 && python3 cp0_correct.py` -> `cp0_correct.out`; `mate_vs_claim.out`; "
       "`mate_forfeit_general.out` | NEW |")
assert old in s, "F171 tail not found"
s = s.replace(old, new, 1)

row = (
    "| 23-F172 | 3 | **THE MATE-FORFEIT IS GENERAL: 4 of 4 validated threefold roots where the mover has mate in 1, and the "
    "base forfeits it every time.** Same search as 23-F171 over eight candidates: four had a neutral cycle AND a mate in 1 "
    "at the threefold root, and in every one **the base plays `f2f3` \u2014 the generator's first move \u2014 and forfeits the "
    "mate, while the PC plays the mating move.** So the forfeit does not depend on which piece delivers the mate or where "
    "the queen starts; it is the mechanism. **This is the one-fixture rule applied to my own sharpest claim, and the claim "
    "survived four fixtures instead of one.** Four candidates were excluded and printed: one with no neutral cycle, three "
    "whose root had no mate in 1. LIMIT: mate in 1 in all four, so no search is needed to see it \u2014 a mate in 2 or 3 at a "
    "threefold root is untested and would be the harder case. "
    "| `cd forge-combo29/swarm/23/job68 && python3 mate_forfeit_general.py` -> `mate_forfeit_general.out` | NEW |\n"
)
s = s.rstrip('\n') + '\n' + row
io.open(p, 'w', encoding='utf-8').write(s)
print("F171 extended and F172 appended")
