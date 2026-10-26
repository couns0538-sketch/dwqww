# ADVICE — speed gate planning, 2026-10-26

First prove unchanged behavior: exact nodes, scores/moves where required, perft,
FMA0, UCI contract, source/build identity and relevant sanitizers. Measure speed
on the intended PC with a frozen A/A control and interleaved protocol; cloud
timings remain advisory. A non-regression SPRT is a separate gate and does not
prove a positive Elo gain.

The specified non-regression[-3,1]nElo/1500 design is severely cap-limited in these
models. With the supplied G119 shape at assumed true0, all20,000 trials cap; at
true+10, modeled P(cap)=0.99995; at true+20 it remains0.97365. Zero observed H1 or
H0 is a finite-sample observation with a Wilson interval, not zero underlying
probability. Narrow bounds require much more information than a short cap gives.

Retain a demonstrably useful node-identical speed patch as a speed result while
keeping playing-strength acceptance open. Do not label a capped non-regression
run accepted, change the bounds after seeing it, or convert a percentage NPS
gain into Elo. If the crew needs more decisive non-regression evidence, vote on
a longer preregistered design and simulate that exact design separately; this
grid ends at4000 games and does not validate an arbitrary larger cap.

The measured conc5 shapes are independent inputs. No conc7/8 speed conclusion is
available from them. S48's guard requires recorded TC, book hash, opponent hash,
core mask and concurrency before comparing reported Elo. Missing PC metadata
remains unknown. The planner performs no gate run, PC speed measurement, source
adoption or automated promotion.
