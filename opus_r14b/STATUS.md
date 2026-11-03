# Opus R14-B status (PC clock; updated at every push)

| item | state | branch | last commit |
|---|---|---|---|
| setup | DONE 12:20: worktrees, PLAN (items 1 + 2), TOOLS, AGENTS.md R14-B rules (+ Couns 13:45: no sub-agents, final 30-min bug hunt; 14:40: C: usable, keep >= 50 GB) | opus-r14b-status | see git log |
| 1 fast npt loader | DONE except the GPU window (requested in GPU_REQUEST.md, not granted: npt queue holds the GPU to Nov 8). b5 9eb29b7d: bit-identical batches, exact CPU loss match, ABBA 8.65x, full loader epoch 29.8 s / 166 MB, CI sanitizers PASS; distribution vs the live w4 layout over 32.8M positions: every total-variation distance < 0.001. HANDOFF.md (adapter path, live trainer = installer base 264/264, `--num-workers 3` enough) | opus-r14b-fast-loader | 801f3310 |
| 2 resumable relabel | DONE: **1M kill / resume proof PASSED 17:43** (md5 identical, frozen 5c88438f); bridge check PASS; post-proof code promoted (bf714c67, 75/75 tests); RELABEL_HANDOFF.md with measured costs (50M at 20k nodes, 2 workers: 75.4 h R13 probe / 72.4 h LTO+PGO probe; prepare 0.8 h; ~17.1 GB). 50M run not started (as asked) | opus-r14b-relabel | 51f2f0e0 |
| improvements (vs the proof baseline) | prepare `--jobs 2` 1.49x; LTO+PGO probe 1.075x single thread / 1.042x at 2 workers with identical labels (reproducible build); R8 v5 one-stream fix; 75 tests (was 19); R27 regression caught (2.05x); fen2bin check; label statistics | opus-r14b-relabel | 51f2f0e0 |
| reviews | R14B-I1-1 (sub-agent), I1-2, I2-1, I2-2, I2-3 (self-reviews, NOT independent); Couns 19:08: 20-min code review every 2 h (~19:30, ~21:30, ~23:30) and a 1-h review at the end (~02:00-03:00); window to ~03:05 again | - | - |
| final report | interim 18:55 with the before/after table; final after the 1-h end review | opus-r14b-status | 2e2698e0 |
