# Opus R14-B status (PC clock; updated at every push)

| item | state | branch | last commit |
|---|---|---|---|
| setup | DONE 12:20: worktrees, PLAN (items 1 + 2), TOOLS, AGENTS.md R14-B rules (+ Couns 13:45: no sub-agents, final 30-min bug hunt; 14:40: C: usable, keep >= 50 GB) | opus-r14b-status | see git log |
| 1 fast npt loader | DONE except the GPU window (requested in GPU_REQUEST.md, not granted: npt queue holds the GPU to Nov 8). b5 9eb29b7d: bit-identical batches (raw, 24-config matrix, spanning batches past a wrap, trainer path), exact CPU loss match, ABBA 8.65x, full loader epoch 29.8 s / 166 MB, CI sanitizers PASS. HANDOFF.md: adoption through the adapter (`--npt-repo` + `--npt-extra --fast-loader`), `--num-workers 3` enough | opus-r14b-fast-loader | 4855888a |
| 2 resumable relabel | PROOF RUNNING (16:05): A 50/100, B 47/100 shards; both hard exits of B done (14:48:59 in shard 14, 15:34:20 in shard 36), resumed, no orphaned probe; ends ~17:50. Post-proof dev copy (patches/post_proof_changes.patch): review R14B-I2-1 fixes F1-F7, F8 (R8 v5 shards split games across files -> one input stream in name order), R17, `prepare --jobs 2`; dev tests 73/73 (+1 case running). Output checked through Forge's fen2bin (new labels carried 1200/1200). Labelling/resume path identical source in both versions (logs/fn_diff) | opus-r14b-relabel | fb84a004 |
| after the proof (baseline) | assemble + md5 compare, bridge to the final relabel2.py, 2-worker + node-count measurements, loader distribution comparison (old w4 vs fast) | - | - |
| improvements to 02:30 | first: LTO + PGO build of the relabel probe (labels must stay bit-identical; ABBA speed); reviews every ~2 h; final 30-min bug hunt 02:30-03:00; final report with measured before/after numbers | - | - |
| final report | interim pushed 14:45 | opus-r14b-status | 57f591c8 |
