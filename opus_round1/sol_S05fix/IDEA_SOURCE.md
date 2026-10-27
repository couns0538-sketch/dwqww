# IDEA_SOURCE — S05fix

- Base: Sol's S05 v3 FMA checker and fixture runner (`forge_sol_S05_fmacheck_v3_20261025.py`,
  `forge_sol_S05_fmacheck_tests_20261025.py`, branch `forge/sol-pack31-20261025` @ 17aa0cae, S05_v2 folder).
  The NNUE output-contract code (mask/blend zero-clamp proof) is Sol's, copied unchanged into v4.
- Fix-up item: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3, S05-1 ("scan the whole .text (not only forge::nnue::),
  compute fma_count (not a literal), print the whole-binary count"); section 1 rule "FMA 0 (whole-.text objdump grep)".
- Whole-binary grep reference: the PC/CI recipes `build_pc.sh` and `opus_round1/ci/run_ci.sh`
  (`objdump -d | grep -cE 'vfn?m(add|sub)'`).
- Mnemonic families: Intel SDM / AMD APM names of FMA3 (`vfmadd*`, `vfmsub*`, `vfnmadd*`, `vfnmsub*`,
  `vfmaddsub*`, `vfmsubadd*`), FMA4 (`vfmaddps` 4-operand forms), AVX512_4FMAPS (`v4fmaddps`) and AVX512-FP16
  complex FMA (`vfmaddc*`, `vfcmaddc*`).
- Planted bug (std::fma in the LMR table setup): original, for the checker test only.
- No engine code, tuning constant or code from another engine is used.
