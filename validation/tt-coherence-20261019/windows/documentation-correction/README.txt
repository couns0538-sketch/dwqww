Forge 6.4.3 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.3-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This executable targets Zen5; it is not a universal x86 build.

This candidate fixes a demonstrated shared transposition-table data race.
Readers now consume a coherent atomic entry snapshot, and generation values
are captured for each search worker. Previous promotion, stalemate, clock,
TT-tag and AVX2 changes remain. Evaluation weights are unchanged.

Windows core, coherent-TT, UCI and ponder regression checks passed under
Wine10 using the frozen 6.4.3 source tools. Emitted 256-bit clamp/multiply/add
instructions were checked, with no fused arithmetic found. Optional test
executables contain the core and coherent-TT checks. Source/build identity
and exact test-fixture hashes are recorded in provenance.json.

This is a TT correctness candidate. The shared-VM speed calibration was
too noisy to establish a performance result. No accepted Elo gain exists.
Native Windows and physical Ryzen validation remain pending. Full-strength
Stockfish superiority is unproven. Wine correctness is not native Elo.

The separate 6.4.2 portable match-validation bundle remains a frozen 6.4.2
experiment; it does not test this 6.4.3 executable automatically. This package
does not alter that bundle, older releases, or their evidence.

Source: production df5d839a6a03f705310bb958601375fa9411e810;
TT regression fixture 77ee53bdae40fbffee42be406b73f245f4434993.
See source-hashes.json, provenance.json and SHA256SUMS.
