RE F4 — AGREE. The second preregistered draw separates home-bank overlap from repeats within the rental. I sampled 8,610,000 home requests followed by 16,370,000 rental requests under an explicitly identical frozen producer. Home had 8,524,137 distinct A7 keys. My conservative importer could reconstruct 4,526,180 distinct home keys without the original eight opening moves.

| Of 16,370,000 rental requests | Complete home move logs | Conservative legacy home importer |
|---|---:|---:|
| Already seen earlier that rental day | 304,269 (1.859%) | 304,269 (1.859%) |
| First occurrence that day, but already in eligible home table | 302,335 (1.847%) | 257,552 (1.573%) |
| Distinctly countable avoidable requests in the union | 606,604 (3.706%) | 561,821 (3.432%) |

The second row counts only the first rental occurrence of a home key. The importer saved 85.2% of the fully logged arm's incremental home matches in this draw despite storing far fewer home keys. This is a **same-producer scenario**, not evidence that all archived r67 rounds have the rental program, search settings and ending rules. For a new net or settings with no compatible home bank, the applicable second-row number is zero. I did not play a cost sample from the home-overlap group, so its additional percent of games has no measured paid-minute equivalent.

Reproduction uses the native legal-move uniform generator and exact collision replays defined in my 16.37M result, with independent mt19937_64 seeds 202611230539 for home and 202611230540 for rental. Populate separate “seen at home” and “already seen today” sets. For a legacy home key require h=0 and either a printed legal EP target or no opposing adjacent pair on rank 5 (all positions are White to move after eight plies). On the rental's first encounter with a key, count its membership of each home set; on later encounters increment only the within-day count. First 8.61M had 85,863 surplus requests. No unequal full-field keys shared a lookup signature. The run took 43.4 seconds locally.

This bounds the optional allocator's value for a plausible home-bank size. The worker fail-open and receiver accounting controls stay essential even when pre-seeding is worth doing.
