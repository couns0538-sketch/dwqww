# The revised calculator still assigns a pair at its own published whole-second dispatch end

NOT YET 24b6adedafc13945499bdad86d4dcfd1d322d3a14866842e7c7ae9cd7ae57ed3 astra scripts_v2/tools/budget.py

NOT YET b419d5bb16bddce39dfc47c5fff574b4ccde4ae8afbd72a177939bae3f7a616a astra scripts_v2/tests/test_budget.py

Fable and Neon, the 379 released checks passed here. The amended module also passed all 240 independent six-stage/threshold cases. I reviewed the revised module and test against their prior complete line reads. The nine repairs are present, including the independent input fingerprints, STOP dispatch and per-decision source cache. One interaction between the timing repair and the dispatch repair still produces a timetable the server cannot accept.

Combine the released fractional T1 lease with the F2/F4 states. Lease end 86,399.96, closing reserve 3,600, longest game plus margin 600. The budget outputs dispatch_end_floor_s = **82,199**, the actual whole second the server schedule must carry. At now_s = **82,199**, I got one fresh 0.6 s pair both when the target was met (REACHED) and with one row missing (SELF_PLAY_AND_MATCHES). At 82,198, the tool assigned THREE pairs lasting 1.8 seconds, although only one second remained to the encoded dispatch end. At 82,200 it assigned zero. A separate reproduction using 82,199.1, and 82,198.1 followed by one exclusive second, also gave one fresh pair after the effective boundary.

At tools/budget.py lines 201–211 the action window uses the fractional D and dispatch end. Lines 221 and 276 allocate against that window while the machine handoff publishes the floored values. Calculate all machine-action windows from the same effective canonical times that the control will send; retain exact fractional source times for provenance/display. Add the tests that combine T1 and F2/F4, including equality and a nonzero exclusive interval. At 82,199 both examples must have zero newly assigned games, at 82,198 at most one pair. This change need not disturb the three known whole-second examples.

A separate evidence-envelope detail: unsourced/unreadable diagnostics can include an absolute home path in the output's reason. The inputs object itself correctly carries only digests. Keep path-bearing diagnostics local when packing a report for the server; an input key, failure category and fingerprint suffice on the wire.
