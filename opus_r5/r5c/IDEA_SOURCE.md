# R5C idea sources

Every implementation in this folder and in the engine diff is my own code; sources are where the ideas come from.

| idea | source |
|---|---|
| N3 bundle (SyzygyPath 3-4-5 + IntendedThreefold + HardDeadline=10 gated together) and its blockers | job spec R5C (Engine QA for Couns, 2026-10-29); the options come from Opus C1 (Syzygy prober), C3 (HardDeadline watchdog) and the IntendedThreefold option on forge-bundle-int b7c1772 |
| v4 net = v3 layout + int16 second layer (L2 = 16) + per-output-bucket final layer | J7 prototype (branch fable-fb2-j7, `fable_fb2/j7/README.md`, `tools/nnue/fable_nnue_train.py --l2 16`, crew bot Fable); v3 file format FORGENN3 (branch fable-nnue-arch, `src/nnue_v3.cpp`) as the format reference |
| `tbhits N` in the info lines (hits of this search, all workers, only while tables are loaded) | UCI protocol `info tbhits`; the counter `syzygy::probe_hits` exists since C1; the per-search base is my own |
| v4 unit test with its own FNN4 writer and an int64 reference forward written from FNN4_FORMAT.md | own; the planted-reference idea is the Forge verify practice (`forge-engine-verify` skill) |
| M1 tests (`tests/r5c_n3_tests.cpp`, `tools/r5c_n3_uci.py`): tables present / missing / wrong path, Syzygy50MoveRule both ways, DTZ root filter legality, path change while idle, IntendedThreefold x CuckooRep, HardDeadline timing | the job's M1 list (R5C spec); the checks and harnesses are my own code; tablebase reference values from `tests/syzygy_reference.tsv` (job C1, python-chess 1.11.2 prober) |
| endgame-heavy smoke book (`n3_endgame_book.epd`, 6-9 pieces from self-play positions) | own selection (`tools/make_endgame_book.py`) from `tests/data/nnue_selfplay_sample_916.txt` |
| smoke runner `smoke_n3.py` | own R5A/R5B runner (`opus_r5/r5b/smoke_ab.py`) + FEN openings and tbhits counting |
| FNN4 exporter `tools/nnue/export_fnn4.py` (factoriser merge, fake-quant grid for w1/b1/b2, FNN4 writer) | own code; tensor names and the forward read from Fable's J7 trainer (`tools/nnue/fable_nnue_train.py`, branch fable-fb2-j7), as the job allows |
| parity method: engine kernels vs an independent numpy int64 forward read back from the file, plus the float gap | Forge verify practice (FB1 v3 parity, `forge-nnue-v3` skill); own implementation |
| exact holdout scorer (`export_fnn4.py holdout`) | the J7 trainer's loss definition (K 2.25, blend, FPOS meta) re-implemented; agrees with Fable's float metric to 5e-6 |
| `r5c_v4_eval.cpp` (engine values per FEN) | own; same role as FB1's `forge_nnue_v3_tool eval` |
