# IDEA_SOURCE — S-A4 hidden layer 512 (after S-A2)

- **Spec.** `SOL_LEFTOVERS_FOR_CLAUDE.md` §2 item 41 ("S-A4 hidden 512 (after S-A2; NPS d16/d20)") and
  `OPUS_TEST_PLAN.md` row 4 (G-A4, srand 507544535: "Hidden layer 512 (after A2) … NEW Sol job (GPU, thermal <=80C,
  never stop current training); NPS at d16/d20"). Idea list: OPUS_TOP_ENGINES_2025_2026 (wider feature transformer).
  Lock archive `5_nnue/docs/NNUE_NEXT_WEEK_PLAN.md` item 8: "H384+ needs faster inference first … Order: … int16 H256
  design → only then H384" — hence after S-A2.
- **Base:** branch `opus-sol-SA2` (head 4b2a6800): NnueInt16 port + `trainer_v3c_clip.py` (`--weight-clip`).
- **Engine width:** the lock already compiles the network width from `FORGE_NNUE_HIDDEN` (all builds pass 256) and every
  NNUE kernel (float 16-lane sums, int16 16-unit groups) only needs `HiddenSize % 16 == 0`. Added: the compile flag
  `FORGE_NNUE_WEIGHTS` (and CMake `FORGE_NNUE_WEIGHTS_FILE`) to pick another include file, so an H512 net builds without
  replacing `src/nnue_weights.inc`; the include file's own static_asserts reject a width mismatch. Default build =
  lock identity.
- **Smoke net:** trained with the S-A2 trainer (`--shape 512 --weight-clip`, renamed copy) on the lock archive's
  synthetic data32 sample — a pipeline artifact, not a playing net.
- **Widened lock nets** (`widen_net_sa4.py`): function-preserving widening is the Net2Net idea (Chen, Goodfellow, Shlens,
  "Net2Net: Accelerating Learning via Knowledge Transfer", ICLR 2016: duplicate units and split their outgoing weights;
  or add units with zero outgoing weights). Own code; the exact integer split (ceil(w/2) + rest) is chosen so that the
  NnueInt16 evaluation is unchanged bit for bit. Used for H512 parity/NPS on the lock's search tree and as an optional
  GPU warm start.
- **Synthetic CTest net** (`tests/nnue_gen_net.cpp`): seeded SplitMix64 weights, own code; lets CI build and test the
  H512 code path without a trained net in the repository.
- **Reused tools:** S-A2 `nnue_int16_dump.cpp`, `sa2_parity.py`, `uci_bench.py`, `nps_ab_opts.py` (S29 nps_ab.py),
  `opus_nnue_smoke_sa2.py`; `LA/2_build/uci_check.py`. Production recipe from the read-only run command
  `F:\forge_nnue_train\runs\resid_h256_e48_f074_…cmd.txt` and `queue.txt` format (read only).
