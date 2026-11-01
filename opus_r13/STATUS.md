# Forge R13 (Opus) - status, one line per phase

Updated: 2026-11-01 09:37 PC clock. Plan blocks 1-4 in opus_r13/PLAN.md. All results UNPROVEN (no gate).

| phase | state | branch | last commit |
|---|---|---|---|
| P1 near-miss ports | DONE: all 5 items READY (b1, packa_w50, packa_w60, bnd68, packc28, eos49) | opus-r13-p1-nearmiss-ports | 759acc6d |
| P2 speed stack / align / net-path PGO / sparse L1 | DONE for now: stack align0 ff6628ce, align1 302ad8fb (neutral), sparse stks 6fdf46dc exact but SLOWER (stopped); steps 5/5a TODO | opus-r13-p2-sparse-l1 | a9d14902 |
| P3 Sf26 split + SPSA | split READY (exe 029d58e8, 3 single lines + combined); SPSA bits 2/4 running (160 pairs each) | opus-r13-p3-sf26split | 1aaf00bd |
| P4 v2-feature nets (bullet) | IN PROGRESS: trainer/exporter/harness/reference written (da68b43c), build + parity next | opus-r13-p4-v2nets | da68b43c |
| P5 relabel pipeline | tools staged (relabel_job.py: sharded/resumable Windows driver around Astra relabel_positions), run after the SPSA | opus-r13-p5-nnue-data | - |
| P6 Syzygy on the lock tree | port script applied cleanly (+1796 lines), patch pushed; build + checks after the SPSA | opus-r13-p6-syzygy | c860d3b8 |
| P7 E3 fit | tools written (raw eval harness, PGN extractor, fitter); no E3 gate is H0 yet; run after the SPSA | opus-r13-p7-e3fit | 7d81f367 |
| P8 final report | checkpoint 2 (FINAL_REPORT.md), updated as work lands | opus-r13-status | - |

Notes
- F: had 45.0 GB free at start (< 50 GB floor), so scratch/builds/handoff exes are on C:\o13\ (C: 169.7 GB free) until F: is >= 50 GB again.
