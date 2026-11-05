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
| Adam-Kulju/Patricia | 36b2889435 | 2026-08-02 | LICENSE | MIT | MIT License | api: MIT | T05D | copy with notice |
| Adam-Kulju/Patricia | 67cdfcb55f | 2025-07-07 | LICENSE | MIT | MIT License | api: MIT | T04G | copy with notice |
| Adam-Kulju/Patricia | 67d83d7056 | 2026-09-12 | LICENSE | MIT | MIT License | api: MIT | T02B, T04, T04G, T05C, T06 | copy with notice |
| Adam-Kulju/Patricia | bf655244b6 | 2025-01-19 | LICENSE | MIT | MIT License | api: MIT | T04 | copy with notice |
| Adam-Kulju/Patricia | eeb786dd5a | 2026-07-30 | LICENSE | MIT | MIT License | api: MIT | T05D | copy with notice |
| Alex2262/AltairChessEngine | 12ac55a0e2 | 2026-01-21 | LICENSE | MIT | MIT License | api: MIT | T05C | copy with notice |
| Alex2262/AltairChessEngine | 2639e58f60 | 2025-12-31 | LICENSE | MIT | MIT License | api: MIT | T05D | copy with notice |
| Alex2262/AltairChessEngine | 6bddce6de2 | 2024-06-14 | LICENSE | MIT | MIT License | api: MIT | T04 | copy with notice |
| Alex2262/AltairChessEngine | 99df021453 | 2023-09-21 | LICENSE | MIT | MIT License | api: MIT | T04G | copy with notice |
| Alex2262/AltairChessEngine | b2447b825b | 2026-04-19 | LICENSE | MIT | MIT License | api: MIT | T02B, T04, T04G, T06B | copy with notice |
| Alex2262/AltairChessEngine | b38d5ea001 | 2023-07-03 | LICENSE | MIT | MIT License | api: MIT | T04G | copy with notice |
| Alex2262/AltairChessEngine | b68643baab | 2023-07-08 | LICENSE | MIT | MIT License | api: MIT | T04G | copy with notice |
| Alex2262/AltairChessEngine | cbb5e27ab2 | 2024-07-18 | LICENSE | MIT | MIT License | api: MIT | T04G | copy with notice |
| Alex2262/AltairChessEngine | e42311036d | 2023-07-17 | LICENSE | MIT | MIT License | api: MIT | T04G | copy with notice |
| AndyGrant/Ethereal | 0e47e9b67f | 2024-06-11 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04N | ideas only |
| AndyGrant/Ethereal | 513a93c232 | 2020-09-19 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06C | ideas only |
| AndyGrant/Ethereal | 5e25d42142 | 2022-01-16 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06C | ideas only |
| AndyGrant/Ethereal | 7f6b2d3945 | 2018-07-22 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T05B | ideas only |
| AndyGrant/Ethereal | 8d02577b5f | 2020-09-28 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06C | ideas only |
| AndyGrant/Ethereal | b552e36f88 | 2020-09-24 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06C | ideas only |
| AndyGrant/Ethereal | f71ac4769a | 2023-03-17 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04N | ideas only |
| AndyGrant/OpenBench | 230ed46e47 | 2026-11-04 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12 | ideas only |
| Ciekce/Stormphrax | 29e175a2f5 | 2024-11-09 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04B | ideas only |
| Ciekce/Stormphrax | 3219c3021b | 2024-11-13 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04F | ideas only |
| Ciekce/Stormphrax | 3ff4e1a02a | 2024-06-20 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T01B | ideas only |
| Ciekce/Stormphrax | 41f435dd88 | 2025-06-05 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T01B | ideas only |
| Ciekce/Stormphrax | 639efd5c08 | 2025-11-10 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06B | ideas only |
| Ciekce/Stormphrax | 76c5178883 | 2026-05-19 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04C | ideas only |
| Ciekce/Stormphrax | d1468d99e3 | 2026-08-29 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02B, T04B, T04F, T04H | ideas only |
| Ciekce/Stormphrax | e410c4214f | 2024-01-07 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04B | ideas only |
| Ciekce/Stormphrax | e4b88b7a67 | 2026-02-22 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T01B | ideas only |
| Ciekce/Stormphrax | eea6168441 | 2026-06-13 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T01B | ideas only |
| Disservin/chess-library | 430266434a | 2026-11-03 | LICENSE | MIT | MIT License | api: MIT | T05C | copy with notice |
| KierenP/Halogen | 50a42bca43 | 2025-08-01 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04N | ideas only |
| KierenP/Halogen | f00b8e3417 | 2025-11-14 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04N | ideas only |
| KierenP/Halogen | fe9b4dafc7 | 2026-11-01 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04N | ideas only |
| Luecx/Koivisto | 6de225ad85 | 2023-02-08 | LICENSE.md | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04N | ideas only |
| Matthies/RubiChess | 263f15d796 | 2026-11-03 | copying | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04N | ideas only |
| PGG106/Alexandria | 49391d7b70 | 2026-07-22 | LICENSE.md | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T07 | ideas only |
| PGG106/Alexandria | 7de97e77aa | 2024-09-29 | LICENSE.md | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06B | ideas only |
| PGG106/Alexandria | 829daf405e | 2026-11-02 | LICENSE.md | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02B, T04C | ideas only |
| PGG106/Alexandria | 8e3fc66e52 | 2024-06-24 | LICENSE.md | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T07 | ideas only |
| SH11235/rshogi | f248c52c84 | 2026-11-04 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T05E | ideas only |
| TerjeKir/weiss | c735b8f3d2 | 2026-08-13 | COPYING.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02B | ideas only |
| TerjeKir/weiss | ff59b2741d | 2020-10-26 | COPYING.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T05B | ideas only |
| TimAnthonyAlexander/chessgo | 3eedea13d6 | 2026-07-07 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T05E | ideas only |
| TimAnthonyAlexander/chessgo | cdbe8eea5f | 2026-08-30 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T05E | ideas only |
| Witek902/Caissa | 2fd8f56e40 | 2023-10-12 | LICENSE | MIT | MIT License | api: MIT | T04F | copy with notice |
| Witek902/Caissa | 434bbda5c3 | 2024-01-03 | LICENSE | MIT | MIT License | api: MIT | T04 | copy with notice |
| Witek902/Caissa | 47fc56acc5 | 2023-10-21 | LICENSE | MIT | MIT License | api: MIT | T04F | copy with notice |
| Witek902/Caissa | 4b2cf654a3 | 2025-09-26 | LICENSE | MIT | MIT License | api: MIT | T05F | copy with notice |
| Witek902/Caissa | 57cae7ef71 | 2026-11-04 | LICENSE | MIT | MIT License | api: MIT | T01, T02B, T04, T04F, T05C, T05F, T06 | copy with notice |
| Witek902/Caissa | 8d2454c72f | 2026-10-17 | LICENSE | MIT | MIT License | api: MIT | T02 | copy with notice |
| Witek902/Caissa | a677c890f9 | 2023-08-23 | LICENSE | MIT | MIT License | api: MIT | T04F | copy with notice |
| Witek902/Caissa | b02c47fa35 | 2026-05-24 | LICENSE | MIT | MIT License | api: MIT | T05D | copy with notice |
| Witek902/Caissa | c84df9fce5 | 2026-07-25 | LICENSE | MIT | MIT License | api: MIT | T02B | copy with notice |
| Witek902/Caissa | c8a30a7d11 | 2023-08-17 | LICENSE | MIT | MIT License | api: MIT | T04F | copy with notice |
| Yoshie2000/PlentyChess | 5c8c8c7b46 | 2025-12-22 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06B | ideas only |
| Yoshie2000/PlentyChess | 5fe2d9cd7e | 2024-11-09 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04H | ideas only |
| Yoshie2000/PlentyChess | 7cb061e068 | 2025-06-03 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04H | ideas only |
| Yoshie2000/PlentyChess | 9686668c65 | 2024-07-23 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T01B | ideas only |
| Yoshie2000/PlentyChess | fbc64b5ba8 | 2025-10-12 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T01B | ideas only |
| Yoshie2000/PlentyChess | fdbdbccab8 | 2026-10-30 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02B, T04C | ideas only |
| aronpetko/integral | 29456bb34c | 2026-11-04 | absent | no licence (all rights reserved) | - | api: none | T01 | ideas only (no licence) |
| codedeliveryservice/Reckless | 460b614e37 | 2024-10-14 | LICENSE | MIT | MIT License | api: AGPL-3.0 | T02B | copy with notice |
| codedeliveryservice/Reckless | 5e5443d798 | 2026-03-25 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 | T04E | ideas only |
| codedeliveryservice/Reckless | 5e669a65b4 | 2026-05-22 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 | T04E | ideas only |
| codedeliveryservice/Reckless | 845f49d3f1 | 2026-01-14 | absent | no licence (all rights reserved) | - | api: AGPL-3.0 | T04E | ideas only (no licence) |
| codedeliveryservice/Reckless | aec5cb2e80 | 2026-10-29 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 | T04E | ideas only |
| codedeliveryservice/Reckless | d6603046e7 | 2026-07-30 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 | T04E | ideas only |
| cosmobobak/viridithas | 591aa39bd4 | 2026-02-01 | LICENSE | MIT | MIT License | api: AGPL-3.0 | T04E | copy with notice |
| cosmobobak/viridithas | 7489e701bb | 2026-11-04 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 | T01, T02B, T04E | ideas only |
| cosmobobak/viridithas-networks | d3da3953e4 | 2026-06-08 | LICENSE | CC0-1.0 | Creative Commons Legal Code | api: CC0-1.0 | T01 | free use (public-domain dedication) |
| gab8192/Obsidian | 2079f0879a | 2024-01-04 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04B | ideas only |
| gab8192/Obsidian | 720614a61e | 2025-09-27 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02B, T04B, T04H | ideas only |
| gab8192/Obsidian | beaa13742e | 2024-08-15 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T01B | ideas only |
| gab8192/Obsidian | d5f3e454dc | 2024-12-20 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04B | ideas only |
| gab8192/Obsidian | d8e8007f15 | 2024-03-24 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T01B | ideas only |
| gab8192/Obsidian | e144325d52 | 2025-06-20 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06B | ideas only |
| jdart1/arasan-chess | 2dbc0649dc | 2021-05-31 | absent | no licence (all rights reserved) | - | api: NOASSERTION | T05B | ideas only (no licence) |
| jdart1/arasan-chess | 6e432a21ef | 2026-11-04 | LICENSE | MIT | ---------------------------------------------------------------------- | api: NOASSERTION | T05B | copy with notice |
| jhonnold/berserk | 8c72a1d869 | 2024-01-04 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06B | ideas only |
| jhonnold/berserk | a3a6f62397 | 2026-11-04 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02B, T04C, T04H | ideas only |
| jw1912/bullet | da426a49b2 | 2026-10-26 | LICENSE | MIT | MIT License | api: MIT | T01 | copy with notice |
| llvm/llvm-project | b537630299 | 2026-10-20 | LICENSE.TXT | Apache-2.0 WITH LLVM-exception | ====================================================================== | api: NOASSERTION | T05 | copy with notice |
| llvm/llvm-project | f7d11195ab | 2026-11-04 | LICENSE.TXT | Apache-2.0 WITH LLVM-exception | ====================================================================== | api: NOASSERTION | T12 | copy with notice |
| lynx-chess/Lynx | 57bd72e93f | 2026-11-04 | LICENSE | MIT | MIT License | api: MIT | T05E | copy with notice |
| official-clockwork/Clockwork | 2844edc8c0 | 2026-01-05 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 | T06C | ideas only |
| official-clockwork/Clockwork | 753f88460c | 2026-01-25 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 | T06C | ideas only |
| official-stockfish/Stockfish | 1548538ede | 2026-09-18 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12B | ideas only |
| official-stockfish/Stockfish | 23df82905b | 2026-10-25 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12B | ideas only |
| official-stockfish/Stockfish | 2e96c513ad | 2019-10-06 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04F | ideas only |
| official-stockfish/Stockfish | 392b529c3f | 2020-11-08 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04F | ideas only |
| official-stockfish/Stockfish | 3d92950859 | 2024-06-15 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12B | ideas only |
| official-stockfish/Stockfish | 472de897cb | 2019-10-18 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04F | ideas only |
| official-stockfish/Stockfish | 49ef4c935a | 2024-04-24 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T05E | ideas only |
| official-stockfish/Stockfish | 5380403393 | 2026-08-24 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12B | ideas only |
| official-stockfish/Stockfish | 5c617e579c | 2025-02-27 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12 | ideas only |
| official-stockfish/Stockfish | 5ca4bfe72b | 2026-09-09 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T07 | ideas only |
| official-stockfish/Stockfish | 71e0b5385e | 2020-01-28 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04H | ideas only |
| official-stockfish/Stockfish | 73018a0337 | 2021-09-23 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12 | ideas only |
| official-stockfish/Stockfish | 7316ef4e86 | 2026-10-24 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12B | ideas only |
| official-stockfish/Stockfish | 86f1df7134 | 2026-06-10 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T05B | ideas only |
| official-stockfish/Stockfish | 9451419912 | 2021-12-08 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04H | ideas only |
| official-stockfish/Stockfish | 9bdf2f8d4c | 2026-04-15 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02B | ideas only |
| official-stockfish/Stockfish | a06e7004c1 | 2024-09-17 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12 | ideas only |
| official-stockfish/Stockfish | b7f17346e5 | 2024-11-22 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12B | ideas only |
| official-stockfish/Stockfish | c02b3a4c7a | 2020-08-30 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04H | ideas only |
| official-stockfish/Stockfish | c3ce220408 | 2023-04-25 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02B | ideas only |
| official-stockfish/Stockfish | c56bd10cb5 | 2025-08-17 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12B | ideas only |
| official-stockfish/Stockfish | d212e663bb | 2024-07-06 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06 | ideas only |
| official-stockfish/Stockfish | d47aa639bd | 2024-04-21 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T04H | ideas only |
| official-stockfish/Stockfish | d53071eff4 | 2021-06-03 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02B | ideas only |
| official-stockfish/Stockfish | df01cb7ed3 | 2026-04-09 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T12B | ideas only |
| official-stockfish/Stockfish | e0bafa1911 | 2020-08-30 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T06C | ideas only |
| official-stockfish/Stockfish | e17725f445 | 2026-04-26 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T05C | ideas only |
| official-stockfish/Stockfish | ff7cee4244 | 2026-10-28 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02, T04, T04D, T05 | ideas only |
| official-stockfish/books | a804a97e70 | 2026-10-16 | LICENSE | CC0-1.0 | Creative Commons Legal Code | api: CC0-1.0 | T12 | free use (public-domain dedication) |
| official-stockfish/fishtest | 5a8a229a52 | 2026-10-13 | absent | no licence (all rights reserved) | - | api: none | T12 | ideas only (no licence) |
| official-stockfish/nnue-pytorch | b26145006e | 2026-10-28 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02B | ideas only |
| official-stockfish/nnue-pytorch | c625702757 | 2026-11-01 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02 | ideas only |
| official-stockfish/nnue-pytorch | f5c9d01569 | 2026-04-15 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T02B | ideas only |
| ovnice-dev/onechess | 928d53d2eb | 2026-10-30 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T05E | ideas only |
| ovnice-dev/onechess | e9d1c500d6 | 2026-11-04 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T05E | ideas only |
| rektdie/Eleanor | 134af1abde | 2026-10-03 | LICENSE | MIT | MIT License | api: MIT | T05E | copy with notice |
| rektdie/Eleanor | 2c81f2fc4e | 2026-10-12 | LICENSE | MIT | MIT License | api: MIT | T05E | copy with notice |
| sebhofmann/sleepmind2 | 4f6cdfcc5a | 2026-11-03 | absent | no licence (all rights reserved) | - | api: none | T05E | ideas only (no licence) |
| yaneurao/YaneuraOu | 3a0e4fd239 | 2026-11-03 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 | T05E | ideas only |

30-Oct table repos not read by this job (no check needed unless a card cites them): jdart1/Fathom (verify).
<!-- merged:end -->

## Differences from the 30-Oct table
- official-stockfish/fishtest: the 30-Oct table says GPL-3.0, but at 5a8a229a52 there is no licence file anywhere in
  the tree (recursive tree listing, 23:05) and GitHub detects none. Treated as no licence: ideas only (its test pages
  and logs are read, never its code) - the same use as GPL, so nothing changes for the cards.

## Datasets and tools named by the cards (licence as stated by the source; use)
| dataset / tool | licence | where it was read | use in the cards |
|---|---|---|---|
| Lc0 (Leela) training data and the Leela-scored / TB-rescored binpacks | ODbL 1.0 (Stockfish README @ff7cee4244 lines 125-126) | notes/T02/TABLE.md (one line) | optional external teacher slice only after G1 (MIX.md 5); attribution needed; sets of 328-514 GB do not fit F: |
| Lichess open game database / evaluations | CC0 per database.lichess.org (30-Oct round); NOT re-checked in this job | notes/T06/FIT_RECIPE.md D4 | optional check data only |
| cosmobobak/viridithas-networks @d3da3953e4 | CC0-1.0 (LICENSE "Creative Commons Legal Code"; GitHub: CC0-1.0) | notes/T01/licences.md | none used (nets of another engine; no card trains on them) |
| aronpetkovski/integral-datasets (Hugging Face, main 3e8d6ac1) | card field "license: mit" | notes/T01/licences.md | no data files on main today; training on another engine's data = owner decision |
| Viridithas at tag v20.0.0 (0631113e22) | MIT at that tag (AGPL-3.0-only from v21) | notes/T01/licences.md | read as ideas only in this job; reading v20 source would be allowed by its licence - owner decision |
| bullet @da426a49 (trainer) | MIT | LICENCES table above | T01 configs (copy with notice) |
| nnue-pytorch @c625702757 (trainer) | GPL-3.0 | LICENCES table above | run-only tool of the crew; PR text read, never source |
| fastchess (match runner) | MIT (30-Oct round; not re-checked) | crew tool | gates (T12) |
| UHO_Lichess_4852_v1.epd and other Stockfish books | CC0 (30-Oct round, books repo; not re-checked) | fishtest run data quoted by T05 / T07 verifiers | gate book |
| uops.info measurement tables; Agner Fog instruction_tables.pdf (2025-09-20) | facts / documentation (no code copied) | notes/T05/sources.md 1-4 | Zen 5 latency / throughput figures |
| LLVM BOLT README @b537630299 | Apache-2.0 WITH LLVM-exception | notes/T05/sources.md 5 | the one-line "BOLT on Windows: no" |
| Syzygy tablebase files | free to use; the generator syzygy1/tb is GPL-2.0 (30-Oct round) | T02-05 | presence on grok-pc PENDING |
| arXiv 2412.17948 (Xiangqi NNUE data study) | CC BY 4.0 | notes/T02/sources.md | dead end (no Elo) |
