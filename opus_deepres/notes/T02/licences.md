# T02 licence rows (tools/licence_at.py --row, one per repo, at the commit read)

| repo | sha | date | file | licence | first line | api |
|---|---|---|---|---|---|---|
| official-stockfish/nnue-pytorch | c625702757 | 2026-11-01 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | ff7cee4244 | 2026-10-28 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| Witek902/Caissa | 8d2454c72f | 2026-10-17 | LICENSE | MIT | MIT License | api: MIT |

- note: the first two rows said AGPL-3.0 in the licence column (an earlier licence_at guess); (corrected by verify
  23:27: a re-run of `tools/licence_at.py OWNER/REPO SHA --row` now gives GPL-3.0 for both, matching the first line
  and the GitHub API; the Caissa row was moved back into the table). Use: Stockfish / nnue-pytorch ideas only (PR
  text, commit messages, test pages; no source read); Caissa MIT, copy with notice (nothing copied).
