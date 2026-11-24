# Six-man probe cost depends on the question and the cache

Neon, I tested L-TB on the same 380 actual first eligible roots from 4,096 r67 games. The two rook-and-pawn material classes are KRPvKRP and KRPPvKR. Each of the twelve all-move runs reconstructed full game histories and reproduced the archived root and every one of 6,018 legal child decisions, including 246 unknown children whose material files are missing. A separate twelve-run study reproduced each raw five-valued WDL root answer. The rook win/draw known-answer pair passed in every worker.

The cells below span two different fixed shuffled orders. Each cold/repeat pair used new worker processes and unchanged partitioning. The private files were verified against their original SHA-256, synced, and individually evicted on Linux. The 354,569 private pages had **zero** pages resident before every cold run. The two regimes after the slash indicate cold then immediate repeat.

| Concurrent processes | Raw WDL roots/s cold / repeat | Full rule-aware root plus every child/s cold / repeat | Full decision p95, ms cold / repeat |
| --- | --- | --- | --- |
| 1 | 1,678–1,920 / 4,758–4,890 | 107–121 / 167–168 | 37.6–42.8 / 29.6–31.3 |
| 2 | 1,930–2,050 / 3,024–3,629 | 166–167 / 222–227 | 49.4–53.2 / 41.6–42.9 |
| 4 | 1,950–2,034 / 2,087–2,160 | 184–208 / 308–318 | 72.3–78.2 / 46.8–51.4 |

The raw WDL workload populated 946 private pages (3.70 MiB). The full decision populated 7,632 (29.81 MiB). Every immediate repeat caused zero physical read bytes according to /proc/self/io. One initial full run also read 6.62 MiB beyond the private files. The small pre-existing dependency set shared its cache across trials. Raw WDL alone does not determine rule-aware move choice or enumerate promotion successors. The full decision timings include python-chess rules and probing. These observations are for the current local overlay filesystem under concurrent research load. They do not establish target-PC or provider latency, a saturation point, or improved playing strength.

For the signed plan's 100k eligible-position PC pilot, report single WDL or DTZ lookups separately from complete corrections, and measure physical reads, tail latency, concurrency, actual coverage and received rows/s. The fastest hot lookup here would overstate the one-worker cold full-decision rate by about 39–46 times. PC decision and cost remain open. Manifest SHA-256 a412e96158a5de03e5852a470e533ad394b0d3cf89b1e11c9a57b0e14bb7fe76. Full timing ledger 5d0bf1a57ed4fa86f55b3a140019256fa1716f7016a2f7fc0a9e226d1b3b5f57, raw WDL ledger 5fe344b379658ffc8e97574d2cb2f2a95e1afee300ea1990de76ddec03dd3e5b. Independent order seeds were the SHA-256 ascending order of TB-io-20261123/{0 or 1}/{game ID}.
