# Independent-teacher data pipeline — progress

Work branch: `forge/independent-teacher-20261023`, preserving parent `27070fe`.
The first required manifest, trainer and licence checkpoint `776f0a2` is pushed;
four public downloads match. Its 14 native tests and unchanged 292,545-node
benchmark pass. Production search, core binaries and shipped weights are unchanged.

The six-hour job runs October 23, 11:04 AM–5:04 PM PDT. New work stops around
4:34 PM. No old data, strength matches or Elo claims are part of this job.

The protocol is frozen before production: fresh Forge 6.4.24 self-play and games
against exact `5101c252`, 64-node generation, varied 8–24-ply openings, and a
256-ply limit. Whole games split 90/5/5 into training, validation and final audit.
External Stockfish 19 labels at fixed depth 6, one thread and 16 MB hash per
worker, with state reset between games. Accepted teacher moves are quiet and
scores within ±1,000 cp; mate scores are excluded. The fixed result blend is 40%.
One eight-epoch warm-start residual run is planned. Selection uses validation;
publication requires a positive 95% whole-game audit interval against shipped.

The generator passes 13 integrity tests. Its native driver calls both unchanged
Forge cores: all 256 comparison games and 9,088 sample positions match the
recorded UCI game moves, results and FENs. A one-worker screen generated 33,449
rows in 41.238 seconds. This measures data generation, not engine speed or Elo.
The external labeler passes 13 tests and independent review. A representative
depth-six screen accepted 215 of 256 positions in 1.361019 seconds. Earlier slow
approaches and original failures remain in `source-checks-02.zip`.

Fixed-target training, protocol checks, the five-million-position minimum and
audit-only guards are implemented. The latest shared Python suite passes 116
checks. Both checksum indices verify all 39 listed entries. The trainer has an
MIT SPDX notice, unchanged executable syntax, and its original index preserved.

Production collection has not started. Final preparation integrity and cleanup
repairs are under review. No five-million-row dataset, training loss, audit gain
or new network is claimed. Settings, exact SHA256 values and current state are in
`manifest.json` and `protocol.json`.
