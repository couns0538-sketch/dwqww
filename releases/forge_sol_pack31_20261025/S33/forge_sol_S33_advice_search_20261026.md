# ADVICE — search gate planning, 2026-10-26

Finish correctness, legal-move/state/TT tests and frozen input/build checks before
any strength gate. Compare one isolated change against its exact accepted parent.
The planner changes no engine option, tuning value or live gate.

At the assumed true+20 logistic Elo with G119's separate supplied pair shape,
[0,10]/1500 produces modeled P(H1)=0.91375 and P(cap)=0.08625. At true+10 the
same design produces P(H1)=0.21235 and P(cap)=0.78760. Thus1500 games often fail
to resolve a useful smaller effect. A cap is inconclusive, not a regression or
positive acceptance. Select bounds, cap, openings and stopping rule beforehand;
never pool capped attempts, reseeds or different concurrency.

For a future adequately resourced trial near the smaller modeled effect,
[0,10]/3000 is one design worth voting on: its G119-shape true+10 H1 forecast is
0.75895. This is advice about operating characteristics, not permission to alter
the current crew rule. Search changes may have a different pair profile; repeat
planning with their actual profile when available. Synthetic draw-ratio profiles
are sensitivity checks, not substitutes for missing real data.

Keep source correctness, speed and equal-clock Elo separate. A node reduction or
tactical screen cannot establish a gain. The analytic calculation is a Gaussian/
Brownian approximation; agreement with modeled trials does not establish native
Fastchess error rates. A clean independent confirm remains necessary. Native PC,
actual search candidate outcomes and Stockfish superiority are UNVERIFIED here.
