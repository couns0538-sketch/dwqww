# READ CHECK: twelve questions about the source (written by Opus, 23 November 2026)

Answer each in one line, with the file and line(s) that carry the answer, for example
`source/src/search.cpp:1234`. Where a question says "under the loop's options", take the values from
`loop/LOOP_OPTIONS.txt`; a setting that file does not name keeps its compiled default from the source.
Paths are those of this branch: `source/src/*.cpp`, `source/include/forge/*.hpp`.

## Search
1. Under the loop's options, from which move count on does late-move pruning stop searching the remaining
   QUIET moves at depth 4, when the position is improving and when it is not? Name the conditions under which
   this pruning is not used at all.
2. Under which conditions does a singular extension become a DOUBLE extension, and how many double extensions
   can one path from the root hold at most?
3. Under the loop's options, what reduction R does the null-move search use at depth 9 when the static
   evaluation is 450 above beta? Give the formula and the number.
4. Under the loop's options, at depth 5 and not improving, by how much must the evaluation exceed beta for
   reverse futility pruning to return, and how does the setting TtPruneV2 that the loop sends change that
   number? What does the search return there?

## Move ordering and histories
5. Under the loop's options, how large is the history bonus for a search of depth 8? Give the formula and the
   number.
6. For a node of the main search that is not in check and has a hash (TT) move: in which order does the move
   picker hand out its stages, and at which place do the losing captures come?

## The net's inference (king-bucket nets, file format FORGENN3)
7. How does the net choose its OUTPUT bucket for a position?
8. When is one side's input mirrored left to right, and is the king bucket looked up before or after that
   mirroring?

## Time handling
9. With wtime / btime AND movestogo given, how are the soft and the hard time limits computed, and what caps the
   moves-to-go value?
10. How often does a search ask whether it must stop: with a node limit, and without one?

## The engine's own self-play loop (the `selfgame` command)
11. When does a self-play game end as a win, and when as an adjudicated draw (two kinds of draw ending)?

## Option handlers
12. What does the engine print for `setoption name OwnBook value True` (capital T), and does its opening book
    ever answer a `go depth 12` search?
