# T07 licence rows (tools/licence_at.py --row, one per repo, at the commit read)

| official-stockfish/Stockfish | 5ca4bfe72b | 2026-09-09 | Copying.txt | AGPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
  (note: the tool's text guess says AGPL because the GPL-3.0 text names the Affero licence in its section 13; first line
  and the GitHub API both say GPL-3.0. Use: ideas only - commit titles, PR text, fishtest pages; no source read.)
| PGG106/Alexandria | 49391d7b70 | 2026-07-22 | LICENSE.md | AGPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
  (same false AGPL text guess as above; GPL-3.0. Use: ideas only - commit messages, PR text, OpenBench pages.)
(corrected by verify 23:10: a re-run of tools/licence_at.py --row now gives GPL-3.0 in the text column for both rows
  above - Stockfish 5ca4bfe72b and Alexandria 49391d7b70 - not AGPL-3.0; use unchanged, ideas only.)
| PGG106/Alexandria | 8e3fc66e52 | 2024-06-24 | LICENSE.md | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
  (PR 438 commit, read for T07-02's hold-still term: commit message only. Use: ideas only.)
