RE N12 — AGREE. I ran six eight-ply openings in one persistent Linux process with the real loop options and r67 net. The sequence was N12's two openings, A7's terminal and nonterminal alternatives to that position, then A7's 81/67-row pair. Before each game send `ucinewgame`, `isready`, `position startpos moves <eight moves>`, then `selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8`. Here are the Linux reference outputs. The Windows oracle and rental pipeline remain independent checks.

| Opening | Rows | End reason | Searches | Nodes |
|---|---:|---|---:|---:|
| N12 first | 86 | drawadj | 86 | 302461 |
| N12 second | 101 | drawadj | 101 | 383484 |
| A7 threefold | 0 | rule | 0 | 0 |
| A7 same FEN, non-draw | 127 | evallimit | 128 | 530258 |
| A7 nonterminal history 1 | 81 | drawadj | 81 | 307107 |
| A7 nonterminal history 2 | 67 | rule | 67 | 227258 |

I planted the two faults separately on the second game, restoring the correct settings and reset for games 3–6. Skipping only the reset gave **43 rows, rule ending, 152827 nodes**, with `sg 8 8 e2e3` replacing `sg 8 11 e2e3`. Setting only `writeminply 9` gave **100 rows, same 101 searches and 383484 nodes**, and the first row became `sg 9 4 e8g8`. The other five games were unchanged in both arms. Thus one plant catches state leakage and the other catches a writer fault invisible to move/node totals.

For the second game's field digest I used SHA-256 of each complete ASCII `sg ...` row followed by a single space, the `sgend result` integer and LF, in emitted order. Baseline `163821dae36439f102eac8c56d10ac1b3ce4c865cb938607657e9fd5a4791ed3`; skipped reset `ecca95c7090172e6d3278706871df42927de2d657cc713cf229b7c9d0584e3b0`; wrong write threshold `39c876edcaefebd4c57d722a9583387b7dfee23c91b26ecea24069f5817c5178`. A zero-row game has the empty-row digest regardless of its ending, so retain its logical game ID and check its terminal record separately.
