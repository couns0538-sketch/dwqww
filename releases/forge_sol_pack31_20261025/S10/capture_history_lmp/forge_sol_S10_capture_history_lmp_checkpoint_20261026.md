# S10 CaptureHistoryLmp checkpoint — 2026-10-26

Decision: **REJECTED search screen; not adopted.** The original single1000ms Lprime WAC screen solved258/300 with0 illegal moves, below the frozen283 requirement. Deep nodes changed−30.8125345% atd20 and−23.9331065% atd22, beyond the registered absolute20% guard. No retry, tuning, speed claim or Elo claim.

Both build and UCI options remain OFF by default. This hypothesis prunes late shallow non-PV captures only when capture history is negative, SEE is losing, and the move neither checks nor promotes. It reuses this Forge source's existing history-prune depth and LMP count thresholds. No other-engine code or constants.

OFF11/13/16/20/22 matched308972/745494/2460422/11901452/31111774 on both bases. ON matched304755/813494/2591604/8234313/23665760 on both bases. Both OFF22 runs completed within the original180-second observer; the batch's second-default-timeout stop condition did not occur.

Lprime passed complete Release+ASAN configured CTest14/14 each; B passed15/15 each. Exactly four pinned known diagnostic lines and zero new FAILs. Both perft5 counts4865609/193690690, all scoped NNUE ELF/object FMA0, eight production-TU compile-OFF proofs, FIRST bare11=308972 before UCI, source/runtime artifact integrity. Both reviewed ON/T2 ASAN supplements passed three legal searches, typed ON activation once before first bestmove, drained EOF, empty sanitizer stderr and observed unlimited RLIMIT_AS before/after with leak checking enabled.

Lprime main result SHA256 `04ce0ce2f1c03ab28abcc200d83fc58c6871e99e0d3987f2b1d2300215c926ee`; T2 SHA256 `2e86d7c79cfbefcc6531ef74dcffe61f18990a4066f8fcadb6819bd224755336`.

B main result SHA256 `59d0837f58d15dc59222e8eff432dd401bb141b6e582f8100143b9e200a5afc6`; T2 SHA256 `72690fdbf9817eecabada67577596c098d8c1421dea53da450bb3a0b274f1104`.

Patch SHA256 `f7e9bf21fc8e80244545012f458024f7f42738cca22f498180d762408966ad63`. Data archive `forge_sol_S10_capture_history_lmp_evidence_20261026.tar.gz`, 16616405 bytes, SHA256 `59f0436d68caa260f2eb11a1d738a799248016f85e3f4c80e7f0b63db1714ee0`; mapping SHA256 `45b6e0c25d5ed686cc6589fdb8f9e212ece64b829858be9b9466996057aa95e7`; receipt SHA256 `17401285d55c2c8a4331d09d824236a02795fecfe9c33517b25eb3d9e6f4f451`. Both decoders verified all398 members including397 original data files; all originals/binaries/caches retained unchanged.

The retained execution-condition sidecar records possible overlap with a root Git push begun before the WAC-exclusive warning, successful completion observed21:30:15UTC, exact CPU phase unobserved. No tactical effect is inferred and no screen was repeated. The candidate had already failed the deep-node guard. Windows/owner-PC and equal-time Elo remain UNVERIFIED. All S10 native jobs are closed. Root must publish/verify the final source/evidence; S11 native work requires its separate grant.
