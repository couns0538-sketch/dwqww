# Where the cp 0 at halfmove 99 comes from

Base 6b98f217, forge-combo29/src/search.cpp. Line numbers from that commit.

## The root guard is NOT the cause

   2250    // Terminal or adjudicated roots: report without searching.
   2251    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
   2252                                               board.is_insufficient_material());

Measured with an instrumented build (job2/diag.py, stderr):

    DIAG root_guard legal=2 root_drawn=0 hm=98  rep=0 insuf=0
    DIAG root_guard legal=2 root_drawn=0 hm=99  rep=0 insuf=0     <-- guard does NOT fire
    DIAG root_guard legal=2 root_drawn=1 hm=100 rep=0 insuf=0     <-- guard fires, 0 nodes

At halfmove 99 the counter is 99, so `halfmove_clock() >= 100` is false. The
root guard is untouched at 99. The 0-node path (36 nodes is not 0 nodes) is
somewhere else.

## The cause is the leaf rule, evaluated one ply down

   1300    bool Worker::is_draw(const Board& board, int ply) const {
   1302        if (board.halfmove_clock() >= 100) {
   1303            // Checkmate on the hundredth half-move still wins; everything else is a draw.
   1304            return !board.in_check() || board.has_legal_move();
   1305        }

Called from the main search at 1569 for every non-root node, and from qsearch at
1425. Instrumented stderr at halfmove 99:

    24 x DIAG clause=halfmove>=100 ply=1 hm=100 in_check=0 has_legal=1 returns=1

Every one of Black's moves makes a child at ply 1 with clock exactly 100. Those
children are NOT checkmate (in_check=0) and they DO have legal replies
(has_legal=1), so line 1304 returns true and the child returns 0 at once. The
search never looks at ply 2, where White plays Ra8#. Result: both root moves
score 0, so the root returns 0 for the position.

At halfmove 98 the same probe reads:

    23 x DIAG clause=halfmove>=100 ply=2 hm=100 in_check=1 has_legal=0 returns=0

Now the clock-100 node is at ply 2 and is checkmate, so 1304 returns false and
the mate is scored. That is the single-ply difference between `mate -1` and
`cp 0`.

## Why no depth fixes it

The pruning happens at ply 1, independent of the requested depth. Nodes grow by
exactly 3 per depth step (one root node plus two children), because both
children return before any further expansion:

    depth  1 -> cp 0  nodes 3
    depth  2 -> cp 0  nodes 6
    depth  6 -> cp 0  nodes 18
    depth 12 -> cp 0  nodes 36
    depth 24 -> cp 0  nodes 72
    depth 32 -> cp 0  nodes 96

Depth 24 and depth 32 are both still 0. A deeper search cannot see through a
node that returns a constant.

## The intended rule, and where the implementation departs from it

The comment on 1303 states the intent correctly ("checkmate on the hundredth
half-move still wins"). The implementation only tests whether the node at
clock >= 100 is ALREADY checkmate. It does not test whether the side to move can
DELIVER mate on this move -- which is the case FIDE 9.3 actually turns on, since
the fifty-move draw is a claim available only to a player having the move, and
mate ends the game at once.

So the correct condition at clock >= 100 is "the side to move has no mate in 1",
not "this node is not checkmate". At a node where the side to move CAN mate in 1
the position is a win for them, not a draw.
