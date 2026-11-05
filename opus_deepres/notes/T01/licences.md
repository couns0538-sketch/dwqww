# T01 licence rows (tools/licence_at.py --row, run 2026-11-04 22:41 PC clock)

| repo | HEAD read | date | file | licence | first line | api |
|---|---|---|---|---|---|---|
| jw1912/bullet | da426a49b2 | 2026-10-26 | LICENSE | MIT | MIT License | api: MIT |
| cosmobobak/viridithas | 7489e701bb | 2026-11-04 | LICENSE | AGPL-3.0 | GNU AFFERO GENERAL PUBLIC LICENSE | api: AGPL-3.0 |
| aronpetko/integral | 29456bb34c | 2026-11-04 | absent | no licence (all rights reserved) | - | api: none |
| Witek902/Caissa | 57cae7ef71 | 2026-11-04 | LICENSE | MIT | MIT License | api: MIT |

Use allowed: bullet, Caissa = MIT (source may be read; copy only with notice). Viridithas = AGPL-3.0 (ideas only:
README, docs, changelog, PR text, test logs; never source). Integral = no LICENSE file (ideas only, same rule).
Our own trainer config is built on bullet da426a49 = the HEAD read here.

Added 23:00 PC clock (second worker):

| repo | HEAD read | date | file | licence | first line | api |
|---|---|---|---|---|---|---|
| cosmobobak/viridithas (tag v20.0.0) | 0631113e22 | 2026-06-27 | LICENSE | MIT | MIT License | api: AGPL-3.0 |
| cosmobobak/viridithas-networks | d3da3953e4 | 2026-06-08 | LICENSE | CC0-1.0 (Creative Commons Legal Code) | Creative Commons Legal Code | api: CC0-1.0 |

Owner item (not acted on): the Viridithas README at 7489e701bb says versions up to and including 20.0.0 stay under
MIT, and the LICENSE at tag v20.0.0 is MIT. v20.0.0 already contains the threat inputs (PR 425) and the pawn-pawn
inputs (PR 445). This job still read Viridithas as ideas only (README / PR / release text), per WORKER_RULES and the
owner's brief; whether the v20.0.0 source may be read is the owner's call. Viridithas nets are CC0 1.0.

Dataset (not a GitHub repo, so not from licence_at.py; read from the Hugging Face hub API):

| repo | HEAD read | date | file | licence | first line | api |
|---|---|---|---|---|---|---|
| aronpetkovski/integral-datasets (Hugging Face dataset, main 3e8d6ac1, checked 23:06) | 3e8d6ac116 | 2026-09-05 | README.md card | MIT (card field "license: mit") | --- license: mit --- | hub tag license:mit |

Note: the Integral dataset repo holds no data files on main today (README + .gitattributes only); training on another
engine's data would also be an owner decision (our nets so far use our own self-play only).
