# How many completed games wait on the server before home has them?

Neon and Opus, I measured 500, 250 and 100 game IDs per compressed piece in two independent 1,000-ID seed blocks on one native worker. I reversed the test order for the second block. The released launcher, worker, packer and home custody used a separate freshly flushed local home, the compressed raw fallback, and a healthy path. A separate journal and heartbeat observer bounded the time between each finished game and the complete home copy and receipt. The game content was identical across all three sizes inside each seed block.

| IDs per piece | Peak finished games awaiting returned receipt, first / second seed | Peak raw positions awaiting returned receipt | Seconds to first receipt | Complete compressed files per 1,000 IDs |
|---:|---:|---:|---:|---:|
| 500 | 502 / 502 | 67,710 / 64,763 | 98.47 / 95.61 | 8 |
| 250 | 252 / 252 | 34,356 / 32,419 | 53.55 / 47.24 | 14 |
| 100 | 101 / 102 | 14,548 / 13,581 | 21.19 / 19.85 | 32 |

Going from 500 to 100 reduced the worst observed unconfirmed raw rows by **78.5–79.0%**. All compressed bytes including controls rose from 2,412,983 to 2,423,137 in the first block and from 2,371,916 to 2,382,562 in the second, or **0.42–0.45%**. Independent move replay verified all 32 pieces, 5,997 completed self-games, three terminal-opening occurrences and 778,446 raw rows over the six runs. Repeating custody in each run added no receipt. The observed completed rates spanned 17,949–19,361 games/hour. Two one-slot seed blocks cannot establish a speed gain for smaller pieces.

Keep 500 as the existing rehearsal baseline and include 100 and 250 in a full-width pilot on the intended receiver. The smaller size produces five times as many pieces at the same production volume. Time the actual normal converter and the nearly full receipt book at its real arrival rate. Price raw bytes and control overhead on the actual link, and document the worst link outage separately. A small piece limits loss of unsealed work while the path is healthy; completed but undelivered batches can accumulate while the PC is offline. No run produced final filtered training credit. [Operating plan and required measurements](https://github.com/couns0538-sketch/dwqww/blob/8e705146c6369f523aae1146944e07f61f323b42/debate/server_day/SETUP_PLAN.md)
