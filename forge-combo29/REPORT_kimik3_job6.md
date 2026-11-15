# kimik3 job 6 report: the time-management switches measured, and TmStability

**Headline.** On the node clock (both sides `NodeClock 100`, 10+0.1, 1,000 games each, complete colour-reversed
pairs): **TmFinishIteration on vs off: +21.6 Elo [+6.0, +37.3] 95 %** — a clear gain, the first time-management
measurement this engine has ever had. It spends 6 % fewer nodes a move and hits the hard limit 5 times less
often (104 vs 534 stops). **TmNodeShare on vs off: −9.7 Elo [−24.8, +5.3]** — a likely loss. **Both on (T3):
+0.0 Elo [−15.9, +15.9]** — the two cancel; TmNodeShare drags the TmFinishIteration gain away. **TmStability,
the new switch of Part B (T4): −8.0 Elo [−21.8, +5.8]** — it spends *more* nodes a move (+1.1 %), hits the hard
limit nearly twice as often (623 vs 334), and still loses: more of this medicine does not help. Node-time
forfeits in 4,000 games: exactly two, both by the OFF side in T3. No game hit the 200-move cap. The base engine
at `NodeClock 100` spends a mean of 26,201 nodes a move, uses a mean 1.18 of its soft limit, and stops at the
hard limit on 1.4 % of moves. The 20-games-twice proof of job 5 was rerun at the new scale: identical move for
move. Nothing was cut: T3 and T4 both reached 1,000 games inside the budget.

**Correction to job 5, first:** my Part A "weak points" 1 and 2 were wrong. The engine already scales the soft
limit by best-move stability (`TmStableFactor`/`TmSemiStableFactor`/`TmUnstableFactor`, search.cpp:2578-2580 of
the job-5 tree) and by score trend (`TmFallingEvalPercent`, search.cpp:2596-2599), both always on. I missed
them. Part B below therefore implements the new switch as an *additional* scale with my own constants, so that
off is byte-identical and on tests whether more of this medicine helps.

## The match form, and the base picture

Runner `match6.py.txt` (python-chess; one engine process per side). Both sides `NodeClock 100`, Threads 1,
Hash 16, OwnBook false, TC 10+0.1 tracked in node-milliseconds (budget 10,000, +100 a move, decremented by the
search's `time` field). The real clock is never consulted, so nobody can lose on real time by construction; a
side out of node time loses. Openings: UHO (`uho200.epd`), each twice with colours reversed — game 2k and 2k+1
are one pair, pair id k. Pair order shuffled with `random.Random(seed)` — this runner's equivalent of
`order=random -srand <seed>` (stated here because I do not use cutechess). No adjudication: games end by the
laws of chess via python-chess `is_game_over(claim_draw=True)`; a 200-fullmove safety cap exists (never hit).
Elo: 400·log10 of the mean pair score, 95 % interval from the per-pair score distribution (`elo_pairs.py.txt`),
complete pairs only — all 500 pairs completed in every match.

Base engine (switch-free, from the 20-game double run at seed 7500 plus the off-sides of T1/T2, which agree):
mean 26,201 nodes a move (262 node-ms), mean 1.18 of the soft limit used, 30 of 2,080 moves (1.4 %) ended at
the hard limit (a move whose used time reached ≥ 95 % of the computed hard limit; the engine does not log the
reason, so this is the runner-side count). The soft share above 1.0 is expected: the soft limit gates starting
a new iteration, and the finished iteration overshoots; late in a game the budget is small and the +75 floor
dominates.

## The one table

| match | switch on (A) vs off (B) | games/seed | W-L-D (A view) | Elo [95 %] | nodes/move A | nodes/move B | hard stops A/B | soft share A/B | forfeits A/B |
|---|---|---|---|---|---|---|---|---|---|
| T1 | TmFinishIteration | 1000 / 7501 | 341-279-380 | **+21.6 [+6.0, +37.3]** | 23,315 | 24,924 | 104/534 | 0.91/1.16 | 0/0 |
| T2 | TmNodeShare | 1000 / 7502 | 298-326-376 | **−9.7 [−24.8, +5.3]** | 24,763 | 25,368 | 367/476 | 1.08/1.16 | 0/0 |
| T3 | both on | 1000 / 7503 | 294-294-412 | **+0.0 [−15.9, +15.9]** | 22,863 | 25,291 | 93/413 | 0.83/1.15 | 0/2 |
| T4 | TmStability (new) | 1000 / 7504 | 289-312-399 | **−8.0 [−21.8, +5.8]** | 26,093 | 25,818 | 623/334 | 1.20/1.15 | 0/0 |

nodes/move in real nodes (node-ms × 100). Hard stops = moves at ≥ 95 % of the computed hard limit.

Reading: TmFinishIteration wins by spending *less* — it skips iterations the last two durations say cannot
finish, banks the nodes for later moves, and almost never hits the hard limit. TmNodeShare loses while also
spending less; its soft-target swings apparently cost more than the saved nodes buy. T3 says the two switches
do not compose: alone they are +21.6 and −9.7, together exactly 0.0 over 1,000 games — and the only two
node-time forfeits of the whole job happened to the off side there (its longer games ran the clock dry twice).
T4 says the existing always-on stability/falling terms are already near the right dose: my extra scale spends
more time and loses a little.

## Part B: TmStability, the new switch (patch: `tmstability.patch.txt`)

Semantics (check, default false; off = not one decision changes, proven below). When on, the soft target of the
current move gets one extra multiplier from `tm_stability_thousandths` (new header
`include/forge/tm_stability.hpp`), composed of (a) best-move stability: 145 % when the best move just changed,
falling linearly to 65 % at 8+ stable iterations; (b) score trend: +25 % per 100 cp of score drop against the
previous iteration, drop capped at 200 cp; the product clamped to [50 %, 160 %]. Applied inside the existing
factor block in `Worker::go` next to the engine's own always-on stability and falling-eval terms.
Constants are my own first guess, chosen as a deliberately milder amplification of the terms the engine
already has (its own are 140/80/60 percent and +100 % per 100 cp); no tuning was done — the 1000-game match is
the measurement. Named tunables: `TmStabUnstablePct, TmStabStablePct, TmStabFallPer100, TmStabMinPct,
TmStabMaxPct` (in the `parameters()` table, so they are settable by spin).

Changed places by file and line (job-5 tree = base):
- `include/forge/tm_stability.hpp` — NEW: `tm_stability_thousandths`, constexpr, lines 1-43.
- `src/search.cpp`: +#include "forge/tm_stability.hpp" (line 5); tune defaults TmStability=false and the five
  constants (lines 110-116); five `parameters()` entries (lines 154-156); the application block guarded by
  `if (tune::TmStability)` (lines 2611-2622).
- `include/forge/search.hpp`: extern declarations (lines 309-315).
- `src/uci.cpp`: option line `option name TmStability type check default false` (line 235); parse branch
  (lines 441-444).

Proof off = old engine: bench 11/13/16 on the patched build = 312,866 / 862,329 / 3,024,920 nodes (the known
counts); 20 games at `NodeClock 100`, seed 7500, patched-with-switch-off against the unpatched job-5 build —
identical move for move (`staboff20.txt` == `base20_run1.txt`). Then T4 in the table.

## Files of the repository opened

search.cpp, search.hpp, uci.cpp, tm_finish.hpp, tm_node_share.hpp, clock_plan.hpp (all forge-combo29/; the
first three also patched in the TmStability tree), plus the job file and my job-5 report.

## Stamps

Job file read 21:30; base proof 21:30; T1+T2 launched 21:30:34, complete 21:47:43; TmStability patch written
21:36-21:40, built 21:31 (g++; the default c++ is clang and cannot link -lstdc++ here), off-identity proven
21:41; T3+T4 launched 21:47:51, complete 22:04; report written 21:48-22:10; all UTC 2026-11-15.

## What I did not do

- No tuning of the TmStability constants; the shipped values are the first guess, measured once.
- The hard-limit stop count is runner-side (≥ 95 % of the computed hard limit), because the engine does not log
  why a search stopped.
- T1/T2/T3/T4 used only seed 7501-7504; a second seed per switch would cost one more match each.
- The job-5 `TmFinishIteration` partial match (203 games at NodeClock 1000, 51.7 %) stays partial; this job's
  T1 supersedes it at the new scale.

## What I am not sure about

- Whether +21.6 Elo for TmFinishIteration transfers to NodeClock 1000 (10× longer games) or to the PC's real
  clock; the mechanism (banking doomed iterations) should, but that is a measurement, not an argument.
- The TmNodeShare loss (−9.7, interval touches +5): with one seed I would not swear it is real, though the
  sign agrees with its lower node spend.
- My paired-Elo interval assumes pair scores are independent and near-normal; 500 pairs makes the normal part
  harmless, independence is by construction (fresh `ucinewgame` each game).

## A better way

The engine already carries three always-on soft-limit factors plus two switched ones; they interact
multiplicatively and are only documented in code. One `TmModel` table (factor name, condition, multiplier,
on/off) printed in the `uci` answer would make every future clock experiment a one-line change and would have
prevented my job-5 misreading. Also: log the stop reason (`info string stop soft|hard|finishiteration`) so the
hard-stop count is exact instead of a 95 % reconstruction.

Model: Kimi K3.
