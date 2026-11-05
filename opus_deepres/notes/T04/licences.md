# T04 licence rows (tools/licence_at.py --row, one per repo, at the commit read)

| repo | sha | date | file | licence | first line | api |
|---|---|---|---|---|---|---|
| Witek902/Caissa | 57cae7ef71 | 2026-11-04 | LICENSE | MIT | MIT License | api: MIT |
| Adam-Kulju/Patricia | 67d83d7056 | 2026-09-12 | LICENSE | MIT | MIT License | api: MIT |
| Alex2262/AltairChessEngine | b2447b825b | 2026-04-19 | LICENSE | MIT | MIT License | api: MIT |

- Altair = github.com/Alex2262/AltairChessEngine (found by gh api; "A top superhuman chess engine made in c++"), MIT at
  HEAD b2447b825b. Caissa, Patricia, Altair: MIT, source may be read (copy only with notice); rows run 22:51 PC clock.
| official-stockfish/Stockfish | ff7cee4244 | 2026-10-28 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |

- Stockfish: GPL-3.0 (row run 23:13 PC clock): ideas only. Read: commit titles and commit messages (with their fishtest
  blocks) via tools/mine_commits.py, nothing else; no source file, no diff.

- Verify re-run (T04 adversarial verify): the rows above match a fresh `--row` run at the same SHAs. Diffs were read at
  older commits, so the LICENSE was also checked at the oldest commit whose diff was read; the LICENSE file of each repo
  was touched by exactly one commit (Caissa e485cb984e 2021-10-25, Patricia ffc0f5f6f5 2024-01-07, Altair 7f28fb4127
  2023-05-28), so MIT holds at every commit read:
| Witek902/Caissa | 434bbda5c3 | 2024-01-03 | LICENSE | MIT | MIT License | api: MIT |
| Adam-Kulju/Patricia | bf655244b6 | 2025-01-19 | LICENSE | MIT | MIT License | api: MIT |
| Alex2262/AltairChessEngine | 6bddce6de2 | 2024-06-14 | LICENSE | MIT | MIT License | api: MIT |
