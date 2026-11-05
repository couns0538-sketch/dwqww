# T07-02: score-stability scaling of the soft limit (stop sooner when the score holds still)
Status: COMPLETE

## Source
Alexandria PR 618, commit https://github.com/PGG106/Alexandria/commit/49391d7b70f3d90b936f6db9c646e37e8fba1858
(2026-07-22, "Introduce score stability TM scaling"). OpenBench logs: STC https://chess.swehosting.se/test/14309/
(branch tm-scoreloss-iso vs master), LTC https://chess.swehosting.se/test/14310/ (same branch; both pages read).
Earlier, possibly still coexisting: PR 438, commit https://github.com/PGG106/Alexandria/commit/8e3fc66e52
(2024-06-24, "Introduce eval stability in time management"); whether 618 replaced 438 was not checked (no source read).

## Licence
GPL-3.0 at 49391d7b70 (notes/T07/licences.md) -> ideas only. Read: commit messages, PR 618 text, both OpenBench pages.
No source file, no diff.

## Mechanism
Exact source formula not read (licence); this is this worker's design of the idea. Keep a counter of consecutive
completed iterations (depth >= 4) whose score stays within +-W cp of the previous iteration's score. Any score move
outside the window or a mate score resets it to 0 (a new best move does not: TmUnstableFactor covers that). The
soft-limit factor gets one more term, g = max(Gmin, 1 - Step * min(count, Cap)); g = 1 at count 0.
Reduce-only: a falling score resets the counter and is
then handled by the lock's falling-eval term alone, so the two terms never pull against each other. The branch name
tm-scoreloss-iso hints the source may also weigh score losses; that part is already Forge's falling-eval term.

## Forge fit
Lacks it. The lock scales the soft limit by best-move stability (src/search.cpp:1436-1438), node effort (1441-1449)
and falling eval vs the previous iteration (1451-1454, extend-only), then clamps at TmMinFactorPercent (1455).
Nothing shortens the search when the score holds still; the only score memory is previous_score (1374, 1428-1429).
`forge_has.sh 'score_stab|stable_score|eval_stab'` -> 0 hits. Change = one counter next to previous_score and one
multiply into `factor` before the clamp at 1455 (the clamp still bounds the product).

## Expected gain
Source (PR 618): STC 8+0.08 Threads=1 Hash=16MB, book UHO_Lichess_4852_v1.epd, +4.24 +- 2.63 (95 %), 16,560 games,
LLR 2.89 (-2.25, 2.89) bounds [0.00, 3.00], Penta [28, 1830, 4365, 2026, 31]; LTC 40+0.4 Threads=1 Hash=64MB
+4.00 +- 2.49, 16,844 games, LLR 2.91 [0.00, 3.00], same book. Alexandria dev vs master. PR 438: STC
+1.42 +- 1.15 (92,920 games), LTC +1.71 +- 1.37 (56,588 games), same TCs and bounds.
Forge estimate: +1 to +4 Elo (lower end of the source's 95 % ranges is +1.6 STC / +1.5 LTC; Forge's best-move
stability term may already take part of it) **UNPROVEN**.

## Effort
Crew 3 h (counter + factor + 3 options 1 h, OFF inspection + box test 1 h, packaging 1 h). CPU: STC SPRT [0,5] about
7-10k games if the true gain is near +4 = 7-16 h at the 640-980 games/h seen in D:/o15/reports/gates_20261103.html;
LTC after an STC pass; optional short SPSA of W / Step / Gmin with the forge-o30-spsa tuner. GPU 0.

## Test plan
Pre-gate: bench / perft pins OFF and ON equal the lock by construction (depth-limited bench never runs the soft-stop
block), so OFF is proved by code inspection (g is exactly 1.0 when OFF) plus a box test: a verify build prints
`info string tm iter <d> count <n> g <x> factor <y>` per iteration; on 20 FENs at `go wtime 10000 winc 100` the OFF
factor sequence equals the lock's and ON differs only by g; check count resets on a score drop and on mate scores.
Gate route: UHO SPRT [0,5] at STC, then LTC; gate_summary must show 0 time forfeits and unchanged mean depth.

## OFF-by-default design
Options (own values, not the source's): TmScoreStab spin default 0 (OFF) range 0-1; TmScoreStabWindow default 12 cp
(2-50); TmScoreStabStep default 3 (x0.01 per stable iteration, 0-10, Cap 8 iterations fixed); TmScoreStabMin default
75 (x0.01, 40-100). OFF: the counter is not read, `factor` is the lock's, so every timed search is the lock's; bench
pins equal.
