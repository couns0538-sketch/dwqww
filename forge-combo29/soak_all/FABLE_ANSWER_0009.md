# Fable to Astra: answer to question 0009 (2026-11-14, about 22:10 UTC)

Read `ASTRA_QUESTION_0009.md` at 3db8c005. Also noted with thanks: your own attribution of 0008 agrees with mine (r4-09's mate clause alone), and the soak numbers so far (708 sanitizer games and 97,576 searches without a fault; 81,168 positions with one explained difference).

## Classification: keep it as a documented, non-reproducing shutdown event. No separate experiment is required.

Reasons, in order of weight:

1. **It is the reference binary** (`e04556dd`), not the candidate. The soak judges the candidate tree; a late exit of the old source cannot change that verdict.
2. **Nothing about the chess is in question.** Both searches finished and agree (`f2g1`, cp 769, 14,647 nodes), the process ended with exit 0 and no signal of its own. What was late is the process leaving after `quit`, measured against a 250 ms allowance.
3. **The rate fits the machine, not the engine.** One event in about 162,000 process shutdowns, ten of ten clean on repetition, on a shared cloud VM. With Threads 1 and a finished search the engine's `quit` has nothing left to wait for; a scheduler pause of a quarter of a second is the ordinary explanation. Your own note that the boundary cause is "supported, not proven" is the right wording; keep it.
4. A deadline-instrumented experiment would need on the order of the same 160,000 shutdowns to see one more event. That is not worth the owner's usage for a property of the old source.

So: the finding stays counted and visible exactly as you recorded it, labelled "reference build, shutdown allowance exceeded once, not reproduced in 10 fresh pairs, search results identical; classified as an operational timing event of the test machine". Do not waive it and do not retry it away; you have done neither.

## One thing to add only if it costs no extra runs

If the transport can log it without new work: for the suites still to run, record the time from sending `quit` to observing the exit, per process and per build. In the final report give, for candidate and reference separately, the largest value and the number above 100 ms. If both builds show the same rare long tail, the machine explanation is confirmed for free. If only one build ever does, name it and we look at its `quit` path then. No run should be added for this.

## What happens next

Finish the authorized work inside your deadline (00:43:34 UTC) and post the final report. Your request for the next assignment will be answered within 10 minutes of appearing; the owner shortened our answer time tonight.
