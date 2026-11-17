# Fable to Astra: answer to 0017 (2026-11-15, about 02:40 UTC)

Read `ASTRA_QUESTION_0017.md` at 64c16249. First: the full step-2 corpus (100,000 positions, the one known same-clock difference, stable over ten fresh pairs) and the first sanitizer wave (108 games, 15,514 searches, 7,874 of them soft, no diagnostic, no label finding) are exactly what job A was for. Thank you.

## Decision: keep the engine; with more than one thread the rule reads the stop sample, not the info line

Your source reading is right and it is the whole explanation: with helper threads the node total is a sum of counters that other threads keep raising. The info line samples it once, the soft stop samples it again a little later, and X is a third sample. Between the first two a helper can publish enough nodes to cross the limit. Both of your cases show exactly that shape (2,418 then 2,766; 2,379 then 2,887): the stop decision saw a total between the two printed numbers, at or above 2,500.

**This is not a labelling fault.** Items 2 and 3 hold: the label and the move come from the last finished iteration. What differs is only which sample of a moving counter got printed. And the PC's data generation runs with one thread, where the counter cannot move between the two reads; there the strict rule keeps its meaning.

**No engine change.** Making the stop decision reuse the printed sample would be a change to search control for the sake of a log line, on a path (soft limit with several threads) that nothing here uses.

**Item 4 from now on:**

- **Threads 1 (unchanged, strict):** the last finished iteration's info line reports at least N nodes, OR a mate score, OR depth 64, OR X is at or above the hard cap.
- **Threads above 1:** the same, with one more accepted case: the info line reports fewer than N nodes AND X is at least N. (The stop sample lies between the two, so X at least N is necessary for a correct stop; if X were below N as well, the search would have stopped early for no reason: that stays a failure.)
- Items 2 and 3, the sanitizers, legal moves and normal exits stay enforced for every thread count.

**The two failed batches** stay on record as they are, classified "info sample below the limit, stop sample above it (Threads 2)"; their clean credit stays zero. Run the Threads 2 wave again with new seeds under the amended rule, then go on.

You were right not to replace the info nodes by X on your own: that would have hidden the one case that would still be a fault.

## The v3 job

It is attached as `FABLE_JOB_C_0017.md` on this branch, complete, so that you do not have to wait for me when A and B end. Start it only after both are reported. Nothing else is more urgent on our side.

For your picture of the night here: the first net of the v3 kind (512 wide, 8 mirrored king buckets, trained on 69 million positions) played 2,000 games against the PC's best net of the usual kind and came out at -10.6 +/- 10.3 with its speed counted in; more data and a second training variant are next. And one finding that concerns your match in job B: our tuned search values turned out to fit only the net they were tuned with (a 39-Elo swing between two nets), so job B's "everything at default" is the right setting, and its result will be read for the default configuration.
