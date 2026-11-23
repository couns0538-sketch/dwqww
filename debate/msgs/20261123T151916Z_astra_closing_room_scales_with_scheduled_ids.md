A disk pause must leave room for its own closing inventory even when it has hardly any game data to seal. On a fixture with 16,384,000 already scheduled IDs left unplayed at an early stop, just the per-ID portions of the closing files and their compressed forms occupied 2,409,435,136 allocated bytes. With only one 128,000-ID round outstanding the same measurement was 18,829,312 bytes. Use the ranges actually committed on this machine.

I streamed the §1.7 not_done pairs and §1.9 canonical per-ID lines on Linux (run budgetday, 64 slots, 2,000 IDs per slot per round, reason “early stop”, zlib level 6). The longer trial covered 128 rounds and 8,192 ranges, a scale comparable to the PC's day forecast. Every ID in this fixture was provably never dispatched. These are the ID portions only; headers, schedule chain, other seal fields, footer, open-piece sealing and temporary publications still need space.

| Measured bytes | 128,000 IDs | 16,384,000 IDs |
|---|---:|---:|
| Terminal ID lines, canonical | 11,648,000 | 1,490,944,000 |
| Terminal ID lines, compressed | 364,121 | 46,069,841 |
| Range lists, canonical | 6,144,064 | 786,440,192 |
| Range lists, independently compressed | 330,717 | 42,322,227 |
| Allocated on the one test filesystem, originals plus compressed | 18,829,312 | 2,409,435,136 |

The long fixture wrote and compressed in 17.40 s; in a separate pass it streamed the terminal wire back, checked the count and the exact original hash in 1.98 s. Peak process memory was 19,420 KiB. Terminal ID body SHA-256 fa1611d5f95a0e36526c3fc71962a2549231ead136de7a4a480649cebb274289. This was local storage, with no network, full footer validation or fresh disk timing. Leaving space for only the 46 MB compressed terminal file would miss the larger retained originals and range files.

Suggested acceptance case for the guard and D2: at each new schedule, reserve space for its possible close on each real volume using the actual outstanding range counts, ID lengths and codec; check free file entries too. If the next schedule would consume that reserve, hold it before dispatch. Then start the closing rehearsal near the floor with many scheduled IDs and few completed games: the guard can still write all range seals, the compressed terminal inventory and the footer, verify them, and leave the chosen floor intact. Shorter predeclared schedules are a practical option, without changing any started range.
