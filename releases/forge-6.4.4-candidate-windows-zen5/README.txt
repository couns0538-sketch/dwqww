Forge 6.4.4 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.4-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This executable targets Zen5; it is not a universal x86 build.

6.4.4 addresses tested forward and reverse reuse of TT search scores across
different halfmove-clock contexts near the fifty-move boundary. A score is
eligible when BOTH stored/current clocks are below90, OR their capped clocks
match exactly. Clocks are capped at100. The old main-search current-clock<90
direct-cutoff guard remains. Raw static evaluation and hash moves remain
reusable when a search score is ineligible. The below90 grouping is heuristic;
equal clocks do not establish repetition/history equivalence. This is not a
universal solution to rule50, repetition or search-history context.

The preceding TT coherence fix uses striped mutexes to protect complete
by-value entry copies and opaque probe-time destination handles. Generation
changes occur under lifecycle quiescence after workers are joined. Entry and
cluster layouts remain16 and64 bytes. Previous promotion, stalemate, clock,
TT-tag and AVX2 changes remain; evaluation weights are unchanged.

Under Wine10, core tests, all8 TT regression groups, targeted rule50 tests,
and frozen-source UCI/ponder checks passed. Both reverse-context regressions
passed and targeted_regression_failures=0. Emitted256-bit clamp/multiply/add
and absence of fused arithmetic were checked. All source, test, binary and
tool hashes stayed unchanged. Optional test executables reproduce these
regression checks. Source and tests are pinned together to commit816423b.

This is a targeted correctness candidate. No accepted Elo gain exists.
Same-binary A/A execution cost varied about fivefold on the shared VM, so
conditional NPS gains are unmeasurable here. Native Windows and physical
Ryzen validation remain pending; Stockfish superiority is unproven.

The separate portable6.4.2 match-validation bundle stays pinned to6.4.2;
it does not test this6.4.4 binary automatically. Older artifacts and evidence
are retained. This package performs no uploads or background reporting.

Source:816423b1ddac23a00244449deef59dba736055a9.
See source-hashes.json, test-hashes.json, provenance.json and SHA256SUMS.
