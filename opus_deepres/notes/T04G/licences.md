# T04G licence rows (tools/licence_at.py --row, one per repo, at the commit read; run 23:57 PC clock)

| repo | sha | date | file | licence | first line | api |
|---|---|---|---|---|---|---|
| Alex2262/AltairChessEngine | b2447b825b | 2026-04-19 | LICENSE | MIT | MIT License | api: MIT |
| Adam-Kulju/Patricia | 67d83d7056 | 2026-09-12 | LICENSE | MIT | MIT License | api: MIT |

- Both MIT at the exact commits whose source files were read for DIFF.md: source may be read, copy only with notice.
  No code is copied into cards or notes; mechanisms are described in own words; no tuned constants are carried over.
- Forge lock FD3A5190 source (`src_al1s198_clean`): own code, read-only.
- Older commits: the PR patches read here (Altair PR 89 / 92 / 105 / 118 / 120, earliest merged 2023-07-03; Patricia
  PR 65 / 47 / 172, earliest 2024-08-16) are all newer than the only commit that touched each repo's LICENSE (Altair
  7f28fb4127 2023-05-28, Patricia ffc0f5f6f5 2024-01-07; found by the T04 verify run, notes/T04/licences.md), so MIT
  holds at every commit whose patch was read.

## Continuation worker rows (tools/licence_at.py --row, run 00:32 PC clock, for the patches read after 00:22)

| repo | sha | date | file | licence | first line | api |
|---|---|---|---|---|---|---|
| Alex2262/AltairChessEngine | cbb5e27ab2 | 2024-07-18 | LICENSE | MIT | MIT License | api: MIT |
| Alex2262/AltairChessEngine | b68643baab | 2023-07-08 | LICENSE | MIT | MIT License | api: MIT |

- cbb5e27ab2 = merge of Altair PR 182 (card T04G-05), b68643baab = merge of Altair PR 95 (TABLE.md row 27): patches
  read, MIT at both, copy with notice; nothing copied.
- Altair PR 25 / 31 / 34 (May 2023) predate Altair's LICENSE commit 7f28fb4127 (2023-05-28): only their PR text (title
  and test block) was read, which the rules allow for any repo; no patch of theirs was opened.
- Patricia engine/src/search.h at 67d83d7056 (MIT, row above) was grepped and two windows read for DIFF.md.
