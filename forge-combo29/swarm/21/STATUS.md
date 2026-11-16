## 2026-11-16T22:46:58Z (from `date -u`)
seat 21. Area 1 finished; now on **the PC's match path** (handoff file 6 item 3/4). **Threads 1 in
every run**, Hash 16, PC20 on the PC build unless stated.

**The find that matters now: 21-F16 — `go nodes N` never reaches N.**
10 real-game positions, Threads 1, PC20: mean undershoot **27.1 %** at N=20000, **28.0 %** at
50000, **20.4 %** at 250000; worst **−51.9 %** (−25,959 nodes); **not one of 30 pairs exceeded the
budget**. Fully deterministic (30/30 identical over 5 fresh processes each). Mechanism is in the raw
output: it stops at the last COMPLETED depth — position 1 at N=20000 finished depth 10 at 10,973
nodes and stopped. So a "250,000-node" match game is often a ~127,000-node game.
`job31/out/summary.md`, `job31/out/p1_n20000_r0_raw.txt`.

**21-C12 CONFIRMS the clock path is healthy**: 30 searches at `wtime 6000 btime 6000 winc 60 binc 60`,
slowest **599.5 ms**, every move legal.

**21-F15 (newer area)**: `go softnodes N` is fully deterministic (40/40) and stops at a depth
boundary, but OVERSHOOTS by up to +58.9 % — the opposite direction from `go nodes`. Both are "stop
at a finished depth" limits; one over-, one undershoots.

**Withdrawn under file 6** (3 claims of mine): 21-F9, 21-F13, 21-F11 — each caught by a rule I had
not applied before. Details in `job29/REPORT_job29.md` and FINDINGS.md.

**Still standing, ranked below the PC path**: 21-F8 (`fullmove 0` refused), 21-F2 (refused FEN →
`readyok` → old board).

**Unfinished**: job28 (seat 15's 15-F3, KNN v K) — killed mid-run, NO output, reported as not done.

**Next**: check whether 21-F16's undershoot costs strength — same positions at matched *effective*
node counts (e.g. N tuned so the completed depth matches a fixed depth), then a fixed-depth
comparison. That decides whether the owner should care.
