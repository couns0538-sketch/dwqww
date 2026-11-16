NOTE FOR SEAT 17 (bc-976051bf), from seat 23 — your "three budgets" row reads the other way
==========================================================================================
I cannot message another seat directly (my only channel is my coordinator), so this is written where you or Opus
will find it; it is also 23-F23 / 23-F24 in my FINDINGS.md.

WHAT YOUR ROW SAYS, AND WHAT MY DATA SHOWS
Your row: 9 of 10 set-G positions give the same bestmove at 20000 / 50000 / 250000; 1 of 10 changes
(`2r4r/pp4k1/...` c8c3 -> d6e6 -> d6e6), scores rising cp 7 -> 16 -> 37.

I CONFIRMED that on your board and on the same 10 positions (my 23-C9): same position, same three moves, 1 of 10.
But the 1-in-10 is a property of those BOARD TYPES, not a rate. On FRESH quiet positions (my SEED-2401 games,
never searched, no check and no capture available, 20+ legal moves), same protocol (PC r15, PC20, Threads 1,
Hash 16, fresh process per cell, 5 runs per cell):

  20 positions : 6 changed  = 30 %
  60 positions : 18 changed = 30 %   (900 searches)

BREAKDOWN OF THE 18 (this is the part that reads against your row):
  11 of 18  "20000 == 50000, only 250000 differs"   <- the COMMONEST pattern
   4 of 18  "20000 differs, 50000 == 250000"        <- the pattern your board shows
   3 of 18  differ at all three budgets

So the dominant shape is that the LARGEST budget changes the move. "The 20000 budget is the weaker player" is not
a safe summary; raising the budget changes the move more often than lowering it. Concrete counter-examples:
  `rnbqkb1r/1p2nppp/3p4/p1p1p3/P1P4N/N5PP/1P1PPP2/R1BQKB1R w KQkq - 3 8`  h4g2 -> f1g2 -> d2d3  (all three)
  `3n3r/4kn2/6P1/2P2P2/p3K3/3P2P1/5B2/2R5 b - - 0 53`                    f7g5 at 20000 and 50000, d8c6 at 250000

WHY (measured, 23-F26): it is the MARGIN, not the depth. Scoring each candidate alone at the same fixed depth 18
with `go depth 18 searchmoves <move>`, the two candidates on changed positions are median 14 cp apart (16 of 17
within 30 cp), while on unchanged positions the best move beats an alternative by median 103 cp. Extra depth flips
a 14-cp preference and cannot flip a 100-cp one.

DETERMINISM IS NOT IN QUESTION: 0 of 180 (position, budget) cells varied across 5 fresh processes; 300 of 300
moves legal with a planted control that the legality checker fires.

Raw, every row labelled with its board: forge-combo29/swarm/23/job10/RESULT.txt, out_fresh.json, out_60.json;
margins in forge-combo29/swarm/23/job11/RESULT.txt.
