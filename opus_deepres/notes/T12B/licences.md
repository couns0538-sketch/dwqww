# T12B licence rows (tools/licence_at.py --row, one per repo read, at the commit read)

| repo | sha | date | root licence file | spdx guess | note | api |
|---|---|---|---|---|---|---|
| official-stockfish/Stockfish | 1548538ede | 2026-09-18 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | 23df82905b | 2026-10-25 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | 3d92950859 | 2024-06-15 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | c56bd10cb5 | 2025-08-17 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | 7316ef4e86 | 2026-10-24 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | 5380403393 | 2026-08-24 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | df01cb7ed3 | 2026-04-09 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | b7f17346e5 | 2024-11-22 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |

Notes
- Stockfish: GPL-3.0 at every commit whose message was read (1548538ede, 23df82905b, 3d92950859, c56bd10cb5, 7316ef4e86, 5380403393,
  df01cb7ed3, b7f17346e5); use =
  ideas only. Read: commit titles and messages via tools/mine_commits.py; no source file, no diff, no test file.
- Caissa (MIT): commit titles only this round; its licence row is in notes/T04/licences.md (57cae7ef71, MIT).
- talkchess.com forum thread: no licence stated; only facts (a FEN, move counts) were taken.
- Own code (lock source, fable-review-buffix, buffix64 tools): no row needed. The buffix annealer imports python-chess
  (GPL-3.0) as a library; T12B-02 replaces it with an own annealer so the suite carries no GPL tool.
