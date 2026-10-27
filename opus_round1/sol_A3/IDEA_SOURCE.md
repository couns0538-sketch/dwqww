# IDEA_SOURCE — sol_A3 (Astra A3, full-NNUE design, trainer, converter, reference evaluator, smoke net)

Ideas only; no code, tuned constants or tables from other engines or projects. All code in this folder is own
code; the data-loading functions follow this repo's own trainer `train_resid_v3b.py` (Forge's trainer, read only
in `LA/5_nnue/trainers/`), the king-bucket feature definition and layouts follow this repo's Opus C4 work.

| idea | source |
|---|---|
| Stand-alone ("full") NNUE behind an OFF-default compile flag and option `UseFullNnue` | the A3 spec (HANDOFF_PROMPT_FULL_20261025_1743.md section 7); the archive prompt's NN-8 item (`FORGE_FULL_NNUE`, `UseFullNnue` 0 by default, own format and loader, float only, incremental = refresh bit-exact); O4 `PureNnue` on `opus-O4` |
| King-bucketed feature transformer (768 x KB), horizontal mirroring, layout M4 | Astra A2 on `opus-sol-A2` (`forge_astra_A2_kingbucket_design_20261027.md`); C4 on `opus-C4`; the general HalfKP/HalfKA family is described in public NNUE literature (Yu Nasu's NNUE paper, 2018, and public NNUE write-ups) |
| Output buckets selected by piece count, map (pieces - 2) / 4 for 8 buckets | C5 on `opus-C5` (`output_layout`); output-bucketed NNUE heads are a public NNUE idea |
| Hidden layer stack (2H -> L1 -> L2 -> 1) per output bucket, clipped-ReLU activations, squared clipped ReLU after the feature transformer | public NNUE architecture descriptions; SCReLU is what the lock net already uses (`src/nnue.cpp`) |
| Float accumulator exact because the first-layer weights are integers / 4096 | `LA/5_nnue/nets/history_all_CR_passed/CR_PASS_nnue_h256_e12_lock_net_float_accumulator_analysis.txt` item 3; the lock's design |
| Fixed 16-lane float32 summation order for the dense layers, no FMA | the lock's `nnue::evaluate` (`src/nnue.cpp`, "Sixteen independent partial sums ... bit-identical results without -ffast-math") |
| Per-perspective lazy accumulators, refresh on an own-king key change, refresh cache per (perspective, key) | A2 section 3.2; C4's `RefreshCache`; publicly described accumulator caching ("Finny tables") |
| Factoriser block folded on export, QAT with straight-through rounding | v3b's `q()` (QAT) and C4's `--king-factor`; feature factorisation is a public NNUE trainer idea |
| FNV-1a 64 file checksum | C4's FORGENN2 trailer; FNV-1a is a public-domain hash |
| Planted-bug (mutation) checks for the tests | the repo's engine-verify practice (forge-engine-verify skill, "Planted bug") |
