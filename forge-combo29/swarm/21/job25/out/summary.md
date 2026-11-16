| case | PC20: refused | PC20: nodes | PC20: perft2 | python perft2 | base: refused | base: nodes |
|---|---|---|---|---|---|---|
| hm_0 | False | 307 | 625 | 625 | False | 320 |
| hm_99 | False | 293 | 625 | 625 | False | 297 |
| hm_100 | False | 293 | 625 | 625 | False | 0 |
| hm_150 | False | 155 | 625 | 625 | False | 0 |
| hm_9999 | False | 155 | 625 | 625 | False | 0 |
| hm_2p31 | False | 155 | 625 | 625 | False | 0 |
| hm_neg1 | True | None | None | None | True | None |
| fm_0 | True | None | None | 625 | True | None |
| fm_1 | False | 307 | 625 | 625 | False | 320 |
| fm_1e9 | False | 307 | 625 | 625 | False | 320 |
| fm_neg1 | True | None | None | None | True | None |
| ep_e3 | True | None | None | 625 | True | None |
| ep_z3 | True | None | None | None | True | None |
| two_kings | True | None | None | 575 | True | None |
| no_kings | True | None | None | 529 | True | None |
| pawn_rank1 | True | None | None | 500 | True | None |
| mate_hm100 | False | 84 | 153 | 153 | False | 0 |

| question | outcome |
|---|---|
| P1 PC still refuses fullmove 0 | yes |
| P2 PC refuses negative clocks and accepts 2^31 halfmove | yes |
| P3 PC searches every halfmove >= 100 (nodes > 0) | yes |
| P4 PC still refuses ep/two-kings/no-kings/pawn-rank1 | yes |
| P5 PC perft2 == python on every accepted case | yes |
