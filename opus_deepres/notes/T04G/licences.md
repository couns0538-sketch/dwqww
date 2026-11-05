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
