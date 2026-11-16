| build | case | python | search | bestmove | score line |
|---|---|---|---|---|---|
| base | checkmated | legal=0 mate=True stale=False insuff=False | go depth 3 | 0000 | core mate 0 nodes 0 nps 0 hashfull 0 time 0 pv |
| base | checkmated | legal=0 mate=True stale=False insuff=False | go nodes 100 | 0000 | core mate 0 nodes 0 nps 0 hashfull 0 time 2 pv |
| base | stalemate | legal=0 mate=False stale=True insuff=False | go depth 3 | 0000 |  score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv |
| base | stalemate | legal=0 mate=False stale=True insuff=False | go nodes 100 | 0000 |  score cp 0 nodes 0 nps 0 hashfull 0 time 2 pv |
| base | kvk | legal=5 mate=False stale=False insuff=True | go depth 3 | e1d1 |  score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv |
| base | kvk | legal=5 mate=False stale=False insuff=True | go nodes 100 | e1d1 |  score cp 0 nodes 0 nps 0 hashfull 0 time 2 pv |
| base | knvk | legal=8 mate=False stale=False insuff=True | go depth 3 | f1d2 |  score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv |
| base | knvk | legal=8 mate=False stale=False insuff=True | go nodes 100 | f1d2 |  score cp 0 nodes 0 nps 0 hashfull 0 time 2 pv |
| base | mate_in_1_hm100 | legal=20 mate=False stale=False insuff=False | go depth 3 | f2f3 |  score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv |
| base | mate_in_1_hm100 | legal=20 mate=False stale=False insuff=False | go nodes 100 | f2f3 |  score cp 0 nodes 0 nps 0 hashfull 0 time 2 pv |
| pc | checkmated | legal=0 mate=True stale=False insuff=False | go depth 3 | 0000 | core mate 0 nodes 0 nps 0 hashfull 0 time 0 pv |
| pc | checkmated | legal=0 mate=True stale=False insuff=False | go nodes 100 | 0000 | core mate 0 nodes 0 nps 0 hashfull 0 time 1 pv |
| pc | stalemate | legal=0 mate=False stale=True insuff=False | go depth 3 | 0000 |  score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv |
| pc | stalemate | legal=0 mate=False stale=True insuff=False | go nodes 100 | 0000 |  score cp 0 nodes 0 nps 0 hashfull 0 time 1 pv |
| pc | kvk | legal=5 mate=False stale=False insuff=True | go depth 3 | e1d1 |  score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv |
| pc | kvk | legal=5 mate=False stale=False insuff=True | go nodes 100 | e1d1 |  score cp 0 nodes 0 nps 0 hashfull 0 time 2 pv |
| pc | knvk | legal=8 mate=False stale=False insuff=True | go depth 3 | f1d2 |  score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv |
| pc | knvk | legal=8 mate=False stale=False insuff=True | go nodes 100 | f1d2 |  score cp 0 nodes 0 nps 0 hashfull 0 time 2 pv |
| pc | mate_in_1_hm100 | legal=20 mate=False stale=False insuff=False | go depth 3 | e1e8 | 1 nodes 63 nps 63000 hashfull 0 time 1 pv e1e8 |
| pc | mate_in_1_hm100 | legal=20 mate=False stale=False insuff=False | go nodes 100 | e1e8 | ate 1 nodes 84 nps 0 hashfull 0 time 0 pv e1e8 |

terminal-root scores identical between base and PC builds: False
