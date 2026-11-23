RE A1 — AGREE. Cover drawadj, matescore and evallimit, and compare emitted game-relative ply. I checked `source/src/uci.cpp:457,518–552`: a FEN with a nonzero fullmove counter can start with selfgame ply zero.

RE A2 — AGREE. Require a mixing check as well as exact row coverage. Predeclare the intended reference shuffle on a fixed round-labelled fixture, compare batch-level round mixes across fixed seeds and include a chronological-reader negative control. Measure actual compressed size and decode throughput before assuming any encoding fits both budgets.

RE A3 — AGREE. Use immutable, checksummed raw chunks and versioned keep flags when the received raw stream fits the measured transfer and storage budgets. Count only eligible delivered rows toward the goal. This preserves the ability to compare filters on the same games. I checked the distinction between the 32 MB game records and 289 MB packed text in `debate/PLAN.md:155–160`.
