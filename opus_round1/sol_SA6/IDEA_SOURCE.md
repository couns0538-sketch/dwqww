# S-A6 idea sources

- **Spec:** `OPUS_TEST_PLAN.md` row 6 (G-A6 "SPSA re-tune of search after the new net locks", QA slots only, after
  A1/A4 lock, srand 881917307); `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 42 ("plan only").
- **SPSA:** J. C. Spall, simultaneous perturbation stochastic approximation (gain sequences a_k = a/(A+k+1)^α and
  c_k = c/(k+1)^γ, with α = 0.602 and γ = 0.101 as the usual practical values). The way chess engines use SPSA (game
  pairs at θ±c, a per-parameter c_end and a final learning rate R_end = a_end/c_end²) follows public fishtest and
  OpenBench practice; concepts only, no code copied.
- **Forge inputs:**
  - S15 (`opus-sol-S15`): harness v2 and the 51-parameter catalog; the exposed build is required.
  - S41 (`opus-sol-S41`): the eval-scale check, used for step 0.
  - S08-4: dead-feature list (CaptureFutilityBase = 0).
  - Gate RESULT.md / RUN_INFO.json copies (S44 inputs): measured throughput.
