# T07-02: score-stability scaling of the soft limit (stop sooner when the score holds still)
Status: COMPLETE

## Source
Hold-still term: Alexandria PR 438, commit https://github.com/PGG106/Alexandria/commit/8e3fc66e52 (2024-06-24,
"Introduce eval stability in time management"); results from the commit message, no test links in commit or PR.
Related: Alexandria PR 618, commit https://github.com/PGG106/Alexandria/commit/49391d7b70f3d90b936f6db9c646e37e8fba1858
(2026-07-22, PR title "Introduce score stability TM scaling", but its only code commit is "Add TM score-loss scaling
factor" and the test branch is tm-scoreloss-iso, so it most likely measures score LOSS). OpenBench logs:
https://chess.swehosting.se/test/14309/ (STC), https://chess.swehosting.se/test/14310/ (LTC), both read.

## Licence
GPL-3.0 at 8e3fc66e52 and at 49391d7b70 (notes/T07/licences.md) -> ideas only. Read: commit messages, PR 618 text,
its commit titles (no files / patch), both OpenBench pages. No source file, no diff.

## Mechanism
Exact source formulas not read (licence); this is this worker's design. A (the card): count consecutive completed
iterations (depth >= 4) whose score stays within +-W cp of the previous iteration's; a score move outside the window
or a mate score resets the count (a new best move does not: TmUnstableFactor covers that). The soft-limit factor
gets g = max(Gmin, 1 - Step * min(count, Cap)), g = 1 at count 0. Reduce-only: a falling score resets the count and
is left to the lock's falling-eval term, so the two never pull against each other.
B (variant, closer to PR 618's commit title): also measure the score loss against the previous move's final score,
not only the previous iteration. Whether PR 618 uses that reference is unverified.

## Forge fit
Lacks a hold-still term: `forge_has.sh 'score_stab|stable_score|eval_stab'` -> 0 hits. The lock scales the soft
limit by best-move stability (src/search.cpp:1436-1438), node effort (1441-1449) and falling eval (1451-1454:
extend-only, drop capped at 150 cp, reference = previous iteration of the same search; previous_score restarts at
1374 every search, so there is no cross-move reference), then clamps at TmMinFactorPercent (1455). Change A = one
counter next to previous_score (1428-1429) and one multiply into `factor` before 1455; B = keep the last search's
final score in the Searcher and feed it to the drop term.

## Expected gain
Source A (PR 438): STC 8+0.08 Threads=1 Hash=16MB +1.42 +- 1.15 (95 %), 92,920 games, LLR 2.91 (-2.25, 2.89)
bounds [0.00, 3.00], Penta [382, 10602, 24096, 11014, 366]; LTC 40+0.4 Threads=1 Hash=64MB +1.71 +- 1.37, 56,588
games, LLR 2.90 [0.00, 3.00]; book not checked (no test links). Related (PR 618, score-loss factor): STC +4.24 +-
2.63, 16,560 games, LLR 2.89 [0.00, 3.00]; LTC +4.00 +- 2.49, 16,844 games, LLR 2.91; book UHO_Lichess_4852_v1.epd.
Forge estimate: +1 to +3 Elo, centre about +1.5 (the hold-still evidence is +1.4 / +1.7; the larger PR 618 gain is
from a loss measure that Forge partly has) **UNPROVEN**.

## Effort
Crew 3-4 h (A: counter + factor + options 1 h; B: 1 h; OFF inspection + box test 1 h; packaging 1 h). CPU: STC SPRT
[0,5] about 7k games at a true +4, about 15-18k at +1.5 (likely H0; own estimate) (review fix, critic summary (c) / B FINAL_REPORT:49-57: these counts read [0,5] as logistic Elo, ~[0,9.5] nElo on UHO = the cost of the [0,10] nElo gates, T12-01:26; read as nElo, [0,5] needs a mean ~26k games, T12-01:32 model; the owner's bounds decision replaces this route) = 7-28 h at the 640-980 games/h
in D:/o15/reports/gates_20261103.html (corrected by verify: the UHO gates vs the lock ran 430.6-455.7 games/h
there, all *_vs_AL1* rows 430-502, so 7k-18k games = about 14-42 h); LTC after an STC pass. Optional short SPSA of W / Step / Gmin. GPU 0.

## Test plan
Pre-gate: bench / perft pins OFF and ON equal the lock by construction (depth-limited bench never runs the soft-stop
block), so OFF is proved by code inspection (g = 1.0, B unused) plus a box test: a verify build prints
`info string tm iter <d> count <n> g <x> factor <y>`; on 20 FENs at `go wtime 10000 winc 100` the OFF factor
sequence equals the lock's and ON differs only by g; count resets on a score drop and on mate scores.
Gate route: UHO SPRT [0,5] at STC (A alone first, B as a second candidate), then LTC; gate_summary must show
0 time forfeits.

## OFF-by-default design
Own values, not the source's: TmScoreStab spin default 0 (OFF, 0-1); TmScoreStabWindow 12 cp (2-50);
TmScoreStabStep 3 (x0.01 per stable iteration, 0-10, Cap 8 fixed); TmScoreStabMin 75 (x0.01, 40-100);
TmScoreLossRef default 0 (0 = previous iteration as the lock, 1 = also the previous move's score). OFF: the counter
and the stored score are not read, `factor` is the lock's, so every timed search is the lock's; bench pins equal.
