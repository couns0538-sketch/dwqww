# IDEA_SOURCE — sol_A2 (Astra A2, king-bucket feasibility design)

Ideas only; no code, tuned constants or tables from other engines or projects.

| idea | source |
|---|---|
| King-bucketed input layer (768 x K, own-king square selects the first-layer weight block), horizontal mirroring, refresh on a king-bucket change | Public NNUE literature and engine documentation (the general HalfKP / HalfKA family of feature sets, described in Yu Nasu's NNUE paper (2018) and the public NNUE write-ups of the computer-chess community); in this repo: the Astra A2 spec (HANDOFF_PROMPT_FULL_20261025_1743.md section 7) and Opus C4 (`opus-C4`, `opus_round1/C4/IDEA_SOURCE.md`) |
| Refresh cache (one cached accumulator per perspective and key, refreshed by applying only the piece differences) | The A2 spec ("a refresh cache idea"); C4's implementation on `opus-C4` (`RefreshCache`, `opus_round1/C4/REPORT.md`); the general idea is described publicly as accumulator caching ("Finny tables") in NNUE write-ups. Code here: own (a counting simulation only) |
| Counting king moves that cross buckets per node on bench positions | The A2 spec ("microbench on L: count king moves that cross buckets per node on bench d20 positions"); implementation own |
| Exactness argument (float accumulator holding multiples of 2^-12 is exact below 2^24 / 4096, so any update order equals a refresh bit for bit) | `LA/5_nnue/nets/history_all_CR_passed/CR_PASS_nnue_h256_e12_lock_net_float_accumulator_analysis.txt` item 3; `LA/7_history/rejected_and_shelved/int32_exact_h256e12_20261025/QA_sol_jobA_return_20261025.md` |
| Factoriser (a shared 768 x H block added to every bucket during training, folded on export) | Public NNUE trainer write-ups (feature factorisation); C4 trainer option `--king-factor` on `opus-C4` |
| Layout maps (half-board rows) | C4 `tools/nnue/forge_nnue_v2.py` `_LAYOUT_ROWS` (own code on `opus-C4`); R4 / R8 rank zones: own |
| NPS cost model calibrated on measured replicas | own; inputs are C4's measured lock-replica NPS (opus-C4 `opus_round1/C4/REPORT.md`, section "5. NPS") and this job's counts |
