# Sources (R3-1 port C)

- **S-A2 NnueInt16 + trainer `--weight-clip`**: branch `opus-sol-SA2` (`d2301c51` engine/tests/trainer, report
  `opus_round1/sol_SA2/REPORT.md`); spec `SOL_LEFTOVERS_FOR_CLAUDE.md` §2 item 39, `OPUS_TEST_PLAN.md` row 2. The
  kernel is Sol's NnueInt16 (`b425207a`: `764db5f3`, `07410241`); see `opus_round1/sol_SA2/IDEA_SOURCE.md`.
- **S-A4 H512 build flags**: branch `opus-sol-SA4` (`127425f8`, report `opus_round1/sol_SA4/REPORT.md`); spec §2
  item 41, test plan row 4. SA4 contains SA2's commits.
- **Why a build switch for NnueInt16** (port decision): the R3-1 rule that the default build stays the previous stack
  binary, and `opus-offguard` (`opus_round1/offguard/REPORT.md` on that branch, run 40520714508): SA2's
  always-compiled option costs 0.40% / 0.46% CPU NPS at d16 / d20 with the option off (both CIs exclude 0), from the
  doubled accumulator entries and larger NNUE kernels. The pattern is S13's `FORGE_S13_TT_CHILD_PREFETCH` (option only
  in the switch build) and the stack's `FORGE_NNUE_O2` (merge `1bec425d`).
- **v2 nets**: NnueInt16 covers the compiled-in network only, like S41 NetScale in the stack (merge `c7e24905`);
  C4's v2 header carries the hidden size, which the loader checks against `FORGE_NNUE_HIDDEN`.
- **Function-preserving v2 replicas** for the non-interference and H512 v2 checks: `tools/nnue/forge_nnue_v2.py
  from-inc ... --replica r1` (C4).
