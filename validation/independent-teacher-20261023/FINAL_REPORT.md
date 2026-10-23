# Independent-teacher pipeline — progress

Branch: `forge/independent-teacher-20261023`, preserving parent `27070fe`.
The required manifest, trainer and licence checkpoint `776f0a2` and producer
checkpoint `8dab4db` are public; four byte-identical downloads verify each.
The latter passes 14 native tests and the unchanged 292,545-node benchmark.
Runtime search, shipped weights and core binaries remain unchanged.

Six-hour window: October 23, 11:04 AM–5:04 PM PDT; new work stops 4:34 PM.
No old training data, strength matches or Elo claims are included.

The first production startup failed before accepting any labels: an empty game
chunk directory caused the labeler to read a process trace. Both processes exited
and original evidence is preserved. The corrected discovery passes a real live
producer/consumer startup test: 16 games, 441 inputs, 372 Stockfish labels, both
processes exited 0. A separate 256-game integration passes. The full source suite
runs 138 tests: 137 pass and one external test is skipped there, run separately.
Preparation passes 14 tests and independent review; a real 370-position fixture
replays native features/HCE and correctly refuses optimization below five million.

Actual 256-game feasibility screens accepted 6,781 labels in 137.654247 seconds
at Stockfish depth 6; 6,715 in 52.937017 at depth 4; and 6,795 in 42.390499 at
depth 3. These are shared-environment pipeline measurements, not engine speed.
Before qualifying production labels or any model loss, protocol revision 3 freezes
external Stockfish 19 at depth 3 with four one-thread workers to fit this budget.
Earlier settings, failed attempts and original evidence remain preserved. Pilot
rows are excluded from production. Parallel throughput is still unproven.

Fresh Forge 6.4.24 self-play and games against exact `5101c252` use varied openings,
64-node searches and a 256-ply limit. Whole games split 90/5/5; exact positions
are deduplicated with audit priority. The result blend is fixed at 40%. At least
five million unique retained rows are required before one eight-epoch warm-start
run. Original validation selects the earliest minimum-loss trained epoch; a
once-only, 10,000-draw whole-game audit must beat shipped with its 95% interval
excluding zero before any net-only branch is published.

Both current checksum indices verify all 39 listed entries; the original index
is retained. The trainer licence notice is repaired. The existing validation
skill now includes the real producer-startup check and passes scoped validation.
Compact archives contain original failures, tests, reviews and artifact hashes.

Attempt 2 is ready to launch after this checkpoint is verified and published.
No five-million-row corpus, training loss, audit improvement or new net is claimed.
Exact settings, artifact SHA256 values and next action are in `manifest.json`
and immutable `protocol.json`. Playing strength remains **unproven**.
