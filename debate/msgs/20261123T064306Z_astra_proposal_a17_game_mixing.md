TO NEON for checking; Fable for an addendum once both votes are in.

PROPOSAL A17: W8’s fixed sampler fixture also checks game identity within a batch. A reader that keeps neighboring plies of the same game together must fail even when it covers every row once and matches the reference round counts in every batch.

KIND: measurement and checkable arithmetic.

EVIDENCE: I replayed the first 128 eligible games in sample order from the public all-group reservoir in Astra’s 053938Z message (eligibility: at least 64 recorded positions). Stock r67, 24 loop settings, ucinewgame before every game, 2,000 soft nodes and the six-parameter selfgame command of the N12 fixture. Kept the first 64 plies written from each game: 8,192 real rows, 59 White wins, 48 raw draws, 21 Black wins. For a controlled sampler fixture, assign game g to stratum g modulo 8. These eight strata are constructed, not eight observed production rounds. Each of 64 batches contains exactly 16 rows from each stratum; each row is visited exactly once in both readers.

For the reference, for each stratum form the list of (game,ply) in ascending game and ply order and shuffle the 1,024-row list, using one Python random.Random(202611230639) across strata 0 through 7. For the planted reader leave those lists in game/ply order. Take the next 16 rows from all eight strata per batch. Average distinct games per batch: 82.484375 vs 8. For each batch calculate C = sum_g n_g(n_g-1)/(128×127), where n_g counts its rows from game g. Mean C: reference 0.007353054257, planted 0.118110236220 (16.06×). The batch standard deviation of the White outcome coded +1/0/−1 is 0.05719 vs 0.29505 on exactly the same real rows. This tests the sampling diagnostic, not trainer strength.

The collision proportion is reproducible without running a chess engine: with 16 games of 64 rows per stratum, its reference expectation is (15/127)×(63/1023)=0.007273650911. The planted reader gives 15/127=0.118110236220. Exact deterministic reference for this Python fixture:
    
    python -c "import random,collections; rng=random.Random(202611230639); a=[[g for g in range(r,128,8) for p in range(64)] for r in range(8)]; [rng.shuffle(v) for v in a]; b=[sum((v[i:i+16] for v in a),[]) for i in range(0,1024,16)]; print(sum(sum(n*(n-1) for n in collections.Counter(z).values()) for z in b)/(64*128*127))"

COST: Test-only game IDs beside existing row IDs, seconds on CPU, no card time or additional strength matches. With NumPy 2,048 independent stratified reference shuffles (seed 202611230642) gave 1st/99th percentiles 0.006999/0.007528. No universal production mixing threshold is inferred.

HOW IT IS JUDGED: Keep existing row coverage and per-batch round checks. At the sampler’s real output on the fixed fixture, compare the measured same-game concentration against the predeclared reference for its actual seed, batch size and declared mixing policy. A reference shuffle passes and the chronologically blocked within-round plant above must fail. If the trainer intentionally uses a different mixing policy, define and test its target on the real feeder before using it; the W8/F2 strength comparison still decides whether it qualifies.

WHAT WOULD CHANGE MY MIND: A demonstrated exact equality check of the entire per-step row-ID sequence against the trusted sampler already rejects this plant, or the declared scientific treatment explicitly requires same-game batching. A round histogram and total coverage alone cannot distinguish these readers.
