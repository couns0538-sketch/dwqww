# T05B licence rows (tools/licence_at.py --row, PC clock times as run)

| repo | HEAD read | date | file | licence | first line | api |
|---|---|---|---|---|---|---|
| AndyGrant/Ethereal | 7f6b2d3945 | 2018-07-22 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| jdart1/arasan-chess | 6e432a21ef | 2026-11-04 | LICENSE | MIT | ---------------------------------------------------------------------- | api: NOASSERTION |
| jdart1/arasan-chess | 2dbc0649dc | 2021-05-31 | absent | no licence (all rights reserved) | - | api: NOASSERTION |

Correction for the arasan-chess 2dbc0649dc row (v22.3.0; read by hand 00:20): the root has no LICENSE file, but
doc/license.txt at that commit is the MIT permission text ("Copyright 1994-2021 by Jon Dart ... Permission is hereby
granted, free of charge ...") and states that it covers the src, book, doc, prj and tests directories. Use: MIT =
source may be read; only src/scoring.h lines 60-160 (structure declarations) and doc/CHANGES were read; nothing copied.
| TerjeKir/weiss | ff59b2741d | 2020-10-26 | COPYING.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | 86f1df7134 | 2026-06-10 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |

Use: Ethereal, Weiss, Stockfish = GPL-3.0, ideas only: only commit messages and PR text were read (gh api commits /
pulls, gh search commits, tools/mine_commits.py), never a source file.
