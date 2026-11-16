## 2026-11-16T22:08Z — checkpoint
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21

**New results since 21:56**
- job8 (area 1 job 2 again, SEED 2111 values): 29 cases; every halfmove value ≥ 100 accepted
  and answering `score cp 0 nodes 0` (100, 150, 9999, 65535, 65536, 91102, 128221, 98147,
  119640, 161959, 2^31); fullmove 0 refused again; ep_e0/e3/e6 refused; 0 perft mismatches;
  0 crashes; 0 sanitizer lines. All 9 predictions held.
- **21-F9 strengthened**: a mate in 1 at halfmove 100 is MISSED by `go depth 5`, `go nodes 100`
  AND `go movetime 50`, in BOTH colours; the same boards at counter 99 find it by all three.
  `job8/out/summary.md`, run by `job8/mate100.py`.
- Harness bug found and fixed in this job: an illegal black-side FEN (`…4r1K1 b`) was refused
  and the searches silently ran on the stale startpos board. Every case now asserts the FEN
  was accepted before any search answer is trusted. Worth telling the other seats.

**Findings**: 21-F1..F10, 21-C1 (CONFIRMS 30-F6), 21-C2. 21-F9 rewritten with the mate control.

**Next**: check the newest unconfirmed finding from another seat (cycle 2a), then area 1 job 3
again with the seed-2111 game.
Next command: `cd forge-combo29/swarm/21 && bash board.sh`
