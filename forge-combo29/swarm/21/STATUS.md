## 2026-11-17T00:21:04Z (from `date -u`)
seat 21. **Threads 1 in every run.** PC build r15 under PC20 unless stated.

**Delivered this stretch**
1. **`METHOD_playout_trap.md`** — the standalone page the coordinator asked for (finding 21-F20): one
   engine-vs-engine play-out manufactures hits at a knife-edge fifty-move counter. Contains the
   reproduction (`8/8/8/8/8/1r1k2K1/8/8 b - - 92 60`: `d3e3` reads as a WIN 3/3 by play-out, yet no
   move forces mate), the exact window method (counter c → only 100−c half-moves, so a bounded minimax
   is exact), the three errors I made in that work, and a 5-point checklist. FINDINGS 21-F20 now points
   at it.
2. **`DESIGN_drawn_root.md`** kept as a design note, not a patch, as instructed.

**NEW: 21-F22 — bare-king endgames explode at depth 13.**
192–211 **million** nodes and 24–30 s in bare-king endings, where a middlegame at the same depth costs
53k–173k (a **1,000–2,700×** difference), with a **108×** jump from depth 12 to depth 13. Reproduces on
the BASE build and the PC build under PC20 — **pre-existing in the shared search, not a PC regression**.

**21-C18 — the clock protects it.** Same positions with `wtime 6000 btime 6000 winc 60 binc 60`: 258–
1,586 ms, no timeouts, on both builds. So matches and clocked self-play are safe; the exposure is any
job that sends `go depth 13`+. My own job40 harness hit this and looked like an engine hang until I
measured it.

**Job40 status: NOT DONE.** The wide-window (counter 85–94) exact scan is still open: its first run hit
the 500 s wall with no output, its second died on the 21-F22 explosion inside `go depth 16`. Both are
recorded in `job40/stamps.txt`; no count is claimed.

**Next**: retry the wide window with the engine search replaced by a node budget (`go nodes`) so the
21-F22 explosion cannot poison it, and with the solver capped so undecided moves stay UNDECIDED.
