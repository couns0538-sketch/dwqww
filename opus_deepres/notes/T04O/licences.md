# T04O licences (tools/licence_at.py --row, HEAD of the default branch, read 2026-11-05 between 04:17 and 04:24 PC)
Brief: mine only engines whose LICENSE at HEAD is MIT / BSD / Apache; anything else is skipped (no source, no mining).
Result: jw1912/akimbo and 1337crisis/svart qualify (MIT: source may be read for cited commits, copy only with notice).
Skipped: Sirius, motor (no LICENSE file = all rights reserved), Starzix (WTFPL, not in the MIT/BSD/Apache list - owner
call), pawnocchio and Tarnished (GPL-3.0).
Svart note: the old address crippa1337/svart now redirects to feliskio/svart, an unrelated one-file placeholder (its
description says it is a repo-takeover proof; 0 stars, README only, not read further). The real engine is
1337crisis/svart (found with two gh search calls, the first, "svart chess", empty). The feliskio row below is that placeholder, not the engine.

| repo | sha | date | file | spdx | first line | api |
|---|---|---|---|---|---|---|
| mcthouacbb/Sirius | 0aab371e4d | 2026-10-03 | absent | no licence (all rights reserved) | - | api: none |
| jw1912/akimbo | f7dd7677d6 | 2025-02-07 | LICENSE | MIT | MIT License | api: MIT |
| jw1912/akimbo | 7120b4be24 | 2024-01-12 | LICENSE | MIT | MIT License | api: MIT | [last round, coordinator, unverified] (the commit row 8 cites)
| martinnovaak/motor | 033a63cf54 | 2026-10-31 | absent | no licence (all rights reserved) | - | api: none |
| feliskio/svart (placeholder behind the crippa1337/svart redirect, not the engine) | 5f7d00413b | 2025-09-26 | absent | no licence (all rights reserved) | - | api: none |
| 1337crisis/svart | f3bf4c1ce0 | 2025-11-18 | LICENSE | MIT | MIT License | api: MIT |
| zzzzz151/Starzix | 2a1577fb15 | 2025-05-10 | LICENSE | unknown (read the text) | WTFPL text (first line not copied) | api: WTFPL |
| JonathanHallstrom/pawnocchio | bd860905d3 | 2026-07-09 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
| Bobingstern/Tarnished | 79f10476c7 | 2026-11-03 | LICENSE | GPL-3.0 | GNU GENERAL PUBLIC LICENSE | api: GPL-3.0 |
