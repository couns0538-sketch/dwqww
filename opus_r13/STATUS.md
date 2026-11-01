# Forge R13 (Opus) - status, one line per phase

Updated: 2026-10-31 16:45 PC clock. Plan: opus_r13/PLAN.md (block 1 done for P1; P2 steps 1/1a/1b building; block 2 = P1 items 3-5, then P2 step 2). All UNPROVEN.

| phase | state | branch | last commit |
|---|---|---|---|
| P1 near-miss ports | DONE: all 5 items READY (b1, packa_w50, packa_w60, bnd68, packc28, eos49) | opus-r13-p1-nearmiss-ports | 759acc6d |
| P2 speed stack / align / net-path PGO / sparse L1 | DONE for now: stack align0 ff6628ce, align1 302ad8fb (neutral), sparse stks 6fdf46dc exact but SLOWER (stopped); steps 5/5a TODO | opus-r13-p2-sparse-l1 | a9d14902 |
| P3 Sf26 split + SPSA | split READY (exe 029d58e8, 3 single lines + combined); SPSA bits 2/4 running (160 pairs each) | opus-r13-p3-sf26split | 1aaf00bd |
| P4 v2-feature nets (bullet) | TODO | opus-r13-p4-v2nets | - |
| P5 relabel pipeline | TODO | opus-r13-p5-nnue-data | - |
| P6 Syzygy on the lock tree | TODO | opus-r13-p6-syzygy | - |
| P7 E3 fit | TODO | opus-r13-p7-e3fit | - |
| P8 final report | checkpoint 2 (FINAL_REPORT.md), updated as work lands | opus-r13-status | - |

Notes
- F: had 45.0 GB free at start (< 50 GB floor), so scratch/builds/handoff exes are on C:\o13\ (C: 169.7 GB free) until F: is >= 50 GB again.
