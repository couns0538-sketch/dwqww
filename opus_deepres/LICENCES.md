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
| Adam-Kulju/Patricia | 67d83d7056 | 2026-09-12 | LICENSE | MIT | MIT License | api: MIT | T04, T06 | copy with notice |
| Adam-Kulju/Patricia | bf655244b6 | 2025-01-19 | LICENSE | MIT | MIT License | api: MIT | T04 | copy with notice |
| Alex2262/AltairChessEngine | 6bddce6de2 | 2024-06-14 | LICENSE | MIT | MIT License | api: MIT | T04 | copy with notice |
| Alex2262/AltairChessEngine | b2447b825b | 2026-04-19 | LICENSE | MIT | MIT License | api: MIT | T04 | copy with notice |
| AndyGrant/OpenBench | 230ed46e47 | 2026-11-04 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12 | ideas only |
| PGG106/Alexandria | 49391d7b70 | 2026-07-22 | LICENSE.md | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T07 | ideas only |
| PGG106/Alexandria | 8e3fc66e52 | 2024-06-24 | LICENSE.md | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T07 | ideas only |
| Witek902/Caissa | 434bbda5c3 | 2024-01-03 | LICENSE | MIT | MIT License | api: MIT | T04 | copy with notice |
| Witek902/Caissa | 57cae7ef71 | 2026-11-04 | LICENSE | MIT | MIT License | api: MIT | T01, T04, T06 | copy with notice |
| Witek902/Caissa | 8d2454c72f | 2026-10-17 | LICENSE | MIT | MIT License | api: MIT | T02 | copy with notice |
| aronpetko/integral | 29456bb34c | 2026-11-04 | absent | no licence (all rights reserved) | - | api: none | T01 | ideas only (no licence) |
| cosmobobak/viridithas | 7489e701bb | 2026-11-04 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 | T01 | ideas only |
| cosmobobak/viridithas-networks | d3da3953e4 | 2026-06-08 | LICENSE | CC0-1.0 | Creative Commons Legal Code | api: CC0-1.0 | T01 | free use (public-domain dedication) |
| jw1912/bullet | da426a49b2 | 2026-10-26 | LICENSE | MIT | MIT License | api: MIT | T01 | copy with notice |
| llvm/llvm-project | b537630299 | 2026-10-20 | LICENSE.TXT | MIT | ====================================================================== | api: NOASSERTION | T05 | copy with notice |
| llvm/llvm-project | f7d11195ab | 2026-11-04 | LICENSE.TXT | MIT | ====================================================================== | api: NOASSERTION | T12 | copy with notice |
| official-stockfish/Stockfish | 5c617e579c | 2025-02-27 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12 | ideas only |
| official-stockfish/Stockfish | 5ca4bfe72b | 2026-09-09 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T07 | ideas only |
| official-stockfish/Stockfish | d212e663bb | 2024-07-06 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06 | ideas only |
| official-stockfish/Stockfish | ff7cee4244 | 2026-10-28 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02, T04, T05 | ideas only |
| official-stockfish/books | a804a97e70 | 2026-10-16 | LICENSE | CC0-1.0 | Creative Commons Legal Code | api: CC0-1.0 | T12 | free use (public-domain dedication) |
| official-stockfish/fishtest | 5a8a229a52 | 2026-10-13 | absent | no licence (all rights reserved) | - | api: none | T12 | ideas only (no licence) |
| official-stockfish/nnue-pytorch | c625702757 | 2026-11-01 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02 | ideas only |

30-Oct table repos not read by this job (no check needed unless a card cites them): jdart1/Fathom (verify), jhonnold/berserk (GPL-3.0), gab8192/Obsidian (GPL-3.0), Yoshie2000/PlentyChess (GPL-3.0), Ciekce/Stormphrax (GPL-3.0), Luecx/Koivisto (GPL-3.0), AndyGrant/Ethereal (GPL-3.0), KierenP/Halogen (GPL-3.0), Matthies/RubiChess (GPL-3.0), codedeliveryservice/Reckless (AGPL).
<!-- merged:end -->

## Differences from the 30-Oct table
- official-stockfish/fishtest: the 30-Oct table says GPL-3.0, but at 5a8a229a52 there is no licence file anywhere in
  the tree (recursive tree listing, 23:05) and GitHub detects none. Treated as no licence: ideas only (its test pages
  and logs are read, never its code) - the same use as GPL, so nothing changes for the cards.

## Datasets and tools
PENDING (collected from the cards at the next report update).
