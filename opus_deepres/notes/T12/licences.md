# T12 licence rows (tools/licence_at.py --row, one per repo read)

| repo | sha | date | root licence file | spdx guess | note | api |
|---|---|---|---|---|---|---|
| official-stockfish/fishtest | 5a8a229a52 | 2026-10-13 | absent | no licence (all rights reserved) | - | api: none |
| AndyGrant/OpenBench | 230ed46e47 | 2026-11-04 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| llvm/llvm-project | f7d11195ab | 2026-11-04 | LICENSE.TXT | Apache-2.0 WITH LLVM-exception (corrected by verify: the 23:31 re-run of the tool prints this guess, not MIT) | ====================================================================== | api: NOASSERTION |
| official-stockfish/Stockfish | 5c617e579c | 2025-02-27 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/books | a804a97e70 | 2026-10-16 | LICENSE | CC0-1.0 | Creative Commons Legal Code | api: CC0-1.0 |
| official-stockfish/Stockfish | a06e7004c1 | 2024-09-17 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| official-stockfish/Stockfish | 73018a0337 | 2021-09-23 | Copying.txt | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |

Notes
- fishtest: the tool finds no root LICENSE file at 5a8a229a52; WORKER_RULES list fishtest as GPL-3.0. Either way the
  tier is "ideas only": only the wiki pages (Fishtest-mathematics, Creating-my-first-test) were read, no source file.
- Verify (23:31): all five original rows re-run with tools/licence_at.py --row and match except the llvm spdx guess
  (above). The last two rows were added by the verifier: T12-03 cites these two Stockfish commits (commit messages
  only); the original table had the licence only at 5c617e579c. The rows were moved above the Notes block so the
  table renders as one table.
