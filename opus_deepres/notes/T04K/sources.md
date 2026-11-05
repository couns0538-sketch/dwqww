# T04K sources (null-move pruning details)

One line per source read: url or repo@sha | licence tier | what it gave | card id or "no card".

1. lock source `src/search.cpp` 1-1531 + `include/forge/search.hpp:262-284` (own code, read in full) | own | NMP block :964-999 (conditions :965-968, R :970-971, null child :979 with !cut_node, mate clamp :983, verification at depth >= 14 :984-997 that turns NMP off for the verifying frame only :989-992), no improving / tt_pv / cut-node term, no TT prefetch after the null move (:978-979 vs :1126) | all cards
2. official-stockfish/Stockfish commit titles + fishtest blocks since 2016 (tools/mine_commits.py --grep 'null|nmp|zugzwang|verification', cache stops 2018-05) | GPL-3.0, titles / test logs only | 78 commits: improving terms 75b75bc / b9e3e79 / 0571e4e, ttPv d878bc8, recursive-verification fix beaadd6, cut-node only c8d8e36, statScore removed 6de2587, nmpColor removed f66c362 | T04K-01, TABLE
3. Reckless, Obsidian, Stormphrax, PlentyChess, Berserk, Viridithas, Alexandria commit titles since 2024 (tools/mine_commits.py --grep 'null|nmp|zugzwang|verif', one batch) | GPL-3.0 / AGPL-3.0 / no licence, titles / test lines only | Reckless #649 #1031 #975 #403 #750 #231 #352 #242; SP #205 #312; VD #314 #352; Alexandria #483 | T04K-01, TABLE
