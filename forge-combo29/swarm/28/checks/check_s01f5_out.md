== python-chess says of my own positions ==
MATE_ROOK_hm0: mate_in_one_exists=True
MATE_ROOK_hm99: mate_in_one_exists=True
MATE_ROOK_hm100: mate_in_one_exists=True
MATE_ROOK_hm101: mate_in_one_exists=True
MATE_ROOK_hm150: mate_in_one_exists=True
QUIET_hm99: mate_in_one_exists=False
QUIET_hm100: mate_in_one_exists=False

| case | halfmove | refused | engine nodes | score | bestmove | bestmove IS mate-in-one |
|---|---|---|---|---|---|---|
| MATE_ROOK_hm0 | 0 | False | 126 | mate 1 | a1a8 | True |
| MATE_ROOK_hm99 | 99 | False | 126 | mate 1 | a1a8 | True |
| MATE_ROOK_hm100 | 100 | False | 0 | cp 0 | f2f3 | False |
| MATE_ROOK_hm101 | 101 | False | 0 | cp 0 | f2f3 | False |
| MATE_ROOK_hm150 | 150 | False | 0 | cp 0 | f2f3 | False |
| QUIET_hm99 | 99 | False | 781 | cp 0 | g2g3 | False |
| QUIET_hm100 | 100 | False | 0 | cp 0 | f2f3 | False |
