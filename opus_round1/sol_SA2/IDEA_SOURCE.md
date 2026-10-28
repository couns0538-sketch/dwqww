# IDEA_SOURCE — S-A2 int16 inference weights + weight clipping in training

- **Spec.** `SOL_LEFTOVERS_FOR_CLAUDE.md` §2 item 39 ("S-A2 int16 inference weights with weight clipping in training
  (on NnueInt16 b425207a; parity 10000/10000 first; accumulators int32)") and `OPUS_TEST_PLAN.md` row 2 (G-A2, srand
  869014820: "int16 inference with weight clipping during training … builds on NnueInt16 b425207a; trainer clip;
  parity 10000/10000 first"). Idea list: OPUS_TOP_ENGINES_2025_2026 (int16 inference); no gate run here.
- **Engine path = a port of Sol's own NnueInt16** (read only, never pushed to): `b425207a` (tip),
  `764db5f3` "Checkpoint H256 int16 inference …" (`src/nnue_int16.inc`, the int16 hunks of `src/nnue.cpp`,
  `include/forge/nnue.hpp`, `src/uci.cpp`) and `07410241` "Complete native integer validation …". Sol's design notes:
  `764db5f3:validation/sol-next-20261024/int16-wip/FEASIBILITY.md` (number format, int64 group widening, 2 cp bound)
  and the IDEA_SOURCE entry of 764db5f3 (Sol's source: the user's supplied Forge H128 `fc_int16_ep10_src.tar.gz`,
  sha256 `aa9558c2…`; "no source, constants, tables or comments from another engine").
- **Ported:** the int16 kernels and the UCI option only. **Not ported:** Sol's `FORGE_AVX512` / `FORGE_NNUE_ALIGN64`
  float paths, the `search.cpp` hunks (deferred-capture buffer, `FORGE_COMPLETE_ITERATION_ONLY`), `.agents`, tools,
  validation trees, LICENSE/README of Sol's zip (CR: must not merge). The lock net and everything else stay the lock's.
- **CR input:** `LA/7_history/cr_notes/CR_HOLD_sol_nnueint16_b425207a.txt` (2026-10-25). Addressed here: the LOW
  finding "int16_detail::selected is a plain global bool … make it std::atomic<bool>" (done, relaxed loads; the UCI
  regression runs a setoption during `go infinite` under TSan in CI); the INFO "the name says int16 but accumulators
  are int32 … the docs should say so" (header, option comment, README). Not changed by this job (policy, crew
  decision): "H256 nets are float-only by crew/Couns rule"; ON needs a crew vote and its own gate.
- **Generic techniques, no third-party code:** `packus_epi32` + `min_epu16` clamp, `mulhrs` rounded square, `madd_epi16`
  dot, int64 widening per 16-unit group (Intel intrinsic semantics; CR found no copied code/comments/tables).
  The parity references (`sa2_parity.py`, `tests/nnue_int16_tests.cpp`) are written from the number format, not from
  the kernels. Feature mapping as in `forge::nnue::feature_index` and the trainer's `features()` (S21 helpers reused).
- **Trainer:** `train_resid_v3c.py` of `opus-sol-S50` (head `ff98828a`, md5 `e7fefe77`, = S39 v3c + `--init-weights`).
  The v3b/v3c `NNUE.project_weights()` (clamp to ±32767/4096 after every step, since v2) already keeps exports inside
  int16; `--weight-clip` adds a configurable, verified clip whose default (K 21704) is derived from the engine's
  NnueInt16 eligibility check (lane bound `|b1| + Σ768 |w1| + 4·max|w1| < 2^24`: 773·K < 2^24). Weight clipping as a
  post-step projection is the standard quantisation-aware technique (clamp parameters to the representable range).
- **Reused tools:** `opus-sol-S21` (int16 range study; its finding that an int16 *accumulator* overflows on every net
  is why accumulators stay int32), `opus-sol-S29/nps_ab.py` (ABBA NPS; `nps_ab_opts.py` adds per-arm UCI options),
  `opus-sol-S50` smoke runner (renamed copies, Idle, RAM floor, supervisor watch), `LA/2_build/uci_check.py`,
  `LA/5_nnue/tools/nnue_check.cpp` (shape of `nnue_int16_dump.cpp`).
