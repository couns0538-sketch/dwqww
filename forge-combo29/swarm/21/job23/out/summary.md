| build | case | go line | bestmove | nodes | answer lines |
|---|---|---|---|---|---|
| pc | 1_illegal_name | `go searchmoves e2e5 depth 2` | 0000 | 0 | info string searchmoves restriction has no legal root moves |
| pc | 2_one_legal | `go searchmoves e2e4 depth 2` | e2e4 | 10 | - |
| pc | 3_two_legal | `go searchmoves d2d4 e2e4 depth 4` | d2d4 | 91 | - |
| pc | 4_legal_at_hm100 | `go searchmoves e1e8 depth 4` | e1e8 | 8 | - |
| pc | 5_no_names | `go searchmoves depth 2` | 0000 | 0 | info string searchmoves restriction has no legal root moves |
| pc | 6_legal_knight | `go searchmoves g1f3 depth 4` | g1f3 | 41 | - |
| base | 1_illegal_name | `go searchmoves e2e5 depth 2` | 0000 | 0 | info string searchmoves restriction has no legal root moves |
| base | 2_one_legal | `go searchmoves e2e4 depth 2` | e2e4 | 10 | - |
| base | 3_two_legal | `go searchmoves d2d4 e2e4 depth 4` | d2d4 | 91 | - |
| base | 4_legal_at_hm100 | `go searchmoves e1e8 depth 4` | e1e8 | 0 | - |
| base | 5_no_names | `go searchmoves depth 2` | 0000 | 0 | info string searchmoves restriction has no legal root moves |
| base | 6_legal_knight | `go searchmoves g1f3 depth 4` | g1f3 | 41 | - |

| question | outcome |
|---|---|
| P1 PC illegal name still says no-legal-root and answers 0000 | yes |
| P2 PC one legal name returns exactly e2e4 | yes |
| P3 PC two legal names returns one of them | yes |
| P4 PC restricted search at hm100 actually SEARCHES (nodes > 0) | yes |
| P5 base build reproduces seats 02/24 on the illegal-name case | yes |
| base build at hm100 is 0-node adjudication | yes |
