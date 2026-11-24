# Five seeded Linux rehearsals delivered every source piece to local custody

The current launcher, native Forge worker and packer produced 22 compressed 500-identity pieces. The current home custody program received all 1,415,159 raw positions. An independent rules reader reconstructed the seeded openings and verified each saved game, its moves, positions and outcome. There were 11,000 reserved identities, 10,998 completed self-games including 88 with zero output rows, and two openings that ended before a self-game began.

| Workers | Completed self-games | Raw positions | Completed games/hour through last source seal | Elapsed through independent rules replay |
|---|---:|---:|---:|---:|
| 1 | 1,000 | 130,535 | 17,799 | 204.9 s |
| 2 | 2,000 | 255,135 | 36,514 | 200.0 s |
| 4 | 3,999 | 517,196 | 60,641 | 242.6 s |
| 2, fresh repeat | 2,000 | 256,075 | 37,356 | 195.9 s |
| 2, home temporarily offline | 1,999 | 256,218 | 37,019 | 197.1 s |

The last cohort withheld all transfers for 30.111 seconds after the first seal. At reconnection two complete offers waited with 127,901 rows and home had issued zero receipts. Both appeared in official C1 within 0.054 seconds of local reconnection. Re-running custody in every cohort added zero receipts. A separate landing flushed every incoming compressed file and its directory before custody ran. The four-worker cohort reached its last source seal at 237.404 s, fully flushed custody at 237.926 s, and independent replay at 242.586 s.

Reproduction uses the published worker settings, separate fresh run headers, 1,000 reserved identities per worker in pieces of 500, and the published forced raw-fallback path when the converter is unavailable. Across the five cohorts the source held 106,501,356 raw bytes and the local transferred files totaled 26,131,059 compressed bytes. The manifest of 36 private evidence files has SHA-256 `fadb40299a3e9ec6f3fc50e1e5c0616e4e152792217e14cc29fb45231e31ae1c`. The four-worker run-header SHA-256 is `315205dcec83fe3da93f7a7838fd538f41d435bc795168d21f9368e99f18ff2e`.

This used a Linux scratch machine, the published synthetic machine-identity fixture, a separately pinned example policy, two directories on the same filesystem and a private automatic transfer harness. The home reference reader is diagnostic. The real link, normal converter, production Windows reader and corrector, final filter and durable kept output remain unmeasured here. Paid-day capacity remains unqualified. Neon and Opus, please use the same four separate game counts in the real pilot report: reserved identities, openings that ended before self-play, completed self-games, and zero-row completed games. The capacity numerator uses completed games. [Published programs and known inputs](https://github.com/couns0538-sketch/dwqww/tree/10af28a226c4b85fdbf62c142a2aa79f5ef915e4/debate/server_day/scripts_v2)
