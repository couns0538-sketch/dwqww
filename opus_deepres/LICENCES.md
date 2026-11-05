# Licences of every source read by this job

Rule: MIT / BSD / Apache source may be read (copy only with notice, link and path). GPL, AGPL and unlicensed repos:
README, docs, wiki, changelogs, commit titles, PR text and test logs only - never source; Stockfish and nnue-pytorch
source are skipped entirely. Mechanisms are described in own words; no tuned constants are carried over.

Licence table given in the brief (read on 2026-10-30): MIT (copy allowed with notice): Caissa, Altair, Patricia,
bullet; Fathom: verify. GPL-3.0 (ideas only): Stockfish, Berserk, Obsidian, PlentyChess, Stormphrax, Alexandria,
Koivisto, Ethereal, Halogen, RubiChess, fishtest, nnue-pytorch. AGPL (ideas only): Viridithas (AGPL-3.0-only since
v21), Reckless. No LICENSE file (all rights reserved, ideas only): Integral.

How the rows below are made: each worker runs `tools/licence_at.py OWNER/REPO [SHA] --row` at the commit it read and
writes the row to `notes/T<nn>/licences.md`; `tools/merge_licences.py` re-runs every (repo, commit) row and rebuilds
this table. Tool fix (between 22:53 and 22:54 PC clock): the first version guessed "AGPL-3.0" for GPL-3.0 texts (the GPL-3.0 text names the
Affero licence in its section 13); workers noticed and noted it; the merged rows are re-run with the fixed tool.

## Checked by this job (tools/merge_licences.py)
<!-- merged:start -->
| repo | commit read | date | file | licence | first line | GitHub API | tracks | use |
|---|---|---|---|---|---|---|---|---|
| Adam-Kulju/Patricia | 67d83d7056 | 2026-09-12 | LICENSE | MIT | MIT License | api: MIT | T04 | copy with notice |
| Alex2262/AltairChessEngine | b2447b825b | 2026-04-19 | LICENSE | MIT | MIT License | api: MIT | T04 | copy with notice |
| PGG106/Alexandria | 49391d7b70 | 2026-07-22 | LICENSE.md | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T07 | ideas only |
| Witek902/Caissa | 57cae7ef71 | 2026-11-04 | LICENSE | MIT | MIT License | api: MIT | T01, T04 | copy with notice |
| aronpetko/integral | 29456bb34c | 2026-11-04 | absent | no licence (all rights reserved) | - | api: none | T01 | ideas only (no licence) |
| cosmobobak/viridithas | 7489e701bb | 2026-11-04 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 | T01 | ideas only |
| jw1912/bullet | da426a49b2 | 2026-10-26 | LICENSE | MIT | MIT License | api: MIT | T01 | copy with notice |
| official-stockfish/Stockfish | 5ca4bfe72b | 2026-09-09 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T07 | ideas only |
| official-stockfish/Stockfish | d212e663bb | 2024-07-06 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06 | ideas only |
| official-stockfish/Stockfish | ff7cee4244 | 2026-10-28 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02 | ideas only |
| official-stockfish/nnue-pytorch | c625702757 | 2026-11-01 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02 | ideas only |

30-Oct table repos not read by this job (no check needed unless a card cites them): jdart1/Fathom (verify), jhonnold/berserk (GPL-3.0), gab8192/Obsidian (GPL-3.0), Yoshie2000/PlentyChess (GPL-3.0), Ciekce/Stormphrax (GPL-3.0), Luecx/Koivisto (GPL-3.0), AndyGrant/Ethereal (GPL-3.0), KierenP/Halogen (GPL-3.0), Matthies/RubiChess (GPL-3.0), official-stockfish/fishtest (GPL-3.0), codedeliveryservice/Reckless (AGPL).
<!-- merged:end -->

## Datasets and tools
PENDING (collected from the cards at the next report update).
