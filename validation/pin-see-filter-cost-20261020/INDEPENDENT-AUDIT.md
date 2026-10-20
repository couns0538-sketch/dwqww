# Independent source and evidence audit

A second agent reviewed the mask implementation, build/orchestration scripts,
diagnostic source, and saved API/bench outputs without changing files, building,
or executing an engine.

Result: no material implementation or counter errors found.

- The mask matches the proof, preserves king candidates, suppresses target
  ghosts, and handles existing checks.
- Reference counters cover only primary SEE queries. Shadow verification leaves
  search state untouched and excludes its queries from primary counts:
  3,614 complete states, 1,275 shadow queries, zero mismatches.
- The bench harness matches UCI's eight FENs, Searcher(16), one thread,
  per-position clearing, depth 11, and exclusive TT access. It prints actual
  scores, best moves, legal PVs, and nodes.
- Raw bench outputs are byte-identical: eight depth-11 results, 385,792 nodes.
- Counts reconcile: reference 742,109 occupied slider queries; mask 474,626
  empty-board queries plus 49,015 between classifications. Each non-slider
  test falls from 371,702 to 237,313.
- All recorded execution phases succeeded. Source-operation counts do not
  establish speed or Elo.
