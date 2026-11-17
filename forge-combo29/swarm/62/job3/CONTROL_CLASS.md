# The control class, and why the obvious choice of control proves nothing

Pasted output of `control_class.py` (base build, depth 12):

    CONTROL: insufficient material -> ROOT GUARD, 0 nodes
    8/8/4k3/8/8/3K4/8/8 b - - 99 40          engine=cp 0   nodes=0
    8/8/4k3/8/8/3K4/8/6N1 b - - 99 40        engine=cp 0   nodes=0
    8/8/4k3/8/8/3K4/8/6B1 b - - 99 40        engine=cp 0   nodes=0
    8/8/4k3/8/8/3K4/8/6N1 w - - 98 40        engine=cp 0   nodes=0

Every one of those four answers `cp 0` with **0 nodes**, and the instrumented
build confirms why:

    DIAG root_guard legal=8 root_drawn=1 hm=99 rep=0 insuf=1

That is `board.is_insufficient_material()` at search.cpp:2251 -- the ROOT GUARD,
a different code path from the defect. Its cp 0 is correct, but it is correct for
a reason that has nothing to do with the fifty-move rule, and it fires at every
clock, not just 99. Using a bare-king position as "the control for the fifty-move
defect" would be an empty comparison: the two positions would be exercising
different lines of code.

**Node count is the mechanical tell.** Root guard = 0 nodes (the board is never
searched). Leaf rule = non-zero nodes (the root and its children were generated
and the children returned 0).

## The control that actually belongs to this defect

Same drawn evaluation, but with a clock-resetting move available, so the clock-100
node is never reached:

    8/6K1/k7/Qq6/8/8/8/8 b - - 99 40         engine=cp 1078   nodes=45919
    8/2Q2q2/8/5K2/8/8/8/3k4 w - - 99 40      engine=cp 1129   nodes=23099
    8/6K1/8/6k1/8/5Q2/8/7q w - - 99 40       engine=cp 879    nodes=99692
    8/2Qq4/8/5k2/8/8/K7/8 b - - 99 40        engine=cp 1188   nodes=42701
    2k5/3Q4/8/2K5/8/3q4/8/8 b - - 99 40      engine=cp 1220   nodes=50858
    2k5/3q4/K7/1Q6/8/8/8/8 b - - 99 40       engine=cp 0      nodes=323

With a reset available the engine does NOT collapse to 0 nodes -- it searches tens
of thousands of nodes and returns a real evaluation. That is the contrast that
makes the defect's signature specific: `cp 0` at ~36 nodes is not "the engine
thinks it is drawn", it is "the engine stopped at the first clock-100 node".

## The trap control, stated as a finding

A position that is lost to a forced mate AND has a reset available still misses:

    1k1K4/8/5p2/8/8/8/3Q4/8 b - - 99 40    hm=0  -> mate -4, 48791 nodes
                                            hm=99 -> cp 0,    123 nodes
    Q4K1k/8/8/8/8/1p6/8/8 b - - 99 40       hm=0  -> mate -3, 80355 nodes
                                            hm=99 -> cp 0,     79 nodes
    7Q/1p6/8/8/8/5K2/8/5k2 b - - 99 40      hm=0  -> mate -3,  5191 nodes
                                            hm=99 -> cp 0,    144 nodes

These have a legal clock-resetting move, so the clock CAN be reset -- but the
losing side is not obliged to play it, and a search that returns 0 at the first
clock-100 node never gets to ask the question. So "a reset exists" is not by
itself enough to make cp 0 correct: it only makes it correct when the reset is
also the best defence. The clean control is "the position really is drawn", as in
the first table above, not "a reset happens to be legal".
