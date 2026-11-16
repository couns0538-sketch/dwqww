# DESIGN NOTE — the drawn root: search it, then fall back to the draw score

**Not a patch.** A direction for the owner, one paragraph of trade-off.

## Direction

At a root that the rules call drawn (third occurrence, or halfmove counter at 100), **search it like
any other root**, and then **take the draw score unless the search finds something strictly better
than a draw for the side to move**. Concretely: run the search normally; if the returned score is a
win for the side to move (a `mate` score in its favour, or a `cp` above the draw score), report that
score and its move; otherwise report `cp 0` with any legal move. That single rule gives both
behaviours the two builds each have half of: the PC build's ability to see a mate at a drawn root
(21-C16), and the base build's refusal to report a won score for a position that is in fact drawn
(21-F19). The cost is that a drawn root is searched instead of answered in zero nodes, which costs
time exactly where the base build was fastest — but a drawn root is rare, the search is bounded by
the same depth/node/clock limits as any other root, and the worst case is one ordinary search of a
position the engine would otherwise have answered instantly.

## The trade-off, stated plainly

- **Against the PC build's current behaviour**: it searches (so it finds mates — good) but reports the
  raw search score (`cp 199` on a drawn K+P vs K board — 21-F19). A training pipeline that records
  scores learns a winning evaluation for drawn positions; an analysis display shows +2 pawns for a
  draw. This note fixes that without losing the mate case.
- **Against the base tree's behaviour**: it adjudicates without searching (`cp 0`, 0 nodes — correct
  for the draw, but it also suppresses a real mate, which is why the PC's change exists at all).
- **The rule is cheap to implement and cheap to test**: the decision is one comparison after the
  search returns, and the acceptance test is already written — a drawn root with a mate in 1 must
  report the mate (my 21-C16 board), a drawn root with no mate must report `cp 0` (my 21-F21 board
  set), and the four honesty pins must not move.
- **What it does not fix**: the score of drawn roots *inside* the tree is a separate question, and a
  root that is drawn but where the opponent can decline a claim is not a thing under the owner's match
  rules (file 6 says the match program ends the game itself), so no claim logic is needed.

## Evidence this note rests on

| finding | what it shows |
|---|---|
| 21-C16 | the PC build correctly finds a mate at a drawn root (`mate 1`, 200 nodes) |
| 21-F19 | the PC build reports a drawn root with no mate as a win (`cp 199–298`) |
| 21-F21 | on an exact metric, 0 of 50 lone-king endings produce a move whose result is worse than an available alternative — so this is a **scoring** problem, not a lost-draw problem |
| 21-C17 | position 155 is not a member of that class; its four moves all lose |

The last two matter for the priority: nothing measured shows the engine *losing* a drawn game because
of the drawn-root handling. What it shows is the engine *reporting* a drawn position as won, which
matters for self-play data and for anyone reading the score.
