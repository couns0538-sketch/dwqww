Forge 6.4.2 candidate - Windows x64 Zen 5 / Ryzen 7 9850X3D

Load forge-6.4.2-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This build targets Zen 5; it is not a universal x86 executable.

Changes since 6.4.1: all rook, bishop and knight promotions now reach
ordinary search and quiescence. The preceding AVX2, clock-accounting,
stalemate and TT-tag corrections are retained. Evaluation weights unchanged.

Validated: 5/5 Linux CTest suites (including19 validator safety checks),
Windows core/UCI/ponder checks under Wine10, both-color promotion regressions,
and emitted AVX2 arithmetic without fused operations. Optional forge_tests.exe
contains the core regression checks. No native Windows or Ryzen run yet.

Strength: no accepted Elo gain for6.4.2. The earlier6.4.1 candidate's178-game
fixed-node SPRT accepted H0; it is not this candidate's strength result.
Full-strength Stockfish superiority remains unproven. The separate portable
native validation bundle provides a preregistered timed test on your Ryzen.

See provenance.json and SHA256SUMS for exact source/build/artifact identity.
