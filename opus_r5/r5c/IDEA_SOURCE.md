# R5C idea sources

Every implementation in this folder and in the engine diff is my own code; sources are where the ideas come from.

| idea | source |
|---|---|
| N3 bundle (SyzygyPath 3-4-5 + IntendedThreefold + HardDeadline=10 gated together) and its blockers | job spec R5C (Engine QA for Couns, 2026-10-29); the options come from Opus C1 (Syzygy prober), C3 (HardDeadline watchdog) and the IntendedThreefold option on forge-bundle-int b7c1772 |
| v4 net = v3 layout + int16 second layer (L2 = 16) + per-output-bucket final layer | J7 prototype (branch fable-fb2-j7, `fable_fb2/j7/README.md`, `tools/nnue/fable_nnue_train.py --l2 16`, crew bot Fable); v3 file format FORGENN3 (branch fable-nnue-arch, `src/nnue_v3.cpp`) as the format reference |
| `tbhits N` in the info lines (hits of this search, all workers, only while tables are loaded) | UCI protocol `info tbhits`; the counter `syzygy::probe_hits` exists since C1; the per-search base is my own |
| v4 unit test with its own FNN4 writer and an int64 reference forward written from FNN4_FORMAT.md | own; the planted-reference idea is the Forge verify practice (`forge-engine-verify` skill) |
