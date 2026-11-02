# Forge R13 (Opus) - status, one line per phase

Updated: 2026-11-01 11:00 PC clock. CR R13: P3 PASS, P6 PASS, P4 + P7 FIX (fixes pushed, runs in progress). All UNPROVEN.

| phase | state | branch | last commit |
|---|---|---|---|
| P1 near-miss ports | DONE: all 5 items READY (b1, packa_w50, packa_w60, bnd68, packc28, eos49) | opus-r13-p1-nearmiss-ports | 759acc6d |
| P2 speed stack / align / net-path PGO / sparse L1 | DONE for now: stack align0 ff6628ce, align1 302ad8fb (neutral), sparse stks 6fdf46dc exact but SLOWER (stopped); steps 5/5a TODO | opus-r13-p2-sparse-l1 | a9d14902 |
| P3 Sf26 split + SPSA | DONE, CR PASS: exe 029d58e8, 3 single lines (queued as gates) + combined; SPSA bits 2/4 noise-level | opus-r13-p3-sf26split | fe841cb4 |
| P4 v2-feature nets (bullet) | CR FIX done (parity fails on mismatch, bullet padding, licence table); trainer compiles (mock backend); random-net parity running; GPU window needed | opus-r13-p4-v2nets | e23fca30 |
| P5 relabel pipeline | tools staged (relabel_job.py: sharded/resumable Windows driver around Astra relabel_positions), run after the SPSA | opus-r13-p5-nnue-data | - |
| P6 Syzygy on the lock tree | CR PASS (port); build + checks next | opus-r13-p6-syzygy | c860d3b8 |
| P7 E3 fit | CR FIX done (raw_eval compiles on d4f4312, loud failures, bootstrap CIs, dedupe); fit running | opus-r13-p7-e3fit | cad3fe13 |
| P8 final report | checkpoint 2 (FINAL_REPORT.md), updated as work lands | opus-r13-status | - |

Notes
- F: had 45.0 GB free at start (< 50 GB floor), so scratch/builds/handoff exes are on C:\o13\ (C: 169.7 GB free) until F: is >= 50 GB again.

## Final state (2026-11-01 ~11:20 PC clock, usage ending)
- P1 DONE: 6 gate lines (b1 e950c77e, packa w50/w60 07cc2393, bnd68 8dc93b38, packc28 cf617e67, eos49 a4e7f24c).
- P2 DONE for now: stack ff6628ce / align 302ad8fb (neutral); sparse L1 6fdf46dc exact but slower (stopped).
- P3 DONE (CR PASS): exe 029d58e8, singles queued; SPSA noise-level.
- P4: CR fixes pushed; parity PASS at H256 (a/b/c x AVX2/SSE 10000/10000); needs a GPU window; H768+ open.
- P5: relabel job running on the PC until 12:25 (job C:\o13\p5\job1); throughput + handoff TODO.
- P6: OFF pins, ON bench = original prober pins, WDL/DTZ 220/220, 50-move 20/20; LTO+PGO pc1/pc2 + CI sanitizer were running.
- P7 DONE: EvalRule50Damp 60 (fitted) beats OFF and hand; Optimism 150 weak; MatScale fits 0.
