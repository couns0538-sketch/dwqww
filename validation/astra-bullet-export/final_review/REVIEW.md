# Final Forge exporter and converter review

Review interval: 2026-10-30T09:24:49.089013+00:00 to 2026-10-30T09:49:21.552640+00:00, 1472.464 seconds. The requested 20-minute window is complete.

Concrete issues repaired and rechecked:

- Native oracle could truncate an existing file or input alias: six red failures, seven green native regressions; exclusive creation and namespace checks.
- R10 rounding immediately below a tie, mutation overflow risk, manifest type handling and parsed-stream hash binding: independent review and unit regressions.
- Converter completion totals, unbound hashed roles, omitted required binpack and source-symlink identity: all reproduced, fixed and independently replayed.
- Initial Bullet wrapper depended transitively on GPL/AGPL format crates: rejected; active MIT-core graph closure audited, including enabled features.
- Adding a second Cargo binary made the earlier initializer command ambiguous: documentation now names the binary; actual replay produced identical checkpoint SHA256.
- PC command now checks the input hash automatically, uses a fresh GUID run directory and checks each exit code. Windows/HIP execution remains unverified.

No error was found in the suspected QAT cancellation case: 446618 randomized/boundary values and all8192 real forward values matched; original smoke was preserved without retraining.

Final evidence includes 40 Python/native-I/O tests without skips, 2 Rust tests, 8192 actual Bullet CPU-mapper rows, native current/initialized/CPU-trained parity at12000 positions, deliberate weight corruption detection, sanitizer pass, exact OFF pins and perft. CTest retains four known failure diagnostics. Source-only whitespace check passes; raw objdump/compiler logs retain their original whitespace.

Job2 final commit:41d23db076f1b217d90a6f26779deb7125361edc.45 tests and independent cumulative dedup/resume check pass. Full private013/014, GPU training and Windows runtime remain unverified. No source data was deleted and no live training or gate was modified.
