# PREDICTION — job1 round 2 (area 1, SEED 1111, new position set R')

Committed and pushed ALONE before the first measuring command of this round. Never edited.
This is brief step 2(c): job 1 of my area again, next seed, a NEW position set (R with SEED+10).

What differs from round 1, stated before measuring:
  - mutation seed 1101 -> 1111 (different mutations chosen),
  - position set R regenerated from random games with seed 1111 (round 1 used 1101),
  - G is the same 353-position file (the brief does not ask for a new G),
  - the runner is the FIXED one (thread+queue timeout); round 1's committed numbers were
    produced with a runner that could not detect a hang, so this round's numbers are the first
    whose harness can prove a non-answer would have been seen.

1. Refusal rate lands in 82–88 % (round 1 was 85.65 %, and the mutation distribution is
   identical by construction, so only the RNG differs).
   KILLED IF: < 80 % or > 90 %.

2. python-chess agreement among accepted FENs is ≥ 99.0 % (round 1: 99.164 %).
   KILLED IF: < 98.5 %.

3. Exactly the same two defect classes as round 1 appear — adjacent digits in a rank, and
   nothing else — and their count is between 10 and 60.
   KILLED IF: a THIRD class appears, or the count is 0, or > 120.

4. 0 crashes, 0 sanitizer lines, 0 illegal bestmoves.
   KILLED IF: any crash, any sanitizer line, any illegal bestmove.

5. The round-1 defect F1 (extra tokens after the sixth field) is NOT reachable by this
   mutation set, because none of the five mutations appends a token after field 6 — "drop"
   removes one and "swap" permutes. So I predict 0 cases of F1 here and I will say so.
   KILLED IF: an F1-style case appears (that would mean my mutation generator can append,
   which I did not write).

6. Wall time under 10 minutes for 20,000 cases with the fixed runner (round 1 took about 40 s
   of engine time but a slow first run; the fixed runner should be faster).
   KILLED IF: over 20 minutes.
