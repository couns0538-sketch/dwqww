(Extracted unchanged by Opus on 28 Nov 2026 at 15:02 PC from the lab's PLAN.md, block PLAN-2811-OPUS-MONDAY-FOCUS. Data for Astra; the job file gives the orders.)

## PLAN-2811-OPUS-MONDAY-FOCUS (14:41 PC, 28 Nov, Opus)
OWNER (between 14:36 and 14:40:15 PC, word for word in LAB_RULES_FULL.md): on Monday all of us (Fable, Astra, Neon, Opus) focus on the fixes and ESPECIALLY on finding out how bad our filtering is, the top priority; the server day starts only when "those 3 things" (net fixes, search fixes, filtering) are very good, otherwise it is moved again.
- PROPOSED BARS for "very good" (Opus's PROPOSAL, to be agreed on Monday BEFORE the tests; games decide, as always):
  1. Search fixes: every fix behind an option (default = today), the three numbers and same_search hold; the bundle of the fixes wins SPRT [0, 10] at 250k (H1) against today's search; its 6+0.06 confirmation is not negative.
  2. Net fixes: skip-noisy placed (proven twice); the loop's next net passes net_sanity S1 (start position -10 to +60) and S2 (|start + after 1.e4| <= 40), or a net that fixes them wins its 250k test against r0067.
  3. Filtering: its faults measured with their sizes; a net trained on the improved filter beats a net trained on today's filter at 250k (SPRT [0, 10], H1), same recipe, same window size, same seed rules as R1.
- Monday roles (PROPOSAL): Fable reads (the skip-noisy package first, then the search patches behind options, then the filter changes); Neon builds and tests; Astra looks for where our filter is wrong (a prompt from Opus, FOR_THE_USER file 53, written after Neon's 18:00 table of today); Opus recounts every result from raw files, places by GO LIVE after Fable's YES, and tells the owner each result.
- The items of NEXT-2611-FABLE-MONDAY about the frozen package, file 46's votes and the server day WAIT until the three bars hold.
