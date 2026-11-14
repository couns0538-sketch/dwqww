# Changes on soak/combo29-fixes

This is the dedicated six-hour validation branch for integration commit `bf5574ee654a773f0ef3d06878707056b90cdad7`. The comparison build uses lock commit `16833ecc03b425586f91f4c8834dea8807bf4c22`. The four integration fixes were already present in the starting commit.

All additions on this branch are text files under `forge-combo29/soak/`. No engine source, header, build definition, or existing test is changed. Any engine fault found is recorded with its trigger and reproduction results, without applying a fix. Only this branch is pushed.

## Added test programs

| File | Purpose and checks |
| --- | --- |
| `play_driver.cpp` | Links the unchanged engine objects for seeded self-play. Generates up to eight random legal opening plies, searches at the requested node or depth limit, and verifies returned moves against the engine's legal list and scores against the legal range. Tracks terminal conditions, complete games, searched moves, opening plies and validation failures. Records exact triggers and supports rerunning a specific seeded game. Used with ASan/UBSan and TSan. |
| `net_driver.cpp` | Compares incremental NNUE evaluation with full recomputation, and the compiled-in network with the converted lock network. Replays identical seeded positions for both network forms, includes castling, en passant, promotions and null moves, and checks that four damaged-file types are rejected without changing sampled evaluations. Emits reproducible seed/chunk/position information for mismatches. |
| `uci_nnue_loader.hpp` | Feeds `NnueFile` commands through the unchanged engine's actual UCI handler, compiled with its entry-point symbol renamed. Captures the handler's output and returns control to the network checker. |
| `uci_process.hpp` | Starts engine subprocesses, sets UCI options, clears state before each search, sends positions and search limits, and captures complete search transcripts. Parses the reported move, score, depth and node count for comparison. |
| `search_compare.cpp` | Compares lock and integration searches at depth 9; selects legal king-and-rook-versus-king roots with one-thread mate scores; repeats two-thread depth-14 searches ten times per root and build. Records differences and mate failures with transcripts and ten-trial frequencies. |

## Added evidence and reports

- `PROGRESS.md`: UTC start time and chronological batch records, including seeds, commands, counts, accumulated totals and fault counts.
- `SOAK_REPORT.md`: phase results, conditions, final wall time, fault-file index and unfinished work. Updated throughout the run and finalized after the six-hour interval.
- `METHOD.md`: exact engine commits, build settings, test semantics, counting rules, opening/network provenance and match settings.
- `batches/*.txt`: commands, actual output, exit status, completed-batch counts and raw-log hashes. Incomplete attempts, if any, remain separate from totals and must be repeated with their original seed.
- `preparation/*.txt`: build and setup output, pinned checks, provenance, corpus preparation and independent evidence audits. Preparation runs are excluded from phase totals.
- `faults/NNN.txt`, when required: exact input and settings, diagnostic or search output, and frequency across ten trials. The report lists every recorded fault.
- `CHANGES.md`: this description of the branch's additions.
- `HANDOFF.md`: the actionable two-thread mate-score finding, a concrete reproducer, and links to both builds' ten-trial transcripts for subsequent engine work.

Official fastchess, its build, the opening book, generated networks, engine executables, temporary orchestration tools and large normal match artifacts stay in the cloud VM. Match artifact hashes are included in the committed batch evidence. No scripts, executables, archives, Python files or CI workflows are added to the branch.

Read [SOAK_REPORT.md](SOAK_REPORT.md) for the measured results and [PROGRESS.md](PROGRESS.md) for the run chronology. Match results are reported as counts under the stated conditions; they are not an Elo or speed claim.
