# Opus R14-B status (PC clock; updated at every push)

| item | state | branch | last commit |
|---|---|---|---|
| setup | DONE 12:20: worktrees, PLAN (items 1 + 2), TOOLS, AGENTS.md R14-B rules (+ Couns 13:45: no sub-agents, final 30-min bug hunt; 14:40: C: usable, keep >= 50 GB) | opus-r14b-status | see git log |
| 1 fast npt loader | DONE except the GPU window (requested in GPU_REQUEST.md, not granted: npt queue holds the GPU to Nov 8). b5 9eb29b7d: bit-identical batches (raw, 24-config matrix, spanning batches past a wrap, trainer path), exact CPU loss match, ABBA 8.65x, full loader epoch 29.8 s / 166 MB, CI sanitizers PASS | opus-r14b-fast-loader | f3e0ed93 |
| 2 resumable relabel | PROOF RUNNING (15:25): 1M rows, run A uninterrupted (29/100 shards) + run B with 2 hard exits (first one landed mid-shard 14, resumed; second due ~15:34); ~340k rows/h per worker; ends ~17:30. Exit-code tests 19/19 on the frozen code. Review R14B-I2-1 (self-review, NOT independent): 7 findings, fixed in the dev copy (post_proof_changes.patch), dev tests 48/48 incl. a mini kill/resume; promoted after the proof | opus-r14b-relabel | f59bf592 |
| after the proof (baseline) | assemble + md5 compare, bridge to the final relabel2.py, 2-worker + node-count measurements, loader distribution comparison (old w4 vs fast) | - | - |
| improvements to 02:30 | first: LTO + PGO build of the relabel probe (labels must stay bit-identical; ABBA speed); reviews every ~2 h; final 30-min bug hunt 02:30-03:00; final report with measured before/after numbers | - | - |
| final report | interim pushed 14:45 | opus-r14b-status | 57f591c8 |
