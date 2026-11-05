# T02C licence rows (tools/licence_at.py --row, one per repo, at the commit read)

| repo | sha | date | file | licence | first line | api |
|---|---|---|---|---|---|---|
| jw1912/bullet | da426a49b2 | 2026-10-26 | LICENSE | MIT | MIT License | api: MIT |
| cosmobobak/viriformat | 0238b315ea | 2026-10-03 | absent | no licence (all rights reserved) | - | api: none |
| lynx-chess/Lynx | ee39ad14c7 | 2026-09-25 | LICENSE | MIT | MIT License | api: MIT |
| codedeliveryservice/Reckless | 2e66182cd3 | 2024-03-14 | LICENSE | MIT | MIT License | api: AGPL-3.0 |
| PGG106/Alexandria | c77904fa86 | 2026-02-13 | LICENSE.md | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-clockwork/Clockwork | 703fcc533c | 2025-09-15 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 |
| AndyGrant/Ethereal | 962c75e40b | 2021-07-18 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| AndyGrant/Ethereal | 33f276e54e | 2020-04-29 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | f09adaa4a4 | 2024-01-07 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| cosmobobak/viridithas | 7489e701bb | 2026-11-04 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 |

Use: bullet MIT at da426a49b2 = copy with notice (docs/3-data.md and examples/advanced/filter.rs read; nothing
copied, the example's numbers are not carried over). Lynx MIT at ee39ad14c7 = copy with notice (the 26-line diff of
the eval / result mismatch filter read via gh api; described in own words, nothing copied). Reckless MIT at 2e66182cd3
(AGPL-3.0 on today's default branch): commit message only, diff not opened. viriformat has NO licence file (all rights
reserved): README only (a format spec), no source file, so its Filter semantics are known only from the MIT Lynx port.
Ethereal, Stockfish, Alexandria (GPL-3.0) and Viridithas, Clockwork (AGPL-3.0) = ideas only: commit messages, PR 599
body and the Viridithas docs file notes/networkhistory.txt (T02B's saved copy, read-only); no source file opened.
Stormphrax, PlentyChess, Obsidian, berserk: commit titles from the cached lists only, rows in
notes/T02B/licences.md; Halogen, Sirius, Renegade, Starzix, Tarnished, pawnocchio: commit titles from the cached lists
only, no file opened, no row written.
