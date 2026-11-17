| board | hm | python mate in 1 | search | engine bestmove | nodes | score line | verdict |
|---|---|---|---|---|---|---|---|
| black_mate | 100 | a8a1 | go depth 5 | f7f6 | 0 | epth 5 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv | MISSED |
| black_mate | 100 | a8a1 | go nodes 100 | f7f6 | 0 | pth 64 score cp 0 nodes 0 nps 0 hashfull 0 time 1 pv | MISSED |
| black_mate | 99 | a8a1 | go depth 5 | a8a1 | 105 | mate 1 nodes 105 nps 52500 hashfull 0 time 2 pv a8a1 | MATE FOUND |
| black_mate | 99 | a8a1 | go nodes 100 | a8a1 | 84 | core mate 1 nodes 84 nps 0 hashfull 0 time 0 pv a8a1 | MATE FOUND |
| white_mate | 100 | e1e8 | go depth 5 | f2f3 | 0 | epth 5 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv | MISSED |
| white_mate | 100 | e1e8 | go nodes 100 | f2f3 | 0 | pth 64 score cp 0 nodes 0 nps 0 hashfull 0 time 1 pv | MISSED |
| white_mate | 99 | e1e8 | go depth 5 | e1e8 | 105 | mate 1 nodes 105 nps 52500 hashfull 0 time 2 pv e1e8 | MATE FOUND |
| white_mate | 99 | e1e8 | go nodes 100 | e1e8 | 84 | core mate 1 nodes 84 nps 0 hashfull 0 time 0 pv e1e8 | MATE FOUND |
| quiet_white_up | 100 | none | go depth 5 | e2e3 | 0 | epth 5 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv | 0 NODES |
| quiet_white_up | 100 | none | go nodes 100 | e2e3 | 0 | pth 64 score cp 0 nodes 0 nps 0 hashfull 0 time 1 pv | 0 NODES |
| quiet_white_up | 99 | none | go depth 5 | e2e4 | 759 | 151800 hashfull 0 time 5 pv e2e4 e8e7 h1h5 e7e6 h5a5 | searched |
| quiet_white_up | 99 | none | go nodes 100 | e2e4 | 100 | s 100 nps 0 hashfull 0 time 0 pv e2e4 e8e7 h1h5 e7e6 | searched |

| check | result |
|---|---|
| a side-blind (both mates missed at 100) | held |
| control (both mates found at 99) | held |
| c quiet +rook answers 0 nodes at 100 | held |
| control (quiet searches at 99) | held |
| b white mate missed at 100 | held |
| black mate missed at 100 | held |

=> CONFIRMS 30-F7
