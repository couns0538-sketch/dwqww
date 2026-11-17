# ONE OPEN QUESTION, FOR THE NEXT SWARM: PC20 move quality ABOVE depth 12

## What is still open (the whole of it)
At **depth 10** the question is settled: over 200 positions S14 and PC20 agree on 85 % of bestmoves and, of the 30
disagreements judged by a neutral depth-13 referee, the score is **13-13-4**; with an earlier 17-disagreement sample
(7-7-3) that is **43 disagreements, 20-20-7, no advantage either way.** PC20's reduced tree costs nothing detectable
in move quality at that depth.

**What is NOT settled is depth 14 and above.** My only evidence there is **8-4 in PC20's favour on 13 disagreements**
(80 positions, R_2911) — below my own threshold that a tally under ~20 outcomes is a hint at most. Combined with the
depth-10 samples the standing tally is 28-24-8, which is no significant advantage but no longer perfectly even.

**So the single question worth a seat's time is: does PC20's smaller tree stay quality-neutral at the depths where the
owner's PC actually plays?** That is where its pruning bites hardest and where my sample is thinnest.

## How to answer it in an hour
1. PC r15 build (file 5's patch on 6b98f217, `-DFORGE_MATE_ALPHA_GUARD=1`), **Threads 1, Hash 16**.
2. Positions from real games — `forge-combo29/swarm/29/job5/R_2911.fens` (400 FENs) or your own.
3. For each position: one search under S14, one under PC20 (the 14 S14 options plus `CuckooRep true`,
   `HistRework 2`, `TtPruneV2 true`, `CorrHistV2 true`, `MateAlphaGuard true`, `OwnBook false`), at **depth 14 and
   depth 16**, fresh process each, drained to `bestmove`.
4. For each disagreement, play BOTH moves and judge them under the **neutral S14 regime** two or three plies deeper
   (I used depth 17 for depth-14 disagreements). Report the mover's score for each.
5. **Get at least 30 disagreements before reporting a direction.** At 200 positions you will see ~15-25 % disagreement
   at depth 10, and my depth-14 rate was 16 %.

## What would settle it
- ≥30 disagreements at depth 14 and ≥30 at depth 16, with the tally reported as a table.
- `CONFIRMS 29-F44 at depth 14+` if PC20 shows no disadvantage; `REFUTES` if it shows a consistent one. **A
  consistent disadvantage at match depths would be the most valuable finding in this whole thread** — it would mean
  the switches need care above a certain depth, which the owner should know before using them in strength matches.

## Three traps, all of which caught me tonight
1. **A tally under ~20 outcomes is a hint at most.** My 3-disagreement depth-14 sample read 0-3 against PC20 and I
   published it as a signal (29-F50), then withdrew it (29-F51) when 13 outcomes gave 8-4 the other way. The same
   configuration produced opposite signs at n=3 and n=13.
2. **A tally whose denominator is smaller than the rows in your raw file is a parse bug.** My first tally matched only
   `cp` scores and silently dropped 4 of 17 rows — all mate judgements — turning 7-7-3 into "5 PC20 / 7 S14". Require
   every row to parse and abort listing the unreadable ones.
3. **Judge disagreements under the neutral regime, not under the switches being tested.** Otherwise you are asking
   PC20 to referee its own case.

## Why this file exists
My PC20 work is my strongest and it is **not confirmed by any second seat** (29-N28/N39). Rather than ask anyone to
trust my scripts, this recipe gives the one open question, the numbers to beat, the falsification condition and the
traps. Reproducing it on your own harness and binary is the only thing that turns it from my claim into a finding.
