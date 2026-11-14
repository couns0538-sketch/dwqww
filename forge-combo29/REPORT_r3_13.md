# QuietExtinction

`QuietExtinction` is one UCI check option. It defaults to false. With every option left at its default, including this one, the engine is unchanged.

## Where the idea comes from

The behaviour was specified for this task. Nothing in the search change was copied from another engine: not the gap, not the reduced margin, and not the control flow.

A quiet move that has already been searched, and still sits far below alpha, is a sign that more ordinary quiets in that node are unlikely to raise alpha. The first such miss halves the futility allowance for later ordinary quiets. A second such miss stops the ordinary quiet tail. Captures, promotions, killers, and the counter-move stay in the list.

## What it does

The option is read only at a non-root node that is not in check, not a mate search, not the bare-king mate-fix path, and not within the fifty-move horizon used by the other pruners (`halfmove_clock + depth < 100`). It also stays off when neither side has a knight, bishop, rook, or queen. That is the pure king-and-pawn case, including bare kings.

A searched quiet counts as a wide miss when its score is at least 176 centipawns below alpha and the best score so far is not a mate-sized loss (`best_score > -MateInMaxPly`). While the best score is still a mate-sized loss, the miss is ignored and no quiet is removed.

- After one wide miss, a later quiet that is not a killer and not the counter-move must beat a futility allowance of half `(FutilityBase + FutilityMultiplier * reduced_depth)`. The depth cap stays `FutilityDepth`. Checks, captures, and promotions are not removed by this test.
- After a second wide miss, the move picker stops returning the rest of the ordinary quiet list. Good captures, bad captures, promotions, killers, and the counter-move are still returned. The quiet that just missed has already been searched.

Root moves are never dropped by this rule, so a finished search still returns a move from the legal root list.

## Default signature

Threads 1, Hash 16, OwnBook false, every option at default, before the change and again on the final binary:

- bench 11 = 312866
- bench 13 = 862329
- `go perft 5` from the start position = 4865609

Turning the option back off reproduces those same three numbers.

## Proof it runs

With `setoption name QuietExtinction value true`, bench 13 searched 602141 nodes. That is not the default 862329.

Source diff in `forge-combo29/src` and `forge-combo29/include`: 42 insertions and 5 deletions.

## Sanitizer

`tests_r3_13/quiet_extinction.cpp` was compiled with `-fsanitize=address,undefined` and `-fno-sanitize-recover=address,undefined`, the same portable search flags, Hash 16, and one thread. It ran 200 searches to depth 10 with the option on: 197 positions reached by playing 1 to 23 legal moves from the start position, plus `4k3/8/8/3p4/3P4/8/8/4K3 w - - 0 1`, `4k3/8/8/8/8/8/8/4QK2 b - - 0 1`, and the start position. Every returned move was legal (a terminal position must return no move). The process exited 0 and printed `searches 200 illegal 0`. No address or undefined-behaviour report was produced.

No strength claim is made. No games were played.

setoption name QuietExtinction value true
bench 13 nodes 602141
