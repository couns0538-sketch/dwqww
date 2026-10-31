# Forge R13 (Opus) - status, one line per phase

Updated: 2026-10-31 (PC clock ~16:40). Plan: opus_r13/PLAN.md (block 1 = P1 items 1-2 + P2 steps 1/1a/1b). All results UNPROVEN (no gate).

| phase | state | branch | last commit |
|---|---|---|---|
| P1 near-miss ports | block 1 DONE: b1 READY (exe e950c77e), packa_w50 + packa_w60 READY (exe 07cc2393); items 3-5 TODO (next plan) | opus-r13-p1-nearmiss-ports | 5cfba947 |
| P2 speed stack / align / net-path PGO / sparse L1 | STARTING step 1 (stack: r10fix1 + S1 LargePages, w21pt recipe) | opus-r13-p2-sparse-l1 | - |
| P3 Sf26 split + SPSA | TODO | opus-r13-p3-sf26split | - |
| P4 v2-feature nets (bullet) | TODO | opus-r13-p4-v2nets | - |
| P5 relabel pipeline | TODO | opus-r13-p5-nnue-data | - |
| P6 Syzygy on the lock tree | TODO | opus-r13-p6-syzygy | - |
| P7 E3 fit | TODO | opus-r13-p7-e3fit | - |
| P8 final report | TODO | opus-r13-status | - |

Notes
- F: had 45.0 GB free at start (< 50 GB floor), so scratch/builds/handoff exes are on C:\o13\ (C: 169.7 GB free) until F: is >= 50 GB again.
