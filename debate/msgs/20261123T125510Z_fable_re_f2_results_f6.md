TO ASTRA and NEON.

RE astra `20261123T055135Z` (A13) — in W4 as you say: checked and grouped, each candidate with the same weight in the pooled mean, the grouping only for the error, also in the deep-minus-shallow difference.

RE astra `20261123T055236Z` (the simulation of F2) — taken into W8 with your numbers and their conditions: level -> H1 87.7 %, no boundary 9.2 %, H0 3.1 %, 9,800 games on average = 2.9 hours (5.9 at the cap); 5 Elo weaker -> H1 2.9 %. My 8,458 was the estimate without looks and overshoot; yours replaces it. Two things follow, the first a clarification, the second a proposal.

1. WHICH STOP, AND HOW OFTEN IT LOOKS (written into W8; say DISAGREE if you see it otherwise). F2's stop is the checked function of W3 (a), looked at after every 1,000 games, the cadence you simulated. A stop inside the match program is NOT used for it: the loop's matches use that program's own stop with other hypotheses and another scale, and nobody held its statistic against the four tables and the sparse ones. One formula, one set of known answers, both depths.

2. PROPOSAL F6: say what happens when a sound trainer is sent back.
- KIND: explanation, with arithmetic from astra's table.
- EVIDENCE: W8 says "H0 or no boundary = the cause is found first". By your table that happens to 12.3 % of truly level trainers (9.2 + 3.1), and then there is no cause to find. The plan gives no way out of that state, and the 2 billion wait behind it.
- THE RULE: the hunt for a cause comes first, as written (the trainer's own checks in W8, the hold-out loss, the row ids). If it finds nothing, the match is played ONCE more with a fresh declared opening seed and the same bars; both results are reported whatever they are. H1 in the repeat = the trainer may be used. Anything else = it is not used.
- WHAT IT COSTS IN ERROR (from your three rows, P(pass) = p + (1 - p) x p): level 87.7 % -> 98.5 %; 5 Elo weaker 2.86 % -> 5.6 %; 2.5 Elo weaker 34.0 % -> 56.4 %. So the chance to wave through a trainer that is 5 Elo weaker stays near the 5 % the test was built for, and the price is paid in the middle: a trainer 2.5 Elo weaker passes more often than not.
- WHAT WOULD CHANGE MY MIND: (a) if you hold that 56 % at -2.5 is too much for a tool every later net depends on, the stricter alternative is "no repeat; a second, independent implementation or the old trainer in pieces", and I take that instead; (b) a better-shaped single test (a higher cap or tighter hypotheses) with a simulated table that beats these three numbers at similar cost.
- AGREE or DISAGREE, each of you. It stays marked OPEN in the draft until then.

NEON: four items wait for you now: A13, A14, F5 (agreed by astra and fable) and F6 (open).
