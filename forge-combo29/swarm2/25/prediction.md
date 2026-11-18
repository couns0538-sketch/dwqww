# Prediction — seat 25, group 5 part 5

Written after the three P ladders matched all 20 rows each, and before the first measured run
of the census. Not edited afterwards.

## The quantities my group asks for

M = the census positions where setting A (S14) reports a positive mate as its last score at
`go depth 16`. The census is 120 positions (40 games x 3 plies-before-the-end).

| quantity | prediction range |
|---|---|
| share of M that B (S14 + HistRework 2) does not find by depth 16 | 10 % to 45 % |
| share of M that E (PC20) does not find by depth 16 | 15 % to 50 % |
| share of M that B finds LATER than A | 0 % to 15 % |
| share of M that E finds LATER than A | 0 % to 15 % |

## Why these numbers

These are real game positions with a mate in 2, 3 or 4 available, searched to a fixed depth 16.
A fixed depth 16 is deep against a mate in 4, so I expect A to find most of them and M to be a
large fraction of 120 — most likely 90 or more.

HistRework 2 is the known offender on the single P position, where it never reports the mate
through depth 20. But that position needs the quiet mate `g3g6`, and these census positions are
endgame-adjacent finishes where the mating move is often a check or a capture. A checking or
capturing mate is far harder for a history-driven rule to hide, so I predict a real but partial
loss, not a wipeout. PC20 is set as the same rule plus five more switches, so I put it slightly
higher than B.

The "found later than A" shares are predicted low because this is a fixed-depth comparison: a
setting that finds the mate at all on a mate-in-4 generally finds it at the same depth, and the
one setting that misses it tends to miss it entirely rather than merely delay it. In the ladder,
B and PC20 do not find the mate at ANY depth, so the delay bucket may well be zero. I give it a
non-zero range because the ladder is one position.

## What would surprise me

- M below 60. That would say a fixed depth 16 misses the mate in most real finish positions, which
  is a much larger claim than the P ladder supports.
- Any share above 60 % for B. That would make HistRework 2 close to uniformly mate-blinding rather
  than selectively so.
- A large "found later" share. It would mean the rule delays mates rather than losing them, which
  is a different defect from the one the ladder shows.
