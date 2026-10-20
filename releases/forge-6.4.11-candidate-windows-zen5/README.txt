Forge 6.4.11 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.11-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This executable targets Zen5; it is not a universal x86 build.

This candidate adds a one-pass NNUE accumulator update for count3 captures
that remove the mover, remove the captured piece, and add the mover or promoted
piece. Each lane subtracts the first removed weight, then the second removed
weight, then adds the new weight. The inherited count2 path and original
other-pattern fallback remain; exact in-place updates remain supported.

The actual frozen6.4.10 and6.4.11 Windows cores produced byte-identical
4,097,860-byte update streams and21,192,328-byte original snapshot streams.
The update driver covers1,644 distinct/in-place API checks,31 dirty masks,
and both-color special moves; the original driver includes100,000 synthetic
output evaluations. All four Windows streams also exactly match the frozen
Linux streams, with matching recorded round-to-nearest/FTZ/DAZ controls.
Headers, weights and network are unchanged. Separate emitted-code inspection
verified the count3/remove/remove/add guard, two sequential subtractions before addition and one
store per lane on vector/scalar routes, with no fused arithmetic. The
compiler uses Zen5 ZMM vectors in this update path. These correctness and
static-inspection results provide no performance or Elo measurement.

The inherited OwnBook repair makes OwnBook=false suppress an external Polyglot book after
it has been loaded. Book File now controls loading independently of OwnBook.
The actual Windows executable passed all five true/false/true/false+reload/true
transitions using a one-entry external book whose path includes a space.
Only an evidence adapter translated that temporary path to Wine Z: syntax;
the frozen production regression test is unchanged.

The inherited root effort repair addresses attribution when root move
ordering changes. Node effort and best-move lookup now use stable full Move
identity across iterative deepening and aspiration retries. Time-manager
constants and evaluation weights are unchanged. Actual timed-stop behavior,
clock reliability and Elo impact have not been established.

The inherited MovePicker change delays direct-check mask initialization until
quiet or evasion generation consumes those masks, retaining their formulas
and move scoring.

The inherited qsearch change computes gives_check inside the existing pruning
block where the read-only result is consumed.

The inherited legal-move query tries one quiet nonpromotion pawn push with
the normal king-safety check, then uses the complete original generator
fallback whenever that witness fails, including promotions.

Under Wine10, all 18,947 comparisons against the old full generator and an
independent make/unmake legality oracle passed. Fixtures, the frozen 10,000-
position corpus and deterministic walks were checked. Core tests including
six reference perft cases, all eight TT groups, rule50 regressions, and frozen
UCI/ponder tests plus the actual OwnBook regression passed. The stdin bench11 signature is 351,063 nodes with
Hash16MiB/Threads1, matching the Windows6.4.10 parent. Time/NPS is not compared.
YMM clamp/multiply/add and absence of fused arithmetic were checked. All
source, fixture, corpus, binary and tool hashes remained unchanged.

Inherited TT safety uses striped mutex-protected entry copies and opaque
probe-time destinations. Score context permits both capped clocks below90
or an exact capped-clock match (cap100), while preserving the main-search
current-clock<90 cutoff guard, raw static eval and hash-move reuse. Entry and
cluster layouts remain16/64 bytes. The below90 grouping is heuristic and does
not solve every repetition or rule50/history issue.

This is a candidate with correctness evidence. No accepted Elo gain exists.
No Windows throughput or timed match was run; any separate helper-kernel
measurement does not establish engine Elo. Native Windows, physical Ryzen
and Stockfish superiority remain unproven. The separate portable6.4.8 validator remains unchanged and does not test this
executable automatically. No new offline validation bundle was built.

Optional tests are included. From this directory, the witness oracle runs as:
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

Source and tests:c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e.
See source-hashes.json, test-hashes.json, provenance.json and SHA256SUMS.
