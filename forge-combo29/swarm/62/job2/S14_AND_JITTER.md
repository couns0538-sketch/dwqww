# The defect under the PC's own settings, and under DrawJitter

All rows pasted from `probe.py` with the S14 option set the brief specifies
(LmrQuietBase 93, LmrQuietDivisor 205, LmrNoisyBase 13, LmrNoisyDivisor 333,
LmrHistoryDivisor 5643, NullMoveBase 5, LmpBase 8, HistoryPruneMultiplier 2220,
HistoryBonusQuadratic 24, HistoryBonusLinear 54, HistoryBonusMax 2212,
SingularDepth 6, IirDepth 2, NonPawnCorrection true). `option_errors: []` on every
run, so no option was silently rejected.

## Under S14, depth 24 (the depth in the brief)

    6k1/8/5PPP/8/8/8/8/R6K b - - 98 40  -> mate -1, nodes 123
    6k1/8/5PPP/8/8/8/8/R6K b - - 99 40  -> cp 0,    nodes 72

Reproduces the brief's claim exactly: wrong at halfmove 99, right at 98, at depth
24, on the PC's settings. The earlier depth ladder (3 nodes per ply) was measured
with default options; under S14 the node counts differ (72 not 96) but the score
is still `cp 0`, because the pruning node is the same one.

## DrawJitter makes the wrong answer look like a real evaluation

With DrawJitter at its default 0 the drawn leaf reports a literal 0. Turning it on
replaces that 0 with a value derived from the node count (`draw_leaf_score`,
search.cpp:1312-1319):

    DrawJitter=0 -> cp  0,  nodes 42
    DrawJitter=4 -> cp -2,  nodes 43
    DrawJitter=8 -> cp  1,  nodes 42

Note the sign flips with the node count. That is worse than `cp 0` for a
diagnostician: `cp 0` at 42 nodes at least looks anomalous, whereas `cp -2` looks
like an ordinary small evaluation and would be accepted as one. Any future check
for this defect must not rely on the score being exactly 0 -- it must compare
against the oracle, or check the node count.
