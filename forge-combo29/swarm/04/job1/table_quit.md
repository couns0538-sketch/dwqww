# quit / EOF table — CHECK of 19-F12 (seat 19 owns the finding), startpos, go depth 12
# produced by: python3 job1/check_quit.py /tmp/quit_rel  (integrity gate must print PASSED)

| case | n | move | nodes | info lines | legal | fabricated |
|---|---|---|---|---|---|---|
| A_control | 3 | e2e4 | 56720 | 12 | True | False |
| B_quit_now | 3 | a2a3 | none | 0 | True | True |
| C_eof_now | 3 | a2a3 | none | 0 | True | True |
| D_quit_2s | 3 | e2e4 | 56720 | 12 | True | False |
| E_quit_200ms | 3 | d2d4 | 23975 | 11 | True | False |
| F_infinite_quit | 3 | e2e4 | 72062 | 13 | True | False |
| G_nodes_quit | 3 | a2a3 | none | 0 | True | True |
| H_isready_then_quit | 3 | e2e4 | 56720 | 12 | True | False |
