| build | case | python truth | bestmove | score | matches convention |
|---|---|---|---|---|---|
| base | A_mated_now | checkmate | 0000 | ('mate', 0) | yes |
| base | B_can_mate_in_1 | can mate in 1 | e1e8 | ('mate', 1) | yes |
| base | C_stalemated | stalemate | 0000 | ('cp', 0) | yes |
| pc | A_mated_now | checkmate | 0000 | ('mate', 0) | yes |
| pc | B_can_mate_in_1 | can mate in 1 | e1e8 | ('mate', 1) | yes |
| pc | C_stalemated | stalemate | 0000 | ('cp', 0) | yes |

The convention check: a mated side scores mate 0, a side that can mate in 1 scores mate 1, a stalemated side scores cp 0.
base build consistent: True
pc build consistent: True

=> 21-F11 is WITHDRAWN (mate 0 is the correct UCI score for a side that is already mated)
