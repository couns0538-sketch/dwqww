# Step 2 search hooks

Only `forge-combo29/include/forge/search.hpp` and `forge-combo29/src/search.cpp` were edited in `/workspace/work/dwqww-v3`. Root owns the default macro and UCI hooks, the commit, and all builds/runtime checks. No changes to imported v3 files, CMake, root state or Git/index. No compiler or engine was run. Step 3 VERIFY is deliberately absent.

Changes follow the exact Job C description:

- Guarded v3 include, one per-worker unique_ptr and method declaration.
- Existing static_evaluate dispatches to v3 directly after the disabled/unavailable-net HCE return; existing earlier DeadMaterial handling stays intact.
- New method allocates on first use, prepares MaxPly+8 entries, obtains dirty lists from absolute stack_[k] after ensure_piece_diff, makes ply+4 valid and evaluates that accumulator.
- Both real and null move paths invalidate child ply+5 immediately after legacy accumulator invalidation, when v3 state exists.
- Root invalidates existing v3 state after stack resets; enabled/available active v3 initializes its root directly. The exact legacy refresh block remains as the alternative.

`STATIC-CHECK.txt` records that deleting the newly guarded blocks from each edited file produces the original before-snapshot bytes exactly. This is a text identity check, not a compiler/preprocessor or runtime proof. The initial draft had an extra blank line outside the new method guard; removing that newly added blank line made the exact text checks pass. Diffs and full before/after snapshots are adjacent.

Current file SHA256:

- search.hpp: 7497da206ad3ee8e411b668616880c2149f1dab1a5148167b417d2e615970b8b
- search.cpp: 4d53ef9e73f13daf5c02344ad84a4f4da2cc88fadf3a0dd9c0c5d7d890640878

Review considerations: null frames already have diff_known=true and empty dirty list; imported prepare handles net-generation changes and lazily sizes the stack; root uses v3 method directly, so a DeadMaterial early return cannot prevent initial v3 preparation. A state object is first created only inside that preparation path, so later optional invalidations have a prepared MaxPly+8 stack.
