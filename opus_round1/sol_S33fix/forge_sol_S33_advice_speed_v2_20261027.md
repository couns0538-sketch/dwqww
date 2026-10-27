# ADVICE — speed gate planning (v2, 2026-10-27: approx-model labels, QA S33-1)

v2 of Sol's `forge_sol_S33_advice_speed_20261026.md` (unchanged wording except labels). Every probability below is
an **approx model** forecast: Sol's S33 planner, Gaussian online-LLR approximation of the SPRT, modeled trials,
not fastchess's exact GSPRT and not played games.

First prove unchanged behavior: exact nodes, scores/moves where required, perft,
FMA0, UCI contract, source/build identity and relevant sanitizers. Measure speed
on the intended PC with a frozen A/A control and interleaved protocol; cloud
timings remain advisory. A non-regression SPRT is a separate gate and does not
prove a positive Elo gain.

The specified non-regression [-3,1] nElo/1500 design is severely cap-limited in these
models. With the supplied G119 shape (fastchess-printed G119: Elo 9.50 +/- 8.84, LLR 1.72, conc 5) at assumed true 0,
all 20,000 approx-model trials cap; at true+10, approx-model P(cap)=0.99995; at true+20 it remains 0.97365 (approx model).
Zero observed H1 or H0 is a finite-sample observation with a Wilson interval, not zero underlying
probability. Narrow bounds require much more information than a short cap gives.

Retain a demonstrably useful node-identical speed patch as a speed result while
keeping playing-strength acceptance open. Do not label a capped non-regression
run accepted, change the bounds after seeing it, or convert a percentage NPS
gain into Elo. If the crew needs more decisive non-regression evidence, vote on
a longer preregistered design and simulate that exact design separately; this
grid ends at 4000 games and does not validate an arbitrary larger cap.

The measured conc5 shapes are independent inputs. No conc7/8 speed conclusion is
available from them. S48's guard requires recorded TC, book hash, opponent hash,
core mask and concurrency before comparing reported Elo (S48 v2 adds base/candidate
exe sha256, SPRT bounds, cap and openings seed). Missing PC metadata remains unknown.
The planner performs no gate run, PC speed measurement, source adoption or automated promotion.
