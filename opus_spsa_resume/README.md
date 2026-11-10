# opus_spsa_resume: resumable paired SPSA, two-family joint config, independent confirmation (combo29)

Work in progress; `STATUS.md` is the live state. The pack will contain three things:
1. `spsa/`: a hash-pinned, crash-safe, paired SPSA harness. It extends the R9 tuner from `opus-r9-spsa` 73eb280a.
2. `configs/` and `engine/`: a joint configuration for two untuned search families behind default-OFF switches, with `patches/*after_combo29.patch`.
3. `confirm/`: an independent confirmation pack and a proposed confirm-SPRT protocol for QA.

No games are played by this job. Real tuning is **PENDING QA EXECUTION**, and the live launchers default to dry-run.
