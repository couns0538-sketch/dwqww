# C6 idea sources (concepts only; all code in this job is our own)

## Primary source
- **Marcel van Kervinck (2013), upcoming-repetition (upcoming cycle) detection.** The job prompt cites it as
  "The design of a fast upcoming-repetition detector"; the Chess Programming Wiki lists it as
  *A fast software-based method for upcoming cycle detection in search trees* (2013), pdf preview
  `http://marcelk.net/2013-04-06/paper/upcoming-rep-v2.pdf` (host did not resolve from this machine on
  2026-10-26), announced in the OpenChess forum thread "Upcoming repetition detection", April 6, 2013,
  `http://www.open-chess.org/viewtopic.php?f=5&t=2300`. It was implemented in van Kervinck's engine Rookie
  (CPW: Rookie won ICT 2013 with it).
- **Chess Programming Wiki, "Repetitions"**, `https://www.chessprogramming.org/Repetitions` (read
  2026-10-26): draw-score conventions (first repetition inside the tree vs. threefold for game history),
  key-list repetition detection bounded by the reversible-move window, the van Kervinck citations above.

## Concepts taken (no code taken)
1. A position that occurred i plies ago (i odd) can be recreated by one move of the side to move iff the
   Zobrist difference between now and then is the key of a single reversible move; all such move keys
   (knight, bishop, rook, queen, king, both colours, unordered square pairs connected on an empty board:
   2 x 1834 = 3668) fit a small cuckoo hash table (two candidate slots per key), so the test costs at most
   two probes.
2. Cheap pre-filter: the XOR of the opponent's move deltas since that position must be zero (the
   opponent's men are back), which skips almost every table probe.
3. The move must be possible: the squares between from and to must be empty.
4. In search, the draw score is a lower bound for a side that can step into a repetition draw:
   raise alpha to it and fail high at once when that reaches beta (the usual way engines such as
   Stockfish use the detector; concept only, no code consulted or copied).

## Our own design decisions (not from the sources)
- The detector is defined to agree exactly with Forge's own search draw rule: a move counts iff the
  resulting position satisfies `Board::is_repetition(root_index)` (one occurrence at or after the root,
  two before it). The window is the child's (`halfmove+1`, `plies_from_null+1`, with the same saturation
  as `make_move`), the root rule is mirrored including the second-occurrence scan, and the mover's
  exact piece and colour are checked. A brute-force reference that plays every legal move is used as the
  test oracle.
- The table is a C++ `constexpr` built at compile time (static_assert on 3668 entries and a complete
  insertion), with our own slot functions (key bits 0-12 and 32-44); on Windows it is placed in a
  `.rdata$zz_forge_cuckoo` section so no existing read-only data moves.
- The search result of a node with an upcoming repetition is floored at the draw score (a fail-low
  there, e.g. because pruning skipped the drawing move, cannot prove less than the draw).
- Zero cost with the option off: `alphabeta.inc` and `qsearch.inc` are compiled twice; the CuckooRep
  instances reach their children through two small wrappers (`src/search/cuckoo.inc`), the default
  instances are the AL1 s198 functions and the root picks the tree once per iteration.

## Related history checked
- `7_history/TRIED_REJECTED_UNPROVEN.md`: no cuckoo / upcoming-repetition entry. `7_history/ideas/
  FORGE_IDEA_BOARD.md` lists "UpcomingRep" as an unbuilt idea (item 7); no gate result exists.
