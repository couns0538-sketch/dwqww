# T02B licence rows (tools/licence_at.py --row, one per repo, at the commit read)

| repo | sha | date | file | licence | first line | api |
|---|---|---|---|---|---|---|
| Witek902/Caissa | 57cae7ef71 | 2026-11-04 | LICENSE | MIT | MIT License | api: MIT |
| cosmobobak/viridithas | 7489e701bb | 2026-11-04 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 |
| official-stockfish/Stockfish | d53071eff4 | 2021-06-03 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/nnue-pytorch | f5c9d01569 | 2026-04-15 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/nnue-pytorch | b26145006e | 2026-10-28 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | 9bdf2f8d4c | 2026-04-15 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | c3ce220408 | 2023-04-25 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| codedeliveryservice/Reckless | 460b614e37 | 2024-10-14 | LICENSE | MIT | MIT License | api: AGPL-3.0 |
| Witek902/Caissa | c84df9fce5 | 2026-07-25 | LICENSE | MIT | MIT License | api: MIT |
| Ciekce/Stormphrax | d1468d99e3 | 2026-08-29 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| Yoshie2000/PlentyChess | fdbdbccab8 | 2026-10-30 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| gab8192/Obsidian | 720614a61e | 2025-09-27 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| jhonnold/berserk | a3a6f62397 | 2026-11-04 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| PGG106/Alexandria | 829daf405e | 2026-11-02 | LICENSE.md | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| Adam-Kulju/Patricia | 67d83d7056 | 2026-09-12 | LICENSE | MIT | MIT License | api: MIT |
| Alex2262/AltairChessEngine | b2447b825b | 2026-04-19 | LICENSE | MIT | MIT License | api: MIT |
| TerjeKir/weiss | c735b8f3d2 | 2026-08-13 | COPYING.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |

Use: Caissa MIT = copy with notice (only mechanisms described, nothing copied, no constants carried over;
SelfPlay.cpp@57cae7ef71 and commit messages read). Viridithas AGPL-3.0 = ideas only (commit messages + the docs file
notes/networkhistory.txt; no source file). Stockfish GPL-3.0 = ideas only (commit messages, PR 6730 text, fishtest run
records; no source file; the fork commit linked from d53071eff4 and the recipe yaml linked from 9bdf2f8d4c were not
opened). nnue-pytorch GPL-3.0 = ideas only (commit titles, PR 450 text, commit metadata and a gh compare; the diff of
d87c248fbe / f5c9d01569 was NOT opened; the loader behaviour is cited from the crew's own-words spec
opus_r14b/item1/LOADER_SPEC.md). Reckless: MIT at 460b614e37 (2024), AGPL-3.0 on today's default branch - only that
commit message was read. Stormphrax, PlentyChess, Obsidian, berserk, Alexandria, weiss (GPL-3.0) and Patricia, Altair
(MIT): commit titles from the cached commit lists only (rows at the default-branch HEAD on 2026-11-05); no file opened.
