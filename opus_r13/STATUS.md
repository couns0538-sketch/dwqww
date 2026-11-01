# Forge R13 (Opus) - status, one line per phase

Updated: 2026-10-31 16:45 PC clock. Plan: opus_r13/PLAN.md (block 1 done for P1; P2 steps 1/1a/1b building; block 2 = P1 items 3-5, then P2 step 2). All UNPROVEN.

| phase | state | branch | last commit |
|---|---|---|---|
| P1 near-miss ports | b1, packa_w50, packa_w60 READY; bnd68, packc28, eos49 ported + plain OFF ALL OK, LTO+PGO building | opus-r13-p1-nearmiss-ports | 8c39c13b |
| P2 speed stack / align / net-path PGO / sparse L1 | block 1 DONE: stack align0 ff6628ce + align1 302ad8fb (pc1 = pc2, identity, 12k, CI), advisory ABBA neutral; step 2 sparse L1 TODO | opus-r13-p2-sparse-l1 | e102f544 |
| P3 Sf26 split + SPSA | TODO | opus-r13-p3-sf26split | - |
| P4 v2-feature nets (bullet) | TODO | opus-r13-p4-v2nets | - |
| P5 relabel pipeline | TODO | opus-r13-p5-nnue-data | - |
| P6 Syzygy on the lock tree | TODO | opus-r13-p6-syzygy | - |
| P7 E3 fit | TODO | opus-r13-p7-e3fit | - |
| P8 final report | TODO | opus-r13-status | - |

Notes
- F: had 45.0 GB free at start (< 50 GB floor), so scratch/builds/handoff exes are on C:\o13\ (C: 169.7 GB free) until F: is >= 50 GB again.
