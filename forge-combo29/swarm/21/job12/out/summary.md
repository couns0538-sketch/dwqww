| case | base | patched | python-chess legal moves | verdict |
|---|---|---|---|---|
| A_fullmove0 | refused=True nodes=20 | refused=False nodes=15 | 15 | FIXED |
| B_fullmove0_game | refused=True nodes=20 | refused=False nodes=30 | 30 | FIXED |
| NEG fullmove_-1 | – | refused=True nodes=20 | – | still refused (good) |
| NEG halfmove_-1 | – | refused=True nodes=20 | – | still refused (good) |
| NEG three_fields | – | refused=True nodes=20 | – | still refused (good) |
| NEG nine_in_rank | – | refused=True nodes=20 | – | still refused (good) |
| NEG two_kings | – | refused=True nodes=20 | – | still refused (good) |
| NEG ep_wrong_rank | – | refused=True nodes=20 | – | still refused (good) |
| E release: refusals over 6073 real FENs | | 0 | | reference |
| E patched: refusals over 6073 real FENs | | 0 | | same as base |
| F perft 2 on 200 G positions, patched vs python-chess | | 0 mismatches | | ok |

=> PATCH VERIFIED
