# PREDICTION - committed BEFORE measurement (19-C48: independent check of 29-F55)

## What I am checking
Seat 29's 29-F55 / REPRODUCE_pc20_quality.md: PC20 vs S14 bestmove quality at depth 14, claiming
**84.5 % agreement and 19-10-2 over 31 disagreements, in PC20's favour**, over 600 positions total.
Seat 29 states it is unconfirmed by any second seat and gives the numbers to beat.

## My setup (independent, my own choices where free)
- Builds: PC r15 `~/pcbuild/build/forge` and base `~/build_rel/forge`, both `id name ... 6.4.24 candidate`.
- Positions: seat 29's own `R_2911.fens` (400 lines) - I use a deterministic subset **I** pick:
  lines 1,3,5,... (odd lines, 200 positions). Not their slice, so not a shared parse bug.
- Threads 1, Hash 16, fresh process per search, drained to `bestmove`.
- S14 = the 14 option lines; PC20 = S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
  MateAlphaGuard true, OwnBook false.
- Judging: for each disagreement, play each move and search the resulting position under the **neutral S14
  regime** (not PC20 - PC20 must not referee its own case) at depth 17, comparing the mover's score.

## My prediction, stated before any number exists
1. **Agreement 80-90 %.** A large disagreement count would mean I parsed or set up differently from seat 29.
2. **The judged split will be NEAR EVEN - I predict 45-65 % of decisions for PC20, i.e. NO clear winner.**
   Reason: 49-36-11 over 96 is sign-test p ~ 0.10, which is not significant, and my sample is smaller than
   their 600. **A clear PC20 advantage on my 200 positions would surprise me; a clear S14 advantage would
   surprise me more.**
3. **Kill condition for my own method:** if agreement lands outside 80-90 %, or if the disagreement
   denominator is smaller than the number of positions I know disagreed, I do not report a direction at all.

## What each outcome would mean
- Near-even -> **CONFIRMS "no disadvantage"**, does NOT confirm "possibly better" (that needs significance).
- Clearly PC20 -> strengthens 29-F55 beyond what its own p-value supports.
- Clearly S14 -> **REFUTES**, and that is the most valuable result, because PC20 is what the owner runs.
