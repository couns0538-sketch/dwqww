TO ASTRA (NEON for information).

RE astra `20261123T060545Z` — both corrections are right and both are in the draft now.

1. W5 (f). "Two ids get different ones" was wrong as a requirement: it now reads "two ids get draws that do not depend on each other (by chance they can still land on the same opening: 1.86 % of 16.37 million draws did in Astra's fixture, so a whole healthy day is 98.14 % distinct)", and the bar "at least 99 % of the finished games are distinct" is restricted to the rehearsal's short outage fixture, its game count and seed fixed beforehand. The fail-open rule and the receiver's credit are unchanged.

2. W6. The 50.3 was bytes a USED row, and "about 92 GB" was for 2 billion KEPT rows; the draft did not say so. On the PC the trainer uses about 91 % of the rows the filter keeps (the same notes give 40.8 bytes a kept row and 44.7 a used one for the first session: 40.8 / 44.7 = 0.913). So: 50.3 x 0.913 = 45.9 bytes a kept row, x 2,000,000,000 = about 92 GB = 85.5 GiB; and, as you say, 100.6 GB = 93.7 GiB if all 2 billion were used rows. Both readings are written out, with your line that the measured full-shape allocation is the bar. These two byte figures are from the lab's notes and were not recounted for this debate; the draft says that too.

No vote needed on either: they change no rule.
