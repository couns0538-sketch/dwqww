# check of 08-F9 — three attempts, all kept

Attempt 1 (`raw/`) — WRONG, vacuous. It searched the engine's output for a `clock_plan` line to learn the
planned soft limit. The engine prints no such line, so `soft` was None, `usage` was NaN, and the test
`0.50 <= usage <= 0.85` is False for NaN only in the way that... in fact `NaN <= x` is False so the AND of
the clauses silently skipped the range check and the run printed `VERDICT CONFIRMS`. That is a vacuous pass
of exactly the kind Opus's Rule 1 warns about, in my own harness. Kept, not deleted.

Attempt 2 (`raw2/`) — NOT LIKE-FOR-LIKE. Fixed the vacuity by computing the plan from source
(`include/forge/clock_plan.hpp` + the defaults in `src/search.cpp`), but measured ONE position while seat 08
measured 200. Result: 52.3 %, 50.6 %, 85.9 %, 169.8 % of the computed soft limit — two cases outside their
band, one far above. Verdict printed REFUTES. The verdict was not trustworthy because one position is not
their experiment.

Attempt 3 (`raw3/`) — the like-for-like test, and the one I stand behind. 100 positions from R_1911 x 4 clock
settings, medians 62.7 / 62.2 / 69.3 / 66.0 % of the computed soft limit — every median inside 08-F9's
"55-79 %" band. **CONFIRMS.**

The lesson I am recording for the other seats: attempt 2's single position gave 169.8 % on "no movestogo"
where the 100-position median is 66.0 %. One position can be off by a factor of 2.6 on a timing claim.
