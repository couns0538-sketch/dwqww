Forge 6.4.12 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.12-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This executable targets Zen5. Source and tests:
8865666cc0ab4961cd507bae40ff6ce44e9319df

This candidate changes TT synchronization for explicitly opted-in one-worker
UCI searches and the UCI bench command. It acquires a coarse gate, publishes an
atomic request, sequentially drains the existing 1,024 stripes, then permits the
owner thread to skip per-entry locks through table-bound TLS. Foreign entry calls
wait safely while table storage/generation remain stable. Default public library
searches and multiworker UCI searches retain the shared stripe path. Clear,
resize, new_search and destruction still require all accessors to be quiescent.
Foreign diagnostics may block for an entire search; the lease does not make
arbitrary concurrent lifecycle changes safe.

NNUE/eval sources, headers and network weights are byte-identical to frozen
6.4.11. Search policy, replacement selection and rule50 policy are unchanged.
The inherited below90 rule50 grouping remains heuristic and does not solve
every repetition or history issue. Entry/cluster sizes remain16/64 bytes.
No new large NNUE snapshot differential was needed or run for this TT change.

Eight Wine10 checks passed: core/reference perft, eight TT groups, rule50,
18,947 legal-witness comparisons, UCI, ponder, five external OwnBook transitions,
and stdin bench11 at351,063 nodes (Hash16MiB/Threads1), matching Windows6.4.11.
The existing output-layer checker verified 256-bit clamp/multiply/add without
fused arithmetic. All source, fixture, corpus, binary and tool hashes remained
unchanged during validation. See README-checks.json and provenance.json.

The compiler is LLVM-MinGW23.1.3, C++20 Release, -march=znver5 -mtune=znver5,
-fno-fast-math -ffp-contract=off and static linking. All six original Windows
executables, actual static core, frozen source tree, exact commands, compiler/link
records, runtime stdout/stderr and full disassembly are in windows-originals.zip.
Its per-file manifest was checked against every archived byte. Originals remain
in the repository validation directory; the release engine is the tested PE.

Full candidate ASan/UBSan and TSan validation is pending separately at packaging.
This is a correctness candidate; no accepted NPS or Elo gain exists. No Windows
throughput or timed match was run. Native Windows, physical Ryzen and Stockfish
superiority remain unproven. Earlier portable offline validators are separate;
no new offline validation bundle was built for this executable.

Optional included tests (from this directory):
forge_tests.exe
forge_tt_tests.exe
forge_rule50_tests.exe
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

See source-hashes.json, test-hashes.json, nnue-parent-identity.json,
provenance.json, windows-originals-SHA256.json and SHA256SUMS.
