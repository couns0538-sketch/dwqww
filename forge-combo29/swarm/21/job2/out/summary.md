measured startpos perft 1 = 20

| case | perft 1 nodes | equals startpos? | what it shows |
|---|---|---|---|
| N1 position, NO ucinewgame (control) | 30 | False | the position's own count |
| N2 ucinewgame BEFORE position (control) | 30 | False | reset must not matter here |
| P position then ucinewgame | 20 | True | the claim |
| P2 FEN then ucinewgame | 20 | True | the claim, FEN form |
| R ucinewgame AFTER a perft 3 search | 20 | True | the claim with a search first |
| E ucinewgame, then a NEW position | 28 | False | GUI that resets per game |
| N3 pos2 without ucinewgame (control) | 28 | False | second position's own count |

controls separate positions from startpos: True
=> CONFIRMS 30-F6
