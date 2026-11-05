# T05 licence rows (tools/licence_at.py --row, PC clock times as run)

| repo | HEAD read | date | file | licence | first line | api |
|---|---|---|---|---|---|---|
| official-stockfish/Stockfish | ff7cee4244 | 2026-10-28 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| llvm/llvm-project | b537630299 | 2026-10-20 | LICENSE.TXT | MIT | ====================================================================== | api: NOASSERTION |

Correction for the llvm-project row (read by hand at b537630299, recorded 23:07): LICENSE.TXT and bolt/LICENSE.TXT both start "The
LLVM Project is under the Apache License v2.0 with LLVM Exceptions" - the tool's MIT guess is wrong (the file also
carries legacy third-party notices). Use: Apache-2.0 WITH LLVM-exception = docs and source may be read; only the
README was read (bolt/README.md).

Use: Stockfish = GPL-3.0, ideas only: only PR titles / PR text / fishtest pages were read (PRs 6359, 7041 and the
ones listed in sources.md), never a source file. uops.info and Agner Fog's tables: measurement data / documentation,
facts only, no code. AMD slides (via search summaries): facts only.
