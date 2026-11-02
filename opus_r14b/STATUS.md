# Opus R14-B status (PC clock; updated at every push)

| item | state | branch | last commit |
|---|---|---|---|
| setup | DONE 12:20: worktrees, PLAN (items 1 + 2), TOOLS, AGENTS.md R14-B rules (+ Couns 13:45: no sub-agents, final 30-min bug hunt) | opus-r14b-status | see git log |
| 1 fast npt loader | IN PROGRESS 14:20: candidate b5 9eb29b7d (pc1 = pc2); bit-identical batches (raw 1000/1000 + val; trainer path 261/261 tensors); **exact 1-epoch loss match** (reproducible CPU setup); self-test + CI ASan/UBSan/TSan PASS; finding: npt `--seed` does not fix the init (optional patch 0006); running: config matrix, spanning batches past a wrap, ABBA, full-epoch loader run; GPU window requested (npt queue booked to Nov 8) | opus-r14b-fast-loader | d773b5bf |
| 2 resumable relabel | IN PROGRESS 14:20: relabel2.py; exit-code tests 19/19; 1M sample prepared (999,921 rows, 10,880 games, A = B); next: proof runs A and B (after item 1's CPU checks) | opus-r14b-relabel | 2fcf1c7d |
| final report | interim skeleton pushed; completed at the end | opus-r14b-status | 00fab7b0 |
