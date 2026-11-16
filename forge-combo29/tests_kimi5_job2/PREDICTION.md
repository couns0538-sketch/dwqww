# kimi5 job 2, Part 1: BLIND PREDICTION (pushed before any measuring command ran)

First line honesty: I have NOT opened `REPORT_glmflash5_job2.md` and NOT opened anything in
`tests_glmflash5_job2/`. I read `NOTES_glmflash5.md` (allowed) at 04:51Z; it contains no
TmFinishIteration/TmNodeShare results. I read `NOTES_deepseek5.md` and the job-1 numbers of
glmflash5 (HindsightDepth/SoundMatePruning only, unrelated). This prediction rests on the
source of 6b98f217 only: clock_plan.hpp:32-50, search.cpp:2110-2120, 2184-2198, 2555-2626,
include/forge/tm_finish.hpp:26-37, include/forge/tm_node_share.hpp:33-67, uci.cpp:233-234.

Stamps: run start 2026-11-16T04:48:19Z (trigger); this file written 2026-11-16T04:56Z (`date -u`).

Planned defaults, Move Overhead 10, no movestogo (soft = (T-10)/22 + 0.75*I, hard = min(0.6*(T-10), 5*soft)):
- 10+0.1 (T=10000, I=100): soft 529 ms, hard 2645 ms.
- 1+0.01 (T=1000, I=10):  soft 52 ms,  hard 260 ms.

Default stop rule (both OFF): after each finished iteration, stop when
elapsed >= soft * factor, factor = stability(0.60/0.80/1.0/1.40) * clamp(1.55-share_all, 0.6, 1.4)
* falling-eval, floored at 0.45. Time is spent in WHOLE iterations: the search only stops at
iteration boundaries (soft) or by poll (hard). So the default routinely ends one iteration
PAST the soft deadline, and that last iteration is complete and its move is used.

## TmFinishIteration (alone vs default)

Mechanism read: after the factor-stop check passes (search would continue), estimate the next
iteration's duration from the last two sampled iteration durations (spike rule: if last > 2*prev
use sqrt(last*prev), else last^2/prev); if the estimate exceeds the remaining soft budget
(deadline - elapsed), stop now and keep the last finished iteration's move
(tm_finish.hpp:26-37, search.cpp:2612-2625). Sampling needs two finished iterations, and runs
only in clock play (search.cpp:2394-2398).

(a) Time per move as a factor of default's — EARLIER only, never later. The hold skips the one
iteration that would have crossed the deadline; at growth ~1.5-2x per iteration that skipped
iteration is roughly 40-60% of the search's total time, but part of it sits below the deadline
the default also crosses, so the net save is smaller.
- 10+0.1: moves 1-20: 0.65; moves 21-40: 0.65; moves 41+: 0.70. Phase barely matters: the save
  is one iteration at any depth; late endgames grow a bit slower, so the skipped iteration is a
  slightly smaller share.
- 1+0.01: moves 1-20: 0.70; moves 21-40: 0.75; moves 41+: 0.90. Durations are ms-quantized
  (1-15 ms), the estimate is noisier, and with budgets of a few ms many searches end before two
  sampled iterations exist, so no hold can fire.
(b) Share of searches that change the stop decision: ~70% at 10+0.1, ~55% at 1+0.01 (a hold can
fire only when the boundary factor-stop did not already stop the search and two samples exist).
(c) Elo: 10+0.1: +0 to +10, center +4. The ~35% per-move saving compounds over a game into
usable time (worth about as much as the one iteration of depth it costs on held moves, ~15-20
Elo each way), with a small extra gain from never finishing a move deep past the planned soft.
1+0.01: -10 to +5, center -3: same trade, but one iteration at depth ~9 is a bigger relative
loss, and quantized durations make last^2/prev fire on noise. NEGATIVE when: growth slows with
depth so last^2/prev overestimates and the hold skips iterations that WOULD have finished in
budget — pure depth loss — and when a tactical move is found exactly by the skipped iteration.
(d) Prove me wrong with ONE measurement: median engine-`time` factor ON/OFF over the 300 UHO
positions at (T,I) = (10000,100). Predicted inside [0.50, 0.80]; anything outside kills (a),
and if the mean last-finished-depth drop is not between 0.5 and 1.5, the mechanism I read is
not what runs.

## TmNodeShare (alone vs default)

Mechanism read: the effort piece of the factor is pinned to 1.0; instead the soft target itself
is rescaled linearly in the best root move's share of ROOT-counted nodes:
soft' = clamp(soft * (1.5 - share_root), 1 ms, hard) (tm_node_share.hpp:33-55,
search.cpp:2576-2578, 2591-2611). Default's curve is clamp(1.55 - share_all, 0.6, 1.4)
multiplying AFTER the stability factor. Two real differences: the pivot drops from 55% to 50%
(ON's line sits ~0.05 BELOW default's inside the clamps), and the range widens from [0.6, 1.4]
to [0.5, 1.5]. Multiplication commutes, so pre/post scaling is not itself a difference.

(a) Both earlier and later, but EARLIER in the large majority. For the same share s inside the
clamps ON's deadline is default's minus ~0.05*soft (slightly earlier); earlier by much more when
one move holds >95% of root nodes (floor 0.5 vs 0.6: forced moves, only recaptures); LATER only
when the best move holds <15% (cap 1.5 vs 1.4: genuinely split positions).
- 10+0.1: moves 1-20: 0.95 (opening shares 30-50%: just the pivot shift); moves 21-40: 0.95;
  moves 41+: 0.92 (more dominant-move positions). 
- 1+0.01: 0.95-1.00 everywhere: deadlines are whole iterations of 2-15 ms, so a 5% shift often
  lands inside the same iteration count and changes nothing; measured factors lumpy.
(b) Share of searches that change the stop decision: the deadline moves in nearly every search
(share is rarely exactly 55%), but the stop changes only when the shift crosses an iteration
boundary: ~30% at 10+0.1, ~20% at 1+0.01. Bestmove changes: ~5-12% of searches.
(c) Elo: 10+0.1: -3 to +3, center 0. Taking time from dominant (usually obvious) moves and
giving it to split (usually hard) positions is the right direction, but the 0.05 pivot drop is a
~5% self time-odds everywhere, which costs about as much as the redirection gains. 1+0.01:
-4 to +4, center 0, quantization makes most shifts no-ops. NEGATIVE when: split positions are
disproportionately already-lost ones where the extra 1.5x time is wasted, or the pivot drop's
uniform thrift simply plays at 0.95x time odds with no compensating gain.
(d) Prove me wrong with ONE measurement: median engine-`time` factor ON/OFF at (10000,100)
outside [0.85, 1.05], or `info string TmNodeShare` lines in the raw output that are not a
mixture of lengthen and shorten with shorten the majority.

## Bench prediction (checked in Part 2)

Both options are clock-play only (sampling and rescale are gated by time_managed_,
search.cpp:2394-2398, 2586-2590; a bench has no clock). bench 11 with either switch ON must be
exactly 312866. If it moves, the switch touches more than the clock.
