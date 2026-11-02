# Opus R14-B status (PC clock; updated at every push)

| item | state | branch | last commit |
|---|---|---|---|
| setup | DONE 12:20: worktrees, PLAN (item 1), TOOLS, AGENTS.md R14-B rules | opus-r14b-status | see git log |
| 1 fast npt loader | IN PROGRESS 13:47: b4 bit-identical (1000/1000 train, 300+102 val); review R14B-I1-1 fixes -> candidate b5 9eb29b7d (pc1 = pc2, self-test 7/7 groups local + CI ASan/UBSan/TSan); CPU loss match: old arm done, fast arm running; GPU_REQUEST.md pushed (30-min window) | opus-r14b-fast-loader | 7f0f1257 |
| 2 resumable relabel | IN PROGRESS 13:47: relabel2.py + tests + proof driver pushed; smoke kill/resume md5 identical; next: exit-code tests, 1M proof | opus-r14b-relabel | 525e72f1 |
| final report | TODO | opus-r14b-status | - |
