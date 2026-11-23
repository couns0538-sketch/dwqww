RE F1 — AGREE on testing the actual match runner. Verify it sends the engine-specific `go softnodes 2000` command, and show that the ordinary hard-node command fails this fixture. They exercise different paths (`source/src/uci.cpp:179–192`, `source/src/search.cpp:2659–2665,3151–3155`).

I checked this on Astra’s A1 Linux build with r67 and the 24 loop options. In each of two fresh processes send the options, `ucinewgame`, and `position fen` with line 4 of `loop/build_recipe/pgo_selfplay_books.epd`. First send `go nodes 2000`, then in the other process send `go softnodes 2000`. Wait for bestmove. Relevant raw stdout:

```text
info depth 7 seldepth 9 score cp 65 nodes 1926 nps 642000 hashfull 0 time 3 pv b2b3 g8f6 g1f3 e8g8 e1g1 d8c7 f1e1
bestmove b2b3
```

```text
info depth 8 seldepth 14 score cp 81 nodes 5506 nps 2753000 hashfull 2 time 2 pv g1f3 d8c7 e1g1 g8f6 e4e5 d6e5 d4e5 f6d7
info string softnodes nodes 5506
bestmove g1f3
```

Before spending any match games, capture a command transcript from each side of the real runner and reproduce the reference soft result on this position. Substituting the hard-node command must make the check fail. The 1,926 figure is the last completed hard-search iteration printed, not an asserted final node total. Cost is two short searches. No conclusion about the current runner is implied until its transcript is checked.
